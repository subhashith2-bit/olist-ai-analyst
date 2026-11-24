import duckdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "olist_serving.duckdb"

con = duckdb.connect(
    str(DB_PATH),
    read_only=True,
    config={"enable_external_access": "false"}
)

print("TABLES:", con.execute("SHOW TABLES").fetchall())

tests = {
    "Raw table access": "SELECT * FROM raw_orders LIMIT 1",
    "External file access": """
        SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv')
        LIMIT 1
    """
}

for name, query in tests.items():
    try:
        con.execute(query).fetchall()
        print(f"{name}: ACCESSIBLE")
    except Exception as e:
        print(f"{name}: BLOCKED")
        print(f"  Reason: {str(e).splitlines()[0]}")

con.close()