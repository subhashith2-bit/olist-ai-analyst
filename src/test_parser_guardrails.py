from sql_guardrails import validate_sql

# Legitimate queries that should pass
allowed_queries = [
    "SELECT order_id FROM fact_orders LIMIT 10",
    "SELECT COUNT(*) FROM fact_orders",
    "SELECT * FROM monthly_kpis WHERE gmv > 1000",
    """
    SELECT customer_unique_id, lifetime_gmv
    FROM customer_metrics
    ORDER BY lifetime_gmv DESC
    LIMIT 10
    """,
    """
    WITH x AS (
        SELECT order_id FROM fact_orders
    )
    SELECT order_id FROM x
    """,
    """
    SELECT order_id FROM fact_orders
    UNION
    SELECT order_id FROM fact_orders
    """,
    "SELECT a.order_id FROM fact_orders a JOIN fact_orders b ON a.order_id = b.order_id LIMIT 10",
]

# Unsafe queries that should fail
blocked_queries = [
    "SELECT * FROM raw_orders",
    'SELECT * FROM "raw_orders"',
    "SELECT * FROM main.fact_orders",
    "SELECT * FROM fact_orders UNION SELECT * FROM raw_orders",
    "SELECT * FROM (SELECT * FROM raw_orders) AS x",
    "SELECT * FROM read_csv_auto('data/raw/file.csv')",
    "SELECT read_text('secret.txt')",
    "SELECT * FROM pragma_database_list()",
    "SELECT * FROM fact_orders; DROP TABLE fact_orders",
    "DELETE FROM fact_orders",
    "SELECT COUNT(*) FROM fact_orders CROSS JOIN fact_orders",
    "WITH RECURSIVE counter AS (SELECT 1 UNION ALL SELECT 1 FROM counter) SELECT * FROM counter",
    "SELECT query FROM query_table()",

    # Realistic table-function and environment-access tests
    "SELECT * FROM query_table('raw_orders')",
    "SELECT * FROM glob('data/raw/*.csv')",
    "SELECT getenv('GEMINI_API_KEY')",
    "SELECT * FROM range(10)",
    "SELECT COUNT(*) FROM fact_orders a, fact_orders b",
    "SELECT COUNT(*) FROM fact_orders a JOIN fact_orders b ON 1=1",
    "SELECT COUNT(*) FROM fact_orders a INNER JOIN fact_orders b ON TRUE",

]

print("===== ALLOWED QUERY TESTS =====")

for query in allowed_queries:
    is_valid, message = validate_sql(query)
    print(f"{'PASS' if is_valid else 'FAIL'}: {message}")

    assert is_valid, f"Legitimate SQL rejected: {query}"


print("\n===== BLOCKED QUERY TESTS =====")

for query in blocked_queries:
    is_valid, message = validate_sql(query)
    print(f"{'PASS' if not is_valid else 'FAIL'}: {message}")

    assert not is_valid, f"Dangerous SQL accepted: {query}"


print("\nAll parser validator tests passed.")