
import duckdb
import time
from pathlib import Path
from query_executor import execute_with_timeout

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"

con = duckdb.connect(
    str(SERVING_DB),
    read_only=True,
    config={"enable_external_access": "false"}
)

# Deliberately expensive query to trigger the timeout
q = """
SELECT SUM(i)
FROM range(10000000000) t(i)
"""

print("Starting query with 5-second timeout...")

start = time.perf_counter()

try:
    execute_with_timeout(con, q, timeout_seconds=5)
    print("Query completed before timeout.")

except Exception as e:
    print("Query stopped:", type(e).__name__, str(e))

finally:
    elapsed = time.perf_counter() - start
    print(f"Elapsed time: {elapsed:.2f} seconds")

# Check whether the same connection still works
print("\nTesting connection recovery...")

try:
    result = con.execute("SELECT 42 AS test_value").fetchdf()
    print("RECOVERY SUCCESS")
    print(result.to_string(index=False))

except Exception as e:
    print("RECOVERY FAILED:", type(e).__name__, str(e))

con.close()
