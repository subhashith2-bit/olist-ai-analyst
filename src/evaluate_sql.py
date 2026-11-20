
import duckdb
import time


def main():
    con = duckdb.connect("olist.duckdb", read_only=True)

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
        """
    }

    print("\n===== SQL EVALUATION =====\n")

    passed = 0
    failed = 0

    for question, query in evaluation_queries.items():
        start = time.time()

        try:
            result = con.sql(query).df()

            elapsed = time.time() - start

            if not result.empty:
                print(f"[PASS] {question}")
                print(f"       Rows returned: {len(result)}")
                print(f"       Time: {elapsed:.3f}s")
                passed += 1
            else:
                print(f"[FAIL] {question}")
                print("       Empty result")
                failed += 1

        except Exception as e:
            print(f"[FAIL] {question}")
            print(f"       Error: {e}")
            failed += 1

    print("\n===== SUMMARY =====")
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    con.close()


if __name__ == "__main__":
    main()
