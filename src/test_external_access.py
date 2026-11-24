import duckdb

con = duckdb.connect(
    "olist_serving.duckdb",
    read_only=True,
    config={"enable_external_access": "false"}
)

queries = [
    "SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv')",
    "SELECT * FROM read_parquet('some_file.parquet')",
]

for q in queries:
    try:
        con.sql(q).fetchall()
        print("FAIL: External access was allowed")
    except Exception as e:
        print("PASS: External access blocked -", type(e).__name__)

con.close()