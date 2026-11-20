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