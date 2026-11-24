
import duckdb
import time
from pathlib import Path

from sql_guardrails import validate_sql, enforce_limit
from query_executor import execute_with_timeout


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"


evaluation_queries = {
    "Q1 - Total delivered GMV": """
        SELECT ROUND(SUM(gmv), 2) AS total_gmv
        FROM fact_orders
    """,

    "Q2 - Total orders": """
        SELECT COUNT(*) AS total_orders
        FROM fact_orders
    """,

    "Q3 - Monthly GMV trend": """
        SELECT month, gmv
        FROM monthly_kpis
        ORDER BY month
    """,

    "Q4 - Top 10 categories": """
        SELECT product_category_name, sales
        FROM category_metrics
        ORDER BY sales DESC
        LIMIT 10
    """,

    "Q5 - Repeat customer rate": """
        SELECT
            ROUND(
                COUNT(*) FILTER (WHERE is_repeat = TRUE)
                * 100.0 / COUNT(*),
                2
            ) AS repeat_customer_rate
        FROM customer_metrics
    """,

    "Q6 - Delivered orders count": """
        SELECT COUNT(*) AS delivered_orders
        FROM fact_orders
        WHERE is_delivered = TRUE
    """,

    "Q7 - January 2018 GMV": """
        SELECT ROUND(gmv, 2) AS january_gmv
        FROM monthly_kpis
        WHERE month = DATE '2018-01-01'
    """,

    "Q8 - Average rating: late vs on-time": """
        SELECT
            ROUND(AVG(review_score) FILTER (WHERE is_late = TRUE), 2)
                AS late_avg_rating,
            ROUND(AVG(review_score) FILTER (WHERE is_late = FALSE), 2)
                AS on_time_avg_rating
        FROM fact_orders
    """,

    "Q9 - Category average price": """
        SELECT product_category_name, average_price
        FROM category_metrics
        ORDER BY average_price DESC
        LIMIT 10
    """,

    "Q10 - State-wise late delivery rate": """
        SELECT
            customer_state,
            ROUND(
                COUNT(*) FILTER (WHERE is_late = TRUE) * 100.0
                / NULLIF(COUNT(*) FILTER (WHERE is_late IS NOT NULL), 0),
                2
            ) AS late_rate_pct
        FROM fact_orders
        GROUP BY customer_state
        ORDER BY late_rate_pct DESC
    """

}


def main():

    con = duckdb.connect(
        str(SERVING_DB),
        read_only=True,
        config={
            "enable_external_access": "false",
            "memory_limit": "2GB"
        }
    )

    passed = 0
    failed = 0

    print("\n===== DAY 9 REGRESSION TEST =====")
    try:
        for question, query in evaluation_queries.items():

            print(f"\nTEST: {question}")

            try:
                # 1. Validate SQL
                is_valid, message = validate_sql(query)

                if not is_valid:
                    raise ValueError(f"Validation rejected query: {message}")

                # 2. Enforce result limit
                final_sql = enforce_limit(query)

                # 3. Execute with application timeout
                start = time.perf_counter()

                result = execute_with_timeout(
                    con,
                    final_sql,
                    timeout_seconds=5
                )

                elapsed = time.perf_counter() - start

                if result.empty:
                    raise ValueError("Empty result returned")

                print("STATUS: PASS")
                print("VALIDATION:", message)
                print(f"ROWS: {len(result)}")
                print(f"TIME: {elapsed:.3f}s")
                print(result.to_string(index=False))

                passed += 1

            except Exception as e:
                print("STATUS: FAIL")
                print("ERROR:", type(e).__name__, str(e))
                failed += 1

    finally:
        con.close()

    print("\n===== REGRESSION SUMMARY =====")
    print("Total tests:", passed + failed)
    print("Passed:", passed)
    print("Failed:", failed)


if __name__ == "__main__":
    main()
