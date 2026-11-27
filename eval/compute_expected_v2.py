"""
Compute reference results locally from the user's DuckDB serving database.
No LLM/API calls. Does not inspect or modify the holdout question outputs.
Expected SQL is authored as reference SQL, then executed locally.
"""
import csv
import json
from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "olist.duckdb"
QUESTIONS = ROOT / "eval" / "questions_v2.csv"
OUT = ROOT / "eval" / "expected_results_v2.json"

def clean_value(v):
    if pd.isna(v):
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if hasattr(v, "item"):
        return v.item()
    return v

def main():
    if not DB.exists():
        raise FileNotFoundError(
            f"{DB} not found. Copy this script/package into your project root."
        )
    df = pd.read_csv(QUESTIONS, keep_default_na=False)
    con = duckdb.connect(str(DB), read_only=True,
                         config={"enable_external_access": "false"})
    results = {}
    try:
        for _, row in df.iterrows():
            qid, sql = row["id"], row["expected_sql"].strip()
            if not sql:
                results[qid] = {"status": "MANUAL", "result": None}
                continue
            # Holdout reference SQL is computed and stored, but do not run LLM on it
            # or reveal model outputs until Day 11.
            result = con.execute(sql).fetchdf()
            results[qid] = {
                "status": "REFERENCE_COMPUTED",
                "columns": list(result.columns),
                "rows": [[clean_value(v) for v in r]
                         for r in result.itertuples(index=False, name=None)]
            }
            print(f"{qid}: reference result saved ({len(result)} rows)")
    finally:
        con.close()
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str),
                   encoding="utf-8")
    print(f"\nSaved reference results to: {OUT}")

if __name__ == "__main__":
    main()
