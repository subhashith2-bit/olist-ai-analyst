from sql_guardrails import enforce_limit

tests = [
    "SELECT order_id FROM fact_orders",
    "SELECT order_id FROM fact_orders LIMIT 10",
    "SELECT order_id FROM fact_orders LIMIT 1000",
]

for query in tests:
    print("\nOriginal:", query)
    print("Safe:", enforce_limit(query))