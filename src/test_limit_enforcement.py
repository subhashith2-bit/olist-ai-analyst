
from sql_guardrails import enforce_limit

tests = [
    ("SELECT order_id FROM fact_orders", 500),
    ("SELECT order_id FROM fact_orders LIMIT 10", 10),
    ("SELECT order_id FROM fact_orders LIMIT 1000", 500),
]

for query, expected in tests:
    result = enforce_limit(query)
    print(f"\nOriginal: {query}")
    print(f"Final:    {result}")
    print(f"Expected maximum rows: {expected}")
