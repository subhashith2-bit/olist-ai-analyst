import duckdb

con = duckdb.connect(
    "olist_serving.duckdb",
    read_only=True,
    config={"enable_external_access": "false"}
)

try:
    con.sql("DROP TABLE fact_orders")
    print("FAIL: DROP was allowed")
except Exception as e:
    print("PASS: Write blocked -", type(e).__name__, str(e))

con.close()