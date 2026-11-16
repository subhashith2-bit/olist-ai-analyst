import duckdb

def main():

    con = duckdb.connect("olist.duckdb")

    print("\n===== BUILDING ANALYTICS TABLES =====\n")

        # Build fact_orders: one row per order
    con.sql("""
        CREATE OR REPLACE TABLE fact_orders AS

        WITH items_agg AS (
            SELECT
                order_id,
                COUNT(*) AS n_items,
                COUNT(DISTINCT seller_id) AS n_sellers,
                SUM(price) AS items_value,
                SUM(freight_value) AS freight_value
            FROM clean_order_items
            GROUP BY order_id
        ),

        payment_agg AS (
            SELECT
                order_id,
                COUNT(*) AS n_payments,
                SUM(payment_value) AS payment_total,
                MODE(payment_type) AS main_payment_type
            FROM clean_order_payments
            GROUP BY order_id
        ),

        review_agg AS (
            SELECT
                order_id,
                AVG(review_score) AS review_score
            FROM clean_order_reviews
            GROUP BY order_id
        )

        SELECT
            o.order_id,
            o.customer_id,
            c.customer_city,
            c.customer_state,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_approved_at,
            o.order_delivered_carrier_date,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,

            COALESCE(i.n_items, 0) AS n_items,
            COALESCE(i.n_sellers, 0) AS n_sellers,
            COALESCE(i.items_value, 0) AS items_value,
            COALESCE(i.freight_value, 0) AS freight_value,

            COALESCE(p.payment_total, 0) AS payment_total,
            COALESCE(p.n_payments, 0) AS n_payments,
            p.main_payment_type,

            r.review_score,

            CASE
                WHEN o.order_status = 'delivered'
                THEN COALESCE(i.items_value, 0) + COALESCE(i.freight_value, 0)
            ELSE 0
            END AS gmv,

            DATE_DIFF(
                'day',
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            ) AS delivery_days,

            CASE
                WHEN o.order_status = 'delivered'
                AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_estimated_delivery_date IS NOT NULL
                THEN DATE_DIFF(
                        'day',
                     CAST(o.order_estimated_delivery_date AS DATE),
                    CAST(o.order_delivered_customer_date AS DATE)
                    )
             ELSE NULL
                END AS delay_days,

            CASE
                WHEN o.order_status = 'delivered'
                AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_estimated_delivery_date IS NOT NULL
                THEN CAST(o.order_delivered_customer_date AS DATE)
                > CAST(o.order_estimated_delivery_date AS DATE)
            ELSE NULL
            END AS is_late,

            o.order_status = 'delivered' AS is_delivered

        FROM clean_orders o
        LEFT JOIN items_agg i ON o.order_id = i.order_id
        LEFT JOIN payment_agg p ON o.order_id = p.order_id
        LEFT JOIN review_agg r ON o.order_id = r.order_id
        LEFT JOIN clean_customers c
            ON o.customer_id = c.customer_id
    """)

    print(
        "fact_orders:",
        con.sql("SELECT COUNT(*) FROM fact_orders").fetchall()[0][0]
    )
        # Build customer_metrics: one row per unique customer
    con.sql("""
        CREATE OR REPLACE TABLE customer_metrics AS

        WITH customer_orders AS (
            SELECT
                f.order_id,
                c.customer_unique_id,
                c.customer_state,
                f.order_status,
                f.order_purchase_timestamp,
                f.gmv
            FROM fact_orders f
            JOIN clean_customers c
                ON f.customer_id = c.customer_id
        ),

        customer_summary AS (
        SELECT
            customer_unique_id,
            MIN(order_purchase_timestamp) AS first_order_date,
            MAX(order_purchase_timestamp) AS last_order_date,

            COUNT(*) AS order_count,

            COUNT(*) FILTER (
            WHERE order_status <> 'canceled'
            ) AS non_canceled_order_count,

            COUNT(*) FILTER (
            WHERE order_status = 'delivered'
            ) AS delivered_order_count,

            SUM(gmv) AS lifetime_gmv

            FROM customer_orders
            GROUP BY customer_unique_id
        ),

        ranked_orders AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY customer_unique_id
                    ORDER BY order_purchase_timestamp, order_id
                ) AS order_number
            FROM customer_orders
        ),

        second_orders AS (
            SELECT
                customer_unique_id,
                order_purchase_timestamp AS second_order_date
            FROM ranked_orders
            WHERE order_number = 2
        ),

        latest_state AS (
            SELECT
                customer_unique_id,
                customer_state AS most_recent_state
            FROM ranked_orders
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY customer_unique_id
                ORDER BY order_purchase_timestamp DESC, order_id DESC
            ) = 1
        )

        SELECT
            s.customer_unique_id,
            s.first_order_date,
            s.last_order_date,
            s.order_count,
            s.non_canceled_order_count,
            s.delivered_order_count,
            s.lifetime_gmv,

            s.lifetime_gmv / NULLIF(s.delivered_order_count, 0) AS aov,

            s.order_count > 1 AS is_repeat,

            s.non_canceled_order_count > 1 AS is_repeat_non_canceled,

            DATE_DIFF(
                'day',
                s.first_order_date,
                so.second_order_date
            ) AS days_to_second_order,

            ls.most_recent_state

        FROM customer_summary s
        LEFT JOIN second_orders so
            ON s.customer_unique_id = so.customer_unique_id
        LEFT JOIN latest_state ls
            ON s.customer_unique_id = ls.customer_unique_id
    """)

    print(
        "customer_metrics:",
        con.sql("SELECT COUNT(*) FROM customer_metrics").fetchall()[0][0]
    )
        # Build category_metrics: one row per product category
    con.sql("""
        CREATE OR REPLACE TABLE category_metrics AS

        WITH category_items AS (
            SELECT
                i.order_id,
                i.product_id,
                i.seller_id,
                i.price,
                i.freight_value,
                COALESCE(p.product_category_name, 'unknown')
                    AS product_category_name
            FROM clean_order_items i
            LEFT JOIN clean_products p
                ON i.product_id = p.product_id
        ),

        category_items_enriched AS (
            SELECT
                ci.*,
                f.review_score,
                f.is_late,
                f.order_status
            FROM category_items ci
            JOIN fact_orders f
                ON ci.order_id = f.order_id
        )

        SELECT
            product_category_name,
            COUNT(*) AS items_sold,
            SUM(price) AS sales,
            AVG(price) AS average_price,

            SUM(freight_value)
                / NULLIF(SUM(price), 0) AS freight_share,

            AVG(review_score) AS average_review_score,

            COUNT(*) FILTER (WHERE is_late = TRUE) * 1.0
                / NULLIF(COUNT(is_late), 0) AS late_delivery_rate,

            COUNT(DISTINCT seller_id) AS number_of_sellers

        FROM category_items_enriched
        WHERE order_status = 'delivered'
        GROUP BY product_category_name
    """)

    print(
        "category_metrics:",
        con.sql("SELECT COUNT(*) FROM category_metrics").fetchall()[0][0]
    )
        # Build monthly_kpis: one row per calendar month
    con.sql("""
        CREATE OR REPLACE TABLE monthly_kpis AS

        WITH month_calendar AS (
            SELECT month
            FROM generate_series(
                DATE '2016-09-01',
                DATE '2018-10-01',
                INTERVAL '1 month'
            ) AS t(month)
        ),

        order_customer_map AS (
            SELECT
                customer_id,
                customer_unique_id
            FROM clean_customers
        ),

        monthly_aggregates AS (
            SELECT
                DATE_TRUNC('month', f.order_purchase_timestamp)::DATE
                    AS month,

                COUNT(*) AS orders,

                COUNT(*) FILTER (
                    WHERE f.is_delivered
                ) AS delivered_orders,

                SUM(f.gmv) AS gmv,

                SUM(f.gmv) / NULLIF(
                    COUNT(*) FILTER (WHERE f.is_delivered), 0
                ) AS aov,

                COUNT(DISTINCT m.customer_unique_id) FILTER (
                    WHERE DATE_TRUNC(
                        'month', f.order_purchase_timestamp
                    ) = DATE_TRUNC(
                        'month', cm.first_order_date
                    )
                ) AS new_customers,

                COUNT(*) FILTER (
                    WHERE DATE_TRUNC(
                        'month', f.order_purchase_timestamp
                    ) > DATE_TRUNC(
                        'month', cm.first_order_date
                    )
                ) AS returning_customer_orders,

                COUNT(*) FILTER (
                    WHERE f.order_status = 'canceled'
                ) * 1.0 / NULLIF(COUNT(*), 0)
                    AS cancellation_rate,

                COUNT(*) FILTER (
                    WHERE f.is_late = TRUE
                ) * 1.0 / NULLIF(COUNT(f.is_late), 0)
                    AS late_rate,

                AVG(f.review_score) AS average_review_score

            FROM fact_orders f
            JOIN order_customer_map m
                ON f.customer_id = m.customer_id
            JOIN customer_metrics cm
                ON m.customer_unique_id = cm.customer_unique_id

            GROUP BY 1
        ),

        monthly_with_previous AS (
        SELECT
        c.month,
        COALESCE(a.orders, 0) AS orders,
        COALESCE(a.orders, 0) < 100 AS low_volume,
        COALESCE(a.delivered_orders, 0) AS delivered_orders,
        COALESCE(a.gmv, 0) AS gmv,
        COALESCE(a.aov, 0) AS aov,
        COALESCE(a.new_customers, 0) AS new_customers,
        COALESCE(a.returning_customer_orders, 0)
            AS returning_customer_orders,
        COALESCE(a.cancellation_rate, 0) AS cancellation_rate,
        COALESCE(a.late_rate, 0) AS late_rate,
        COALESCE(a.average_review_score, 0)
            AS average_review_score,

        LAG(COALESCE(a.gmv, 0)) OVER (
            ORDER BY c.month
        ) AS previous_month_gmv

        FROM month_calendar c
        LEFT JOIN monthly_aggregates a
        ON c.month = a.month
        )
        SELECT
            *,
            (
                (gmv - previous_month_gmv)
                / NULLIF(previous_month_gmv, 0)
            ) * 100 AS mom_gmv_growth_pct,

            month IN (
                DATE '2016-09-01',
                DATE '2018-10-01'
            ) AS is_partial_month

        FROM monthly_with_previous
    """)

    print(
        "monthly_kpis:",
        con.sql("SELECT COUNT(*) FROM monthly_kpis").fetchall()[0][0]
    )
        # Final analytics validation
    print("\n===== ANALYTICS VALIDATION =====\n")

    # Check row counts
    tables = [
        "fact_orders",
        "customer_metrics",
        "category_metrics",
        "monthly_kpis"
    ]

    for table in tables:
        row_count = con.sql(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchall()[0][0]

        print(f"{table}: {row_count:,} rows")

    # Check GMV reconciliation
    fact_gmv = con.sql("""
        SELECT SUM(gmv) FROM fact_orders
    """).fetchall()[0][0]

    monthly_gmv = con.sql("""
        SELECT SUM(gmv) FROM monthly_kpis
    """).fetchall()[0][0]

    customer_gmv = con.sql("""
        SELECT SUM(lifetime_gmv) FROM customer_metrics
    """).fetchall()[0][0]

    print("\n===== GMV RECONCILIATION =====")
    print(f"Fact orders GMV: R${fact_gmv:,.2f}")
    print(f"Monthly KPIs GMV: R${monthly_gmv:,.2f}")
    print(f"Customer metrics GMV: R${customer_gmv:,.2f}")

    if (
        abs(fact_gmv - monthly_gmv) < 0.01
        and abs(fact_gmv - customer_gmv) < 0.01
    ):
        print("GMV reconciliation: PASSED")
    else:
        print("GMV reconciliation: FAILED")

    con.close()


if __name__ == "__main__":
    main()