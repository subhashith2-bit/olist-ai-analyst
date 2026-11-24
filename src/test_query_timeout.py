import duckdb
from pathlib import Path
from query_executor import execute_with_timeout

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"

con = duckdb.connect(
    str(SERVING_DB),
    read_only=True,
    config={"enable_external_access": "false"}
)

# Normal query should complete
print("Testing normal query...")

result = execute_with_timeout(
    con,
    "SELECT COUNT(*) AS total FROM fact_orders",
    timeout_seconds=5
)

print("Normal query passed:", result.iloc[0, 0])


# Deliberately expensive query to test interruption
print("\nTesting timeout...")

try:
    execute_with_timeout(
        con,
        "SELECT SUM(i) FROM range(1000000000000) AS t(i)",
        timeout_seconds=2
    )

    print("WARNING: Query completed before timeout.")

except Exception as e:
    print("Query interrupted:")
    print(str(e).splitlines()[0])

con.close()