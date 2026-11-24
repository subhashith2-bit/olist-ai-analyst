
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ask_analyst


def test_valid_sql_no_repair():

    with patch.object(
        ask_analyst.llm,
        "call_llm",
        return_value="SELECT COUNT(*) FROM fact_orders"
    ) as mock_llm:

        sql, valid, message = ask_analyst.generate_valid_sql(
            "Count orders"
        )

    assert valid is True
    assert mock_llm.call_count == 1

    print("PASS: Valid SQL required no repair.")


def test_repair_success():

    responses = [
        "SELECT * FROM raw_orders",
        "SELECT COUNT(*) FROM fact_orders"
    ]

    with patch.object(
        ask_analyst.llm,
        "call_llm",
        side_effect=responses
    ) as mock_llm:

        sql, valid, message = ask_analyst.generate_valid_sql(
            "Count orders"
        )

    assert valid is True
    assert mock_llm.call_count == 2

    print("PASS: Invalid SQL repaired successfully.")


def test_maximum_repairs():

    responses = [
        "SELECT * FROM raw_orders",
        "SELECT * FROM raw_orders",
        "SELECT * FROM raw_orders"
    ]

    with patch.object(
        ask_analyst.llm,
        "call_llm",
        side_effect=responses
    ) as mock_llm:

        sql, valid, message = ask_analyst.generate_valid_sql(
            "Count orders"
        )

    assert valid is False
    assert mock_llm.call_count == 3

    print("PASS: Query rejected after two repair attempts.")


if __name__ == "__main__":
    test_valid_sql_no_repair()
    test_repair_success()
    test_maximum_repairs()

    print("\nAll SQL repair tests passed.")
