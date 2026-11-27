
from __future__ import annotations

import sys
import hashlib
import json
import math
import numbers
import statistics
import time

from datetime import date, datetime
from decimal import Decimal
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd
import llm
from ask_analyst import generate_valid_sql
from query_executor import execute_with_timeout

DB = ROOT / "olist_serving.duckdb"
QUESTIONS = ROOT / "eval" / "questions_v2_frozen.csv"
EXPECTED = ROOT / "eval" / "expected_results_v2.json"
SCHEMA_FILE = ROOT / "docs" / "schema_v2_frozen.md"
OUTPUT = ROOT / "eval" / "holdout_results_v2.csv"

PROMPT_VERSION = "v1"
TIMEOUT_SECONDS = 5

# --------------------------------------------------
# GENERAL HELPERS
# --------------------------------------------------

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(v):
    if v is None:
        return None

    if hasattr(v, "to_pydatetime"):
        v = v.to_pydatetime()

    if isinstance(v, (datetime, date)):
        return v.isoformat()

    if hasattr(v, "item"):
        v = v.item()

    if pd.isna(v):
        return None

    if isinstance(v, Decimal):
        return float(v)

    return v


def sort_key(v):
    v = value(v)

    if v is None:
        return (1, 0, "")

    if isinstance(v, numbers.Number):
        return (0, 0, float(v))

    return (0, 1, str(v))


# --------------------------------------------------
# TOLERANCE COMPARISON
# --------------------------------------------------

def equal(a, b, tolerance):
    a, b = value(a), value(b)

    if a is None or b is None:
        return a is None and b is None

    if tolerance == "exact":
        if (
            isinstance(a, numbers.Number)
            and isinstance(b, numbers.Number)
        ):
            return float(a) == float(b)

        return str(a) == str(b)

    tol = (
        0.0001
        if tolerance == "rate_0.0001"
        else 0.01
    )

    if tolerance in (
        "money_0.01",
        "numeric_0.01",
        "rate_0.0001",
        "exact_and_money_0.01",
    ):
        try:
            if (
                tolerance == "exact_and_money_0.01"
                and float(a).is_integer()
                and float(b).is_integer()
            ):
                return float(a) == float(b)

            return math.isclose(
                float(a),
                float(b),
                rel_tol=0,
                abs_tol=tol,
            )

        except (TypeError, ValueError):
            return str(a) == str(b)

    return str(a) == str(b)


# --------------------------------------------------
# COLUMN COMPARISON
# --------------------------------------------------

def columns_match(expected_col, generated_col, tolerance, ordered):
    expected_values = [value(v) for v in expected_col]
    generated_values = [value(v) for v in generated_col]

    if len(expected_values) != len(generated_values):
        return False

    if not ordered:
        expected_values.sort(key=sort_key)
        generated_values.sort(key=sort_key)

    return all(
        equal(a, b, tolerance)
        for a, b in zip(expected_values, generated_values)
    )


# --------------------------------------------------
# ROW COMPARISON
# --------------------------------------------------

def rows_match(expected_rows, generated_rows, mapping, tolerance, ordered):

    expected_normalized = [
        tuple(value(v) for v in row)
        for row in expected_rows
    ]

    generated_normalized = [
        tuple(value(row[j]) for j in mapping)
        for row in generated_rows
    ]

    if not ordered:
        expected_normalized.sort(
            key=lambda row: tuple(sort_key(v) for v in row)
        )

        generated_normalized.sort(
            key=lambda row: tuple(sort_key(v) for v in row)
        )

    for expected_row, generated_row in zip(
        expected_normalized,
        generated_normalized,
    ):
        for expected_value, generated_value in zip(
            expected_row,
            generated_row,
        ):
            if not equal(
                expected_value,
                generated_value,
                tolerance,
            ):
                return False

    return True


# --------------------------------------------------
# MAIN RESULT COMPARISON
# --------------------------------------------------

def compare(actual_df, expected_obj, comparison, tolerance):

    generated_rows = [
        [value(x) for x in row]
        for row in actual_df.itertuples(index=False, name=None)
    ]

    expected_rows = expected_obj.get("rows", [])

    if len(generated_rows) != len(expected_rows):
        return (
            False,
            f"row count mismatch: generated {len(generated_rows)}, "
            f"expected {len(expected_rows)}",
        )

    if not expected_rows:
        return True, "values match"

    expected_col_count = len(expected_rows[0])
    generated_col_count = len(generated_rows[0])

    if generated_col_count < expected_col_count:
        return (
            False,
            f"not enough generated columns: "
            f"generated {generated_col_count}, "
            f"expected at least {expected_col_count}",
        )

    ordered = comparison == "ordered_table"

    # Build candidate generated columns for each expected column.
    candidates = []

    for i in range(expected_col_count):

        expected_column = [
            row[i] for row in expected_rows
        ]

        possible_columns = []

        for j in range(generated_col_count):

            generated_column = [
                row[j] for row in generated_rows
            ]

            if columns_match(
                expected_column,
                generated_column,
                tolerance,
                ordered,
            ):
                possible_columns.append(j)

        if not possible_columns:
            return (
                False,
                f"no generated column matches expected column {i + 1}",
            )

        candidates.append(possible_columns)

    # Find a one-to-one column mapping that also preserves
    # complete row alignment.
    def find_mapping(index=0, mapping=None, used=None):

        if mapping is None:
            mapping = []

        if used is None:
            used = set()

        if index == expected_col_count:

            if rows_match(
                expected_rows,
                generated_rows,
                mapping,
                tolerance,
                ordered,
            ):
                return mapping

            return None

        for column_index in candidates[index]:

            if column_index in used:
                continue

            result = find_mapping(
                index + 1,
                mapping + [column_index],
                used | {column_index},
            )

            if result is not None:
                return result

        return None

    mapping = find_mapping()

    if mapping is None:
        return False, "columns match individually, but rows do not align"

    extra_columns = generated_col_count - expected_col_count

    if extra_columns > 0:
        return (
            True,
            f"values match; EXTRA_COLUMNS: {extra_columns}",
        )

    return True, "values match"


# --------------------------------------------------
# SCORER SELF-TESTS
# --------------------------------------------------

def test_comparer():

    # 1. Reordered columns should pass.
    expected = {
        "rows": [
            [100, 20],
            [200, 30],
        ]
    }

    generated = pd.DataFrame({
        "second": [20, 30],
        "first": [100, 200],
    })

    ok, _ = compare(
        generated,
        expected,
        "ordered_table",
        "numeric_0.01",
    )

    assert ok, "Test 1 failed: reordered columns"

    # 2. Incorrect value should fail.
    generated = pd.DataFrame({
        "first": [100, 200],
        "second": [20, 99],
    })

    ok, _ = compare(
        generated,
        expected,
        "ordered_table",
        "numeric_0.01",
    )

    assert not ok, "Test 2 failed: incorrect value"

    # 3. Extra generated column should pass and be logged.
    generated = pd.DataFrame({
        "first": [100, 200],
        "second": [20, 30],
        "extra": ["A", "B"],
    })

    ok, details = compare(
        generated,
        expected,
        "ordered_table",
        "numeric_0.01",
    )

    assert ok and "EXTRA_COLUMNS" in details, (
        "Test 3 failed: extra generated column"
    )

    # 4. Swapped rows should fail for ordered results.
    expected_ordered = {
        "rows": [
            ["A", 10],
            ["B", 20],
        ]
    }

    generated = pd.DataFrame({
        "category": ["B", "A"],
        "amount": [20, 10],
    })

    ok, _ = compare(
        generated,
        expected_ordered,
        "ordered_table",
        "numeric_0.01",
    )

    assert not ok, "Test 4 failed: row alignment"

    # 5. Decimal values should be handled.
    expected_decimal = {
        "rows": [
            [Decimal("10.50")],
        ]
    }

    generated = pd.DataFrame({
        "amount": [Decimal("10.50")],
    })

    ok, _ = compare(
        generated,
        expected_decimal,
        "single_value",
        "money_0.01",
    )

    assert ok, "Test 5 failed: Decimal handling"

    print("Scorer self-tests: 5/5 passed.")


# --------------------------------------------------
# MAIN EVALUATION
# --------------------------------------------------

def main():

    # Test the scorer before running the evaluation.
    test_comparer()

    for p in (DB, QUESTIONS, EXPECTED, SCHEMA_FILE):
        if not p.exists():
            raise FileNotFoundError(p)

    qs = pd.read_csv(
        QUESTIONS,
        keep_default_na=False,
    )

    refs = json.loads(
        EXPECTED.read_text(encoding="utf-8")
    )

    dev = qs[qs["split"] == "holdout"]

    schema_hash = sha256(SCHEMA_FILE)
    schema_text = SCHEMA_FILE.read_text(encoding="utf-8")

    con = duckdb.connect(
        str(DB),
        read_only=True,
        config={
            "enable_external_access": "false",
            "memory_limit": "2GB",
        },
    )

    records = []
    durations = []

    try:

        for _, q in dev.iterrows():

            qid = q["id"]
            qtype = q["type"]
            question = q["question"]

            started = time.perf_counter()

            generated_sql = ""
            response = ""
            model = llm.MODEL_NAME

            outcome = ""
            details = ""
            rows_returned = ""

            try:

                if q["comparison_type"] == "behavior_manual":

                    if qtype == "ambiguous":
                        instruction = (
                            "Ask a concise clarification question "
                            "or state a clear, defensible assumption."
                        )
                    else:
                        instruction = (
                            "Say this cannot be answered from the "
                            "available data. Do not invent columns or values."
                        )

                    response = llm.call_llm(
                        f"{schema_text}\n\n"
                        f"Question: {question}\n\n"
                        f"{instruction}\n"
                        "Respond in natural language, not SQL."
                    )

                    model = llm.LAST_USED_MODEL or llm.MODEL_NAME

                    outcome = "MANUAL_REVIEW"

                    details = (
                        "Grade manually using the question "
                        "bank's manual_grade_notes."
                    )

                else:

                    prompt = (
                        f"{schema_text}\n\n"
                        f"Business question:\n{question}\n\n"
                        "Generate one read-only DuckDB SELECT "
                        "statement using only documented tables "
                        "and columns. Return SQL only."
                    )

                    generated_sql, valid, message = generate_valid_sql(
                        prompt
                    )

                    model = llm.LAST_USED_MODEL or llm.MODEL_NAME

                    if not valid:

                        outcome = "VALIDATION_REJECTED"
                        details = str(message)

                    else:

                        sql = generated_sql.strip().rstrip(";")

                        if "LIMIT" not in sql.upper():
                            sql += "\nLIMIT 500"

                        try:

                            actual = execute_with_timeout(
                                con,
                                sql,
                                timeout_seconds=TIMEOUT_SECONDS,
                            )

                            rows_returned = len(actual)

                            ref = refs.get(qid, {})

                            if ref.get("status") != "REFERENCE_COMPUTED":

                                outcome = "EXECUTION_ERROR"
                                details = "Missing saved reference result."

                            else:

                                ok, details = compare(
                                    actual,
                                    ref,
                                    q["comparison_type"],
                                    q["tolerance"],
                                )

                                outcome = (
                                    "CORRECT"
                                    if ok
                                    else "WRONG_RESULT"
                                )

                        except Exception as e:

                            msg = str(e)

                            outcome = (
                                "TIMEOUT"
                                if (
                                    "interrupt" in msg.lower()
                                    or "timeout" in msg.lower()
                                )
                                else "EXECUTION_ERROR"
                            )

                            details = (
                                f"{type(e).__name__}: {msg}"
                            )

            except Exception as e:

                msg = str(e).lower()

                is_api_error = any(term in msg for term in [
                    "429",
                    "quota",
                    "503",
                    "504",
                    "unavailable",
                    "deadline_exceeded",
                    "resource_exhausted",
                    "service unavailable"
                    ])

                outcome = (
                        "API_ERROR"
                if (
                    is_api_error
                    or "api" in type(e).__name__.lower()
                    or "server" in type(e).__name__.lower()
                    )
                else "EXECUTION_ERROR"
                )

                details = f"{type(e).__name__}: {msg}"

            elapsed = round(
                time.perf_counter() - started,
                3,
            )

            durations.append(elapsed)

            records.append({
                "id": qid,
                "type": qtype,
                "question": question,
                "outcome": outcome,
                "seconds": elapsed,
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "schema_hash": schema_hash,
                "generated_sql": generated_sql,
                "behavior_response": response,
                "rows_returned": rows_returned,
                "details": details,
            })

            print(f"{qid}: {outcome} ({elapsed:.2f}s)")

            if details:
                print(" ", details)

    finally:
        con.close()

    result = pd.DataFrame(records)

    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    scored = result[
        result.outcome.isin([
            "CORRECT",
            "WRONG_RESULT",
        ])
    ]

    correct = int(
        (scored.outcome == "CORRECT").sum()
    )

    n = len(scored)

    print("\n=====HOLDOUT SUMMARY=====")
    print(f"Development questions: {len(dev)}")
    print(
        f"Scored SQL questions: {n}; "
        f"correct: {correct}; wrong: {n-correct}"
    )

    if n:
        print(
            f"SQL accuracy: {correct}/{n} "
            f"({100 * correct / n:.2f}%)"
        )
    else:
        print("SQL accuracy: unavailable")

    for status in [
        "MANUAL_REVIEW",
        "VALIDATION_REJECTED",
        "EXECUTION_ERROR",
        "TIMEOUT",
        "API_ERROR",
    ]:
        print(
            f"{status}: "
            f"{int((result.outcome == status).sum())}"
        )

    print(
        f"Median latency: "
        f"{statistics.median(durations):.3f}s"
    )

    print(
        f"Slowest latency: "
        f"{max(durations):.3f}s"
    )

    print(f"Prompt version: {PROMPT_VERSION}")
    print(f"Schema SHA256: {schema_hash}")
    print(f"Saved: {OUTPUT}")

    print("Holdout questions were not sent to Gemini.")


if __name__ == "__main__":
    main()
