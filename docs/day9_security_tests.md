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

### Validator-Bypassed Serving Database Security Test

**Objective:** Test serving database protections directly without calling the SQL validator.

| Test | Query | Expected | Actual | Protection layer |
|---|---|---|---|---|
| Raw table access | `SELECT * FROM raw_orders LIMIT 5` | Block | Blocked | Serving DB isolation — table absent |
| External CSV access | `read_csv_auto(...)` | Block | Blocked | External access disabled |
| Drop analytics table | `DROP TABLE fact_orders` | Block | Blocked | Read-only connection |
| Re-enable external access | `SET enable_external_access = true` | Block | Blocked | DuckDB runtime configuration restriction |

**Result:** 4/4 attempts blocked.

**Limitation:** Raw-table access was blocked because the raw table does not exist in the serving database. This test does not independently establish access-control behavior for raw tables that are present.

### Alternative Cartesian Join Tests

**Objective:** Check whether Cartesian products can bypass explicit CROSS JOIN protection using alternative SQL syntax.

| Test | Expected | Actual | Protection |
|---|---|---|---|
| Comma-separated tables | Block | Blocked | JOIN condition validation |
| `JOIN ... ON 1=1` | Block | Blocked | Constant-condition validation |
| `INNER JOIN ... ON TRUE` | Block | Blocked | Constant-condition validation |
| Legitimate column-based JOIN | Allow | Passed | Validator preserves valid joins |

**Result:** All four tests passed.

**Limitation:** Column-reference validation does not guarantee a selective join condition. Additional query-cost controls may still be necessary.

### Five-Second Query Timeout and Connection Recovery Test

**Objective:** Verify that the application's configured five-second timeout interrupts expensive SQL queries and that the same database connection remains usable afterward.

| Test | Expected | Actual |
|---|---|---|
| Expensive query | Interrupted after 5 seconds | Interrupted at 5.02 seconds |
| Timeout exception | InterruptException | InterruptException |
| Same connection recovery | Successful | Successful |
| Recovery query | Return 42 | Returned 42 |

**Result:** All checks passed.

**Conclusion:** The timeout mechanism successfully interrupted the expensive query, and the same connection successfully executed a subsequent query.

### DuckDB Memory Limit Test

**Objective:** Configure an explicit memory budget for AI-generated SQL queries.

| Check | Result |
|---|---|
| Default DuckDB memory limit | 12.5 GiB |
| Configured memory limit | 2 GB |
| Reported configured limit | 1.8 GiB |
| Configuration check | Passed |
| Memory-heavy query enforcement | Not yet tested |

**Limitation:** DuckDB's memory limit does not guarantee that total Python process memory stays below 2 GB. The configuration was verified, but out-of-memory behavior has not been tested.

### LIMIT Enforcement Tests

**Objective:** Verify that generated SQL cannot return more than 500 rows.

| Test | Expected | Actual |
|---|---|---|
| Query without LIMIT | Add LIMIT 500 | LIMIT 500 added |
| Query with LIMIT 10 | Preserve LIMIT 10 | LIMIT 10 preserved |
| Query with LIMIT 1000 | Reduce to LIMIT 500 | Reduced to LIMIT 500 |

**Result:** All 3 tests passed.

**Limitation:** LIMIT restricts returned rows but does not guarantee reduced query execution cost.

### Day 8 Regression Testing

**Objective:** Verify that the strengthened SQL guardrails do not reject legitimate business queries.

| Test | Result |
|---|---|
| Total GMV | Passed |
| Total orders | Passed |
| Monthly GMV trend | Passed |
| Top 10 categories | Passed |
| Repeat customer rate | Passed |

**Summary:**
- Total queries: 5
- Passed: 5
- Failed: 0
- Repeat customer rate returned: 3.12%

**Execution environment:** Isolated serving database, read-only connection, external access disabled, 2 GB memory limit, SQL validation, 500-row result limit and 5-second timeout.

**Limitation:** These tests verify successful validation and execution. Full business-result accuracy requires comparison against independently verified expected results.

### Complete 10-Query Regression Results

**Objective:** Verify that the strengthened SQL validator and execution protections continue to support legitimate business questions.

| Test | Business question | Result |
|---|---|---|
| Q1 | Total delivered GMV | R$15,419,773.75 |
| Q2 | Total orders | 99,441 |
| Q3 | Monthly GMV trend | 26 rows returned |
| Q4 | Top 10 categories | 10 rows returned |
| Q5 | Repeat customer rate | 3.12% |
| Q6 | Delivered orders count | 96,478 |
| Q7 | January 2018 GMV | R$1,077,887.46 |
| Q8 | Late vs on-time average rating | 2.27 vs 4.29 |
| Q9 | Category average price | 10 rows returned |
| Q10 | State-wise late-delivery rate | 27 states returned |

**Regression summary:**
- Total queries: 10
- Passed validation and execution: 10
- Failed: 0
- Success rate: 100%

**Reference checks:** The returned GMV, order count, repeat rate, delivered order count, January GMV and delivery-rating results match previously recorded project findings.

**Limitations:** Successful execution does not independently prove the correctness of every result. Q9 and Q10 rankings have not been independently reconciled against separate reference calculations.

### Result Truncation Notice Test

**Objective:** Inform users when the application returns the maximum permitted number of rows.

| Check | Expected | Actual |
|---|---|---|
| Maximum result rows | 500 | 500 |
| Truncation notice | Displayed | Displayed |
| SQL execution | Successful | Successful |
| Run logging | Recorded | Recorded |

**Result:** All checks passed.

**User-facing notice:** "Showing up to 500 rows. Results may be truncated. Refine your question to narrow the results."

**Limitation:** Reaching 500 rows does not prove additional rows exist. The notice correctly says results may be truncated.

### Gemini API Retry and Backoff Tests

**Objective:** Test handling of temporary and permanent Gemini API errors without consuming API quota.

| Test | Expected | Actual |
|---|---|---|
| Two consecutive 503 errors | Retry | Passed |
| Third attempt succeeds | Return response | Passed |
| Permanent 401 error | No retry | Passed |

**Configuration:**
- Primary model: `gemini-2.5-flash`
- Maximum attempts: 3
- Retryable status codes: 429, 500, 502, 503, 504
- Backoff: Exponential with jitter
- Request timeout: 20 seconds

**Result:** Both simulated tests passed. No live API calls were made.

**Limitation:** Actual live 429/503 recovery has not yet been verified.

### Gemini Fallback Model Tests

**Objective:** Verify that the application switches to a fallback model when the primary model exhausts its retry attempts.

| Test | Expected | Actual |
|---|---|---|
| Primary model returns 503 three times | Exhaust retries | Passed |
| Fallback model activated | Switch to Flash-Lite | Passed |
| Fallback response | Return response | Passed |
| Model tracking | Record actual model | Passed |

**Configuration:**
- Primary: `gemini-2.5-flash`
- Fallback: `gemini-3.5-flash-lite`
- Primary maximum attempts: 3
- Fallback attempts: 1

**Result:** All simulated fallback tests passed.

**Limitation:** Fallback activation was simulated. Live fallback behavior during a primary-model outage has not been tested.

### SQL Repair Loop Tests

**Objective:** Verify that invalid SQL can be corrected safely, with a maximum of two repair attempts.

| Test | Expected | Actual |
|---|---|---|
| Initially valid SQL | No repair needed | Passed |
| Invalid SQL followed by valid correction | Repair succeeds | Passed |
| Invalid SQL after two repairs | Reject query | Passed |

**Configuration:**
- Maximum repair attempts: 2
- Initial SQL generation: 1 attempt
- Maximum total SQL generations: 3

**Result:** All three simulated tests passed. No Gemini API calls were consumed.

**Limitation:** These tests cover validation-error repair. Execution-error repair has not been implemented.

### SQL Query Caching Tests

**Objective:** Reduce repeated Gemini API calls for identical business questions.

| Test | Expected | Actual |
|---|---|---|
| New question | Cache miss | Passed |
| Previously saved question | Cache hit | Passed |
| Different capitalization/whitespace | Same cache entry | Passed |
| Different model | Separate cache entry | Passed |
| Cached SQL validation | Revalidate before execution | Passed |


**Live application tests:**

- Question 1: How many orders are there in total?
- First run: CACHE HIT; previously generated SQL reused.
- Question 2: How many total orders do we have?
- First run for this wording: CACHE MISS; Gemini generated SQL.
- Both questions returned 99,441 orders.
- Cache hit: 0.046 seconds lookup, 0 seconds LLM generation.
- Cache miss: 0.071 seconds lookup, 1.5 seconds LLM generation.
- Both queries passed validation and execution.
- Both runs were recorded in `llm_runs.duckdb`.

**Result:** Cache integration and all four isolated cache tests passed.

**Limitation:** Cache entries currently have no expiry policy. Schema changes require updating the schema version.

- Semantically equivalent questions with different wording may generate separate cache entries. The current implementation does not support semantic similarity matching.



### Cache Persistence After Application Restart

**Objective:** Verify that cached SQL remains available after restarting the application.

**Test:** Restarted the application and submitted the exact same question again.

| Check | Expected | Actual |
|---|---|---|
| Cache status | CACHE HIT | CACHE HIT |
| LLM generation | 0 seconds | 0 seconds |
| SQL validation | Pass | Passed |
| SQL execution | SUCCESS | SUCCESS |
| Result | 99,441 orders | 99,441 orders |

**Cache lookup time:** 0.049 seconds.

**Result:** PASS

**Conclusion:** Cached SQL persisted in DuckDB after the application restarted. Gemini was not called again for the cached question.
