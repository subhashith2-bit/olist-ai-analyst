import duckdb
from llm import call_llm, MODEL_NAME
from sql_guardrails import validate_sql, enforce_limit
import pandas as pd
from pathlib import Path
from query_executor import execute_with_timeout
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"
LOG_DB = PROJECT_ROOT / "llm_runs.duckdb"


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


def log_run(
    question,
    model,
    generated_sql,
    validation_status,
    validation_message,
    final_sql,
    execution_status,
    error_message,
    llm_seconds,
    sql_seconds,
    rows_returned
):
    log_con = duckdb.connect(str(LOG_DB))

    try:
        log_con.execute("""
            CREATE TABLE IF NOT EXISTS llm_runs (
                run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                question VARCHAR,
                model VARCHAR,
                generated_sql VARCHAR,
                validation_status VARCHAR,
                validation_message VARCHAR,
                final_sql VARCHAR,
                execution_status VARCHAR,
                error_message VARCHAR,
                llm_seconds DOUBLE,
                sql_seconds DOUBLE,
                rows_returned INTEGER
            )
        """)

        log_con.execute("""
            INSERT INTO llm_runs (
                question,
                model,
                generated_sql,
                validation_status,
                validation_message,
                final_sql,
                execution_status,
                error_message,
                llm_seconds,
                sql_seconds,
                rows_returned
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            question,
            model,
            generated_sql,
            validation_status,
            validation_message,
            final_sql,
            execution_status,
            error_message,
            llm_seconds,
            sql_seconds,
            rows_returned
        ])

    finally:
        log_con.close()


def main():
    question = input("Ask a business question: ")

    prompt = f"""
{SCHEMA}

Business question:
{question}

Generate SQL to answer this question.
"""

    generated_sql = None
    final_sql = None
    validation_status = "NOT_CHECKED"
    validation_message = None
    execution_status = "NOT_EXECUTED"
    error_message = None
    llm_seconds = None
    sql_seconds = None
    rows_returned = None

    # LLM generation
    llm_start = time.perf_counter()

    try:
        generated_sql = clean_sql(call_llm(prompt))
        llm_seconds = round(time.perf_counter() - llm_start, 3)

    except Exception as e:
        llm_seconds = round(time.perf_counter() - llm_start, 3)
        error_message = str(e)
        execution_status = "LLM_FAILED"

        print(f"\nGemini API error: {e}")

        log_run(
            question, MODEL_NAME, generated_sql,
            validation_status, validation_message,
            final_sql, execution_status, error_message,
            llm_seconds, sql_seconds, rows_returned
        )
        return

    print("\n===== GENERATED SQL =====")
    print(generated_sql)

    # Validation
    is_valid, validation_message = validate_sql(generated_sql)

    validation_status = "PASSED" if is_valid else "REJECTED"

    print("\n===== VALIDATION =====")
    print(validation_message)

    if not is_valid:
        execution_status = "REJECTED"

        print("Query rejected. It will not be executed.")

        log_run(
            question, MODEL_NAME, generated_sql,
            validation_status, validation_message,
            final_sql, execution_status, error_message,
            llm_seconds, sql_seconds, rows_returned
        )
        return

    # Enforce result limit
    final_sql = enforce_limit(generated_sql)

    print("\n===== FINAL SQL (LIMIT ENFORCED) =====")
    print(final_sql)

    # Execute against isolated serving database
    con = duckdb.connect(
        str(SERVING_DB),
        read_only=True,
        config={"enable_external_access": "false"}
    )

    sql_start = time.perf_counter()

    try:
        result = execute_with_timeout(
            con,
            final_sql,
            timeout_seconds=5
        )

        sql_seconds = round(time.perf_counter() - sql_start, 3)
        rows_returned = len(result)
        execution_status = "SUCCESS"

        print("\n===== RESULT =====")

        pd.options.display.float_format = "{:,.2f}".format
        print(result.to_string(index=False))

    except Exception as e:
        sql_seconds = round(time.perf_counter() - sql_start, 3)
        error_message = str(e)
        execution_status = "SQL_FAILED"

        print(f"\nQuery execution failed or timed out: {e}")

    finally:
        con.close()

    # Log the completed run
    log_run(
        question, MODEL_NAME, generated_sql,
        validation_status, validation_message,
        final_sql, execution_status, error_message,
        llm_seconds, sql_seconds, rows_returned
    )

    print("\n===== RUN TIMING =====")
    print(f"LLM time: {llm_seconds} seconds")
    print(f"SQL time: {sql_seconds} seconds")
    print(f"Execution status: {execution_status}")

    print("\nRun recorded in llm_runs.duckdb")


if __name__ == "__main__":
    main()