from sql_guardrails import validate_sql

test_queries = [
    ("SELECT * FROM fact_orders", True),
    ("SELECT * FROM monthly_kpis", True),
    ("SELECT * FROM raw_orders", False),
    ("DELETE FROM fact_orders", False),
    ("DROP TABLE fact_orders", False),
    ("SELECT * FROM fact_orders; DROP TABLE fact_orders", False),
    ("SELECT * FROM customer_metrics JOIN category_metrics ON 1=1", True),
    ("SELECT * FROM fact_orders WHERE order_status = 'delivered'", True),
    ("SELECT * FROM fact_orders -- comment", True),
    ("SELECT 1", False),
    ("SELECT * FROM fact_orders WHERE 1=1; SELECT 1", False),
]

for query, expected in test_queries:
    actual, message = validate_sql(query)
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {query}")
    if status == "FAIL":
        print(f"  Expected: {expected} | Actual: {actual} | {message}")

print("\nCTE bypass test:")
query = """
WITH x AS (SELECT * FROM raw_orders)
SELECT * FROM x
"""
print(validate_sql(query))

print("\nSubquery bypass test:")
query = """
SELECT * FROM fact_orders
WHERE order_id IN (
    SELECT order_id FROM raw_orders
)
"""
print(validate_sql(query))

print("\nFile-access bypass test:")
query = """
SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv')
"""
print(validate_sql(query))

print("\nSystem-table bypass test:")
query = """
SELECT * FROM duckdb_tables()
"""
print(validate_sql(query))

# CTE bypass test
query = """
WITH x AS (SELECT * FROM raw_orders)
SELECT * FROM x
"""

passed, message = validate_sql(query)
print(passed, message)
# Day 9 additional security tests

bypass_queries = [
    "SELECT * FROM RAW_ORDERS",
    'SELECT * FROM "raw_orders"',
    "SELECT * FROM main.raw_orders",
    "SELECT * FROM fact_orders UNION SELECT * FROM raw_orders",
    "SELECT * FROM (SELECT * FROM raw_orders) AS x",
    "SELECT read_text('secret.txt')",
    "SELECT * FROM pragma_database_list()",
]

for query in bypass_queries:
    is_valid, reason = validate_sql(query)

    assert is_valid is False, f"BYPASS: {query}"

print("All additional bypass tests passed.")