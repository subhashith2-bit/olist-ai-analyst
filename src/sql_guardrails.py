
import duckdb
import re

ALLOWED_TABLES = {
    "fact_orders",
    "customer_metrics",
    "category_metrics",
    "monthly_kpis"
}


def validate_sql(query):
    query = query.strip()

    # 1. Parse SQL using DuckDB
    try:
        statements = duckdb.extract_statements(query)
    except Exception as e:
        return False, f"SQL parsing failed: {e}"

    # 2. Require exactly one SQL statement
    if len(statements) != 1:
        return False, "Exactly one SQL statement is allowed."

    # 3. Allow only SELECT statements
    if statements[0].type != duckdb.StatementType.SELECT:
        return False, "Only SELECT statements are allowed."

    # 4. Detect tables used in FROM and JOIN
    tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        query,
        re.IGNORECASE
    )

    # 5. Require at least one detected table
    if not tables:
        return False, "No table detected in query."

    # 6. Restrict access to allowed analytics tables
    for table in tables:
        if table.lower() not in ALLOWED_TABLES:
            return False, f"Table not allowed: {table}"

    return True, "SQL passed validation."
