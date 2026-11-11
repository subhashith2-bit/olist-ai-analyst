
import pandas as pd
from datetime import datetime
import duckdb
import sys

def run_check(con, check_name, query, severity="ERROR"):
    failed_rows = con.sql(query).fetchall()[0][0]

    if failed_rows == 0:
        status = "PASS"
    elif severity == "WARN":
        status = "WARN"
    else:
        status = "FAIL"

    print(
        f"{status} | {check_name} | "
        f"Failed rows: {failed_rows} | Severity: {severity}"
    )

    return {
        "check_name": check_name,
        "failed_rows": failed_rows,
        "severity": severity,
        "status": status
    }


def main():
    con = duckdb.connect("olist.duckdb")

    print("\n===== DATA QUALITY CHECKS =====\n")

    results = []

    # Check 1: Orders should not have NULL order_id
    results.append(run_check(
        con,
        "Orders NULL order_id",
        """
        SELECT COUNT(*)
        FROM clean_orders
        WHERE order_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 2: Carrier handoff should not precede purchase
    results.append(run_check(
        con,
        "Carrier before purchase",
        """
        SELECT COUNT(*)
        FROM clean_orders
        WHERE order_delivered_carrier_date < order_purchase_timestamp
        """,
        severity="WARN"
    ))

    # Check 3: Delivered orders should have actual delivery dates
    results.append(run_check(
        con,
        "Delivered orders missing actual delivery date",
        """
        SELECT COUNT(*)
        FROM clean_orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NULL
        """,
        severity="WARN"
    ))

    # Check 4: Duplicate order IDs
    results.append(run_check(
        con,
        "Duplicate order_id groups",
        """
        SELECT COUNT(*)
        FROM (
            SELECT order_id
            FROM clean_orders
            GROUP BY order_id
            HAVING COUNT(*) > 1
        )
        """,
        severity="ERROR"
    ))

    # Check 5: Orders with NULL status
    results.append(run_check(
        con,
        "Orders NULL order_status",
        """
        SELECT COUNT(*)
        FROM clean_orders
        WHERE order_status IS NULL
        """,
        severity="ERROR"
    ))

    # Check 6: Orders with NULL purchase timestamp
    results.append(run_check(
        con,
        "Orders NULL purchase timestamp",
        """
        SELECT COUNT(*)
        FROM clean_orders
        WHERE order_purchase_timestamp IS NULL
        """,
        severity="ERROR"
    ))

    # Check 7: Order items without matching orders
    results.append(run_check(
        con,
        "Order items without matching orders",
        """
        SELECT COUNT(*)
        FROM clean_order_items i
        LEFT JOIN clean_orders o
            ON i.order_id = o.order_id
        WHERE o.order_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 8: Payments without matching orders
    results.append(run_check(
        con,
        "Payments without matching orders",
        """
        SELECT COUNT(*)
        FROM clean_order_payments p
        LEFT JOIN clean_orders o
            ON p.order_id = o.order_id
        WHERE o.order_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 9: Duplicate order item keys
    results.append(run_check(
        con,
        "Duplicate order item keys",
        """
        SELECT COUNT(*)
        FROM (
            SELECT order_id, order_item_id
            FROM clean_order_items
            GROUP BY order_id, order_item_id
            HAVING COUNT(*) > 1
        )
        """,
        severity="ERROR"
    ))

    # Check 10: Order items with NULL product or seller IDs
    results.append(run_check(
        con,
        "Order items NULL product or seller ID",
        """
        SELECT COUNT(*)
        FROM clean_order_items
        WHERE product_id IS NULL
           OR seller_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 11: Negative item price or freight
    results.append(run_check(
        con,
        "Negative item price or freight",
        """
        SELECT COUNT(*)
        FROM clean_order_items
        WHERE price < 0
           OR freight_value < 0
        """,
        severity="ERROR"
    ))

    # Check 12: Duplicate payment keys
    results.append(run_check(
        con,
        "Duplicate payment keys",
        """
        SELECT COUNT(*)
        FROM (
            SELECT order_id, payment_sequential
            FROM clean_order_payments
            GROUP BY order_id, payment_sequential
            HAVING COUNT(*) > 1
        )
        """,
        severity="ERROR"
    ))

    # Check 13: Negative payment values
    results.append(run_check(
        con,
        "Negative payment values",
        """
        SELECT COUNT(*)
        FROM clean_order_payments
        WHERE payment_value < 0
        """,
        severity="ERROR"
    ))

    # Check 14: Order items with NULL order_id or order_item_id
    results.append(run_check(
        con,
        "Order items NULL order identifiers",
        """
        SELECT COUNT(*)
        FROM clean_order_items
        WHERE order_id IS NULL
           OR order_item_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 15: Payments with NULL order_id or payment_sequential
    results.append(run_check(
        con,
        "Payments NULL order identifiers",
        """
        SELECT COUNT(*)
        FROM clean_order_payments
        WHERE order_id IS NULL
           OR payment_sequential IS NULL
        """,
        severity="ERROR"
    ))

    # Check 16: Payments with NULL payment_type or payment_value
    results.append(run_check(
        con,
        "Payments NULL type or value",
        """
        SELECT COUNT(*)
        FROM clean_order_payments
        WHERE payment_type IS NULL
           OR payment_value IS NULL
        """,
        severity="ERROR"
    ))

    # Check 17: NULL item price
    results.append(run_check(
        con,
        "Order items NULL price",
        """
        SELECT COUNT(*)
        FROM clean_order_items
        WHERE price IS NULL
        """,
        severity="ERROR"
    ))

    # Check 18: NULL freight value
    results.append(run_check(
        con,
        "Order items NULL freight",
        """
        SELECT COUNT(*)
        FROM clean_order_items
        WHERE freight_value IS NULL
        """,
        severity="ERROR"
    ))

    # Check 19: NULL review_id
    results.append(run_check(
        con,
        "Reviews NULL review_id",
        """
        SELECT COUNT(*)
        FROM clean_order_reviews
        WHERE review_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 20: NULL review order_id
    results.append(run_check(
        con,
        "Reviews NULL order_id",
        """
        SELECT COUNT(*)
        FROM clean_order_reviews
        WHERE order_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 21: Invalid review scores
    results.append(run_check(
        con,
        "Review score outside 1-5",
        """
        SELECT COUNT(*)
        FROM clean_order_reviews
        WHERE review_score IS NOT NULL
          AND (review_score < 1 OR review_score > 5)
        """,
        severity="ERROR"
    ))

    # Check 22: Review answer before creation
    results.append(run_check(
        con,
        "Review answer before creation",
        """
        SELECT COUNT(*)
        FROM clean_order_reviews
        WHERE review_answer_timestamp IS NOT NULL
          AND review_creation_date IS NOT NULL
          AND review_answer_timestamp < review_creation_date
        """,
        severity="WARN"
    ))

    # Check 23: Reviews without matching orders
    results.append(run_check(
        con,
        "Reviews without matching orders",
        """
        SELECT COUNT(*)
        FROM clean_order_reviews r
        LEFT JOIN clean_orders o
            ON r.order_id = o.order_id
        WHERE o.order_id IS NULL
        """,
        severity="ERROR"
    ))
        # Check 24: NULL product ID
    results.append(run_check(
        con,
        "Products NULL product_id",
        """
        SELECT COUNT(*)
        FROM clean_products
        WHERE product_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 25: Duplicate product IDs
    results.append(run_check(
        con,
        "Duplicate product_id groups",
        """
        SELECT COUNT(*)
        FROM (
            SELECT product_id
            FROM clean_products
            GROUP BY product_id
            HAVING COUNT(*) > 1
        )
        """,
        severity="ERROR"
    ))

    # Check 26: Negative dimensions or weight
    results.append(run_check(
        con,
        "Negative product dimensions or weight",
        """
        SELECT COUNT(*)
        FROM clean_products
        WHERE product_weight_g < 0
           OR product_length_cm < 0
           OR product_height_cm < 0
           OR product_width_cm < 0
        """,
        severity="ERROR"
    ))

    # Check 27: Negative photo count
    results.append(run_check(
        con,
        "Negative product photo count",
        """
        SELECT COUNT(*)
        FROM clean_products
        WHERE product_photos_qty < 0
        """,
        severity="ERROR"
    ))

    # Check 28: Negative name or description length
    results.append(run_check(
        con,
        "Negative product name or description length",
        """
        SELECT COUNT(*)
        FROM clean_products
        WHERE product_name_lenght < 0
           OR product_description_lenght < 0
        """,
        severity="ERROR"
    ))

    # Check 29: NULL product category after cleaning
    results.append(run_check(
        con,
        "Products NULL category after cleaning",
        """
        SELECT COUNT(*)
        FROM clean_products
        WHERE product_category_name IS NULL
        """,
        severity="ERROR"
    ))
        # Check 30: NULL customer_id
    results.append(run_check(
        con,
        "Customers NULL customer_id",
        """
        SELECT COUNT(*)
        FROM clean_customers
        WHERE customer_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 31: NULL customer_unique_id
    results.append(run_check(
        con,
        "Customers NULL customer_unique_id",
        """
        SELECT COUNT(*)
        FROM clean_customers
        WHERE customer_unique_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 32: NULL customer state
    results.append(run_check(
        con,
        "Customers NULL state",
        """
        SELECT COUNT(*)
        FROM clean_customers
        WHERE customer_state IS NULL
        """,
        severity="ERROR"
    ))

    # Check 33: NULL seller_id
    results.append(run_check(
        con,
        "Sellers NULL seller_id",
        """
        SELECT COUNT(*)
        FROM clean_sellers
        WHERE seller_id IS NULL
        """,
        severity="ERROR"
    ))

    # Check 34: NULL seller state
    results.append(run_check(
        con,
        "Sellers NULL state",
        """
        SELECT COUNT(*)
        FROM clean_sellers
        WHERE seller_state IS NULL
        """,
        severity="ERROR"
    ))

    # Check 35: NULL seller ZIP prefix
    results.append(run_check(
        con,
        "Sellers NULL ZIP prefix",
        """
        SELECT COUNT(*)
        FROM clean_sellers
        WHERE seller_zip_code_prefix IS NULL
        """,
        severity="ERROR"
    ))
        # Check 36: Orders row-count reconciliation
    results.append(run_check(
        con,
        "Orders raw-clean row count mismatch",
        """
        SELECT ABS(
            (SELECT COUNT(*) FROM raw_orders) -
            (SELECT COUNT(*) FROM clean_orders)
        )
        """,
        severity="ERROR"
    ))

    # Check 37: Order items row-count reconciliation
    results.append(run_check(
        con,
        "Order items raw-clean row count mismatch",
        """
        SELECT ABS(
            (SELECT COUNT(*) FROM raw_order_items) -
            (SELECT COUNT(*) FROM clean_order_items)
        )
        """,
        severity="ERROR"
    ))

    # Check 38: Payment row-count reconciliation
    results.append(run_check(
        con,
        "Payments unexpected row-count difference",
        """
        SELECT ABS(
            (SELECT COUNT(*) FROM raw_order_payments) -
            (SELECT COUNT(*) FROM clean_order_payments) - 3
        )
        """,
        severity="ERROR"
    ))

    # Check 39: Customers row-count reconciliation
    results.append(run_check(
        con,
        "Customers raw-clean row count mismatch",
        """
        SELECT ABS(
            (SELECT COUNT(*) FROM raw_customers) -
            (SELECT COUNT(*) FROM clean_customers)
        )
        """,
        severity="ERROR"
    ))

    # Check 40: Products row-count reconciliation
    results.append(run_check(
        con,
        "Products raw-clean row count mismatch",
        """
        SELECT ABS(
            (SELECT COUNT(*) FROM raw_products) -
            (SELECT COUNT(*) FROM clean_products)
        )
        """,
        severity="ERROR"
    ))
        # Check 41: Payment total reconciliation
    results.append(run_check(
        con,
        "Raw-clean payment total mismatch",
        """
        SELECT CASE
            WHEN ABS(
                (SELECT SUM(payment_value) FROM raw_order_payments) -
                (SELECT SUM(payment_value) FROM clean_order_payments)
            ) < 0.01
            THEN 0
            ELSE 1
        END
        """,
        severity="ERROR"
    ))

        # Save quality-check results in DuckDB
    results_df = pd.DataFrame(results)

    results_df["run_timestamp"] = datetime.now()

    con.register("results_df", results_df)

    con.sql("""
        CREATE OR REPLACE TABLE dq_results AS
        SELECT * FROM results_df
    """)

    con.unregister("results_df")

    print("\nQuality results saved to dq_results.")

    errors = [
        result for result in results
        if result["status"] == "FAIL"
        and result["severity"] == "ERROR"
    ]

    if errors:
        print("\nDATA QUALITY RESULT: FAILED")
        con.close()
        sys.exit(1)

    print("\nDATA QUALITY RESULT: PASSED")
    con.close()
    sys.exit(0)
    

    con.close()


if __name__ == "__main__":
    main()
