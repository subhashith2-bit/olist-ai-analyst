
import duckdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"

con = duckdb.connect(
    str(SERVING_DB),
    read_only=True,
    config={"enable_external_access": "false"}
)

tests = [
    (
        "Raw table access",
        "SELECT * FROM raw_orders LIMIT 5"
    ),
    (
        "External CSV access",
        "SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv') LIMIT 5"
    ),
    (
        "Drop analytics table",
        "DROP TABLE fact_orders"
    ),
    (
        "Re-enable external access",
        "SET enable_external_access = true"
    )
]

try:
    for name, query in tests:
        print(f"\nTEST: {name}")
        print(f"QUERY: {query}")

        try:
            result = con.sql(query).fetchall()
            print("RESULT: NOT BLOCKED")
            print(result[:2])

        except Exception as e:
            print("RESULT: BLOCKED")
            print(type(e).__name__, "|", str(e)[:250])

finally:
    con.close()
