
import duckdb
from llm import call_llm
from sql_guardrails import validate_sql
import pandas as pd


SCHEMA = """
You are a SQL analyst using DuckDB.

Only use these tables and columns:

fact_orders:
order_id, customer_id, customer_city, customer_state, order_status,
order_purchase_timestamp, order_approved_at, order_delivered_carrier_date,
order_delivered_customer_date, order_estimated_delivery_date,
n_items, n_sellers, items_value, freight_value, payment_total,
n_payments, main_payment_type, review_score, gmv, delivery_days,
delay_days, is_late, is_delivered

customer_metrics:
customer_unique_id, first_order_date, last_order_date, order_count,
non_canceled_order_count, delivered_order_count, lifetime_gmv, aov,
is_repeat, is_repeat_non_canceled, days_to_second_order,
most_recent_state

category_metrics:
product_category_name, items_sold, sales, average_price,
freight_share, average_review_score, late_delivery_rate,
number_of_sellers

monthly_kpis:
month, orders, low_volume, delivered_orders, gmv, aov,
new_customers, returning_customer_orders, cancellation_rate,
late_rate, average_review_score, previous_month_gmv,
mom_gmv_growth_pct, is_partial_month

Business rules:
- GMV is delivered order item value plus freight.
- Use fact_orders for order-level analysis.
- Use customer_metrics for customer-level analysis.
- Use customer_unique_id for customer analysis.
- Use category_metrics for category analysis.
- Use monthly_kpis for monthly analysis.
- Only delivered orders contribute to GMV.
- AOV is delivered GMV divided by delivered order count.
- NULL is_late values must not be included in late-rate denominators.
- Monetary values are in Brazilian reais (R$).
- Aggregate before joining tables if joins could cause fan-out.

SQL rules:
- Generate only read-only SQL.
- Only use the documented tables and columns.
- Do not use SELECT *.
- Do not generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE or other modifying SQL.
- Return only SQL, without Markdown fences or explanations.
- Generate only one SQL statement.
- For rate or percentage questions, multiply the proportion by 100 and ROUND to 2 decimal places.
- Label percentage results clearly, preferably with a column name ending in _pct.
"""

def clean_sql(sql):
    sql = sql.strip()

    if sql.startswith("```"):
        sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql

def main():
    question = input("Ask a business question: ")

    prompt = f"""
{SCHEMA}

Business question:
{question}

Generate SQL to answer this question.
"""

    try:
        sql = clean_sql(call_llm(prompt))
    except Exception as e:
        print(f"\nGemini API error: {e}")
        print("Please try again later.")
        return

    print("\n===== GENERATED SQL =====")
    print(sql)

    is_valid, message = validate_sql(sql)

    print("\n===== VALIDATION =====")
    print(message)

    if not is_valid:
        print("Query rejected. It will not be executed.")
        return

    con = duckdb.connect("olist.duckdb", read_only=True)

    try:
        result = con.sql(sql).df()

        print("\n===== RESULT =====")

        pd.options.display.float_format = "{:,.2f}".format
        print(result.to_string(index=False))

    except Exception as e:
        print(f"\nQuery execution failed: {e}")

    finally:
        con.close()


if __name__ == "__main__":
    main()
