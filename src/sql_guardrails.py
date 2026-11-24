import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {
    "fact_orders",
    "customer_metrics",
    "category_metrics",
    "monthly_kpis"
}

BLOCKED_FUNCTIONS = {
    "read_csv",
    "read_csv_auto",
    "read_parquet",
    "read_json",
    "read_json_auto",
    "read_text",
    "read_blob",
    "read_ndjson",
    "read_xlsx",
    "glob",
    "getenv",
    "current_setting"
}


def validate_sql(query):
    query = query.strip()

    # 1. Parse SQL
    try:
        statements = sqlglot.parse(query, read="duckdb")
    except Exception as e:
        return False, f"SQL parsing failed: {e}"

    # 2. Exactly one statement
    if len(statements) != 1 or statements[0] is None:
        return False, "Exactly one SQL statement is allowed."

    tree = statements[0]

    # Block recursive CTEs
    with_clause = tree.args.get("with_")

    if with_clause and with_clause.args.get("recursive"):
        return False, "Recursive CTEs are not allowed."
    
    # 3. Only SELECT-based queries
    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        return False, "Only SELECT queries are allowed."

    # 4. Collect CTE names
    cte_names = {
        cte.alias_or_name.lower()
        for cte in tree.find_all(exp.CTE)
    }

    # 5. Inspect table references
    tables = list(tree.find_all(exp.Table))

    
# 6. Reject CROSS JOINs and unsafe join conditions
    for join in tree.find_all(exp.Join):

        if join.args.get("kind", "").upper() == "CROSS":
            return False, "CROSS JOINs are not allowed."

        on_condition = join.args.get("on")
        using_condition = join.args.get("using")

    # Reject comma joins and joins without explicit conditions
        if on_condition is None and not using_condition:
            return False, "JOINs must have an ON or USING condition."

    # Reject constant conditions such as ON 1=1 or ON TRUE
        if on_condition is not None:
            if not list(on_condition.find_all(exp.Column)):
                return False, "JOIN conditions must reference columns."

    if not tables:
        return False, "No table detected in query."

    for table in tables:
        table_name = table.name.lower()

        # Reject table functions
        if not isinstance(table.this, exp.Identifier):
            return False, "Table functions are not allowed."

        # Reject schema/catalog-qualified tables
        if table.db or table.catalog:
            return False, "Schema-qualified tables are not allowed."

        # Allow approved tables or CTE references
        if table_name not in ALLOWED_TABLES and table_name not in cte_names:
            return False, f"Table not allowed: {table_name}"

    # 6. Inspect functions
    for func in tree.find_all(exp.Func):
        func_name = func.sql_name().lower()

        if func_name in BLOCKED_FUNCTIONS:
            return False, f"Function not allowed: {func_name}"

    return True, "SQL passed validation."

def enforce_limit(query, max_rows=500):
    parsed = sqlglot.parse_one(query, read="duckdb")

    existing_limit = parsed.args.get("limit")

    if existing_limit is not None:
        limit_value = existing_limit.expression

        if isinstance(limit_value, exp.Literal) and limit_value.is_int:
            current_limit = int(limit_value.this)

            if current_limit <= max_rows:
                return query

    parsed = parsed.limit(max_rows, copy=False)

    return parsed.sql(dialect="duckdb")