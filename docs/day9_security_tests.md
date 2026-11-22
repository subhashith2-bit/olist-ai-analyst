# SQL Security Tests

## 1. SQL Validator Tests
- Raw tables: Blocked
- Schema-qualified tables: Blocked
- External file/table functions: Blocked
- Multiple SQL statements: Blocked
- Non-SELECT statements: Blocked
- CTE and subquery bypasses: Blocked

## 2. Serving Database Isolation
- Approved analytics tables accessible: Verified
- Raw tables inaccessible: Verified
- External file access disabled: Verified

## 3. Execution Protection
- Row limit: LIMIT 500 enforced
- Query timeout: Tested separately; interruption verified
- Read-only connection: Verified

## 4. CROSS JOIN Protection
- **Test:** `SELECT COUNT(*) FROM fact_orders CROSS JOIN fact_orders`
- **Before hardening:** Executed successfully, returning 9,888,512,481; LIMIT 500 did not prevent expensive computation.
- **Change:** Added CROSS JOIN rejection using SQLGlot.
- **Verification:** Validator test passed — `CROSS JOINs are not allowed.`
- **Status:** Blocked before execution.

## 5. Limitations
- LIMIT does not guarantee low computational cost.
- Explicit CROSS JOINs are blocked, but other expensive query patterns may remain.
- Prompt instructions alone are not a security boundary.

### Recursive CTE Test
- **Test:** Attempted a recursive CTE designed to generate repeated rows.
- **Query:** `WITH RECURSIVE counter AS (SELECT 1 UNION ALL SELECT 1 FROM counter) SELECT * FROM counter`
- **Expected behavior:** Reject recursive CTEs.
- **Actual behavior:** Rejected by SQL validator.
- **Result:** PASS
- **Fix implemented:** Added recursive CTE detection using SQLGlot's `with_` AST node.

### Table Function Bypass Test
- **Test:** Attempted to access data through `query_table()`.
- **Query:** `SELECT query FROM query_table()`
- **Expected behavior:** Reject table functions.
- **Actual behavior:** Rejected with `Table functions are not allowed.`
- **Result:** PASS

### Nested Subquery Complexity Test

**Test:** Requested the total number of orders using deeply nested subqueries.

**Result:** The validator accepted the query and execution completed successfully.

**Rows/result:** 99,441 orders.

**Outcome:** Query executed successfully.

**Observation:** The validator does not currently enforce a maximum subquery nesting depth. Deeply nested queries could increase query complexity and execution cost. A nesting-depth restriction may be considered as an additional safeguard.

### Result Limit Enforcement

- **Test:** Execute a query returning a large number of rows.
- **Expected behavior:** The system enforces a maximum result limit of 500 rows.
- **Observed behavior:** The final SQL included `LIMIT 500`, and the output was capped at 500 rows.
- **Status:** PASS

This prevents the analyst application from returning excessively large result sets and helps control output size.

### Query Timeout Test

- **Test:** Execute a computationally expensive query using `range(1000000000)`.
- **Timeout configured:** 1 second.
- **Expected behavior:** Query should be interrupted if it exceeds the timeout.
- **Observed result:** `InterruptException: INTERRUPT Error: Interrupted!`
- **Status:** PASS

The timeout mechanism successfully interrupted the long-running query.

### Read-Only Database Test

- **Test:** Attempted to execute `DROP TABLE fact_orders` on `olist_serving.duckdb`.
- **Configuration:** Database connected with `read_only=True`.
- **Expected behavior:** Modification must be rejected.
- **Observed result:** DuckDB rejected the DROP statement because the database was attached in read-only mode.
- **Status:** PASS

The serving database successfully prevented a destructive SQL operation.

### External File Access Test

- **Test:** Attempted to read CSV and Parquet files directly using DuckDB table functions.
- **Configuration:** `enable_external_access=false`.
- **Expected behavior:** External file access should be blocked.
- **Observed result:** Both `read_csv_auto()` and `read_parquet()` were blocked with `PermissionException`.
- **Status:** PASS

DuckDB's execution-level external access restriction successfully blocked both attempts.