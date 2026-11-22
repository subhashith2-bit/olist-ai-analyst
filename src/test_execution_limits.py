import duckdb
from pathlib import Path
from sql_guardrails import validate_sql, enforce_limit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"

con = duckdb.connect(
    str(SERVING_DB),
    read_only=True,
    config={"enable_external_access": "false"}
)

queries = [
    "SELECT order_id FROM fact_orders",
    "SELECT order_id FROM fact_orders LIMIT 10",
    "SELECT order_id FROM fact_orders LIMIT 1000",
]

for query in queries:
    print("\nOriginal SQL:", query)

    valid, message = validate_sql(query)
    assert valid, f"Validation failed: {message}"

    safe_sql = enforce_limit(query)
    print("Enforced SQL:", safe_sql)

    result = con.execute(safe_sql).fetchall()
    print("Rows returned:", len(result))

    assert len(result) <= 500, "Result exceeded the row limit!"

print("\nAll integrated limit tests passed.")

con.close()