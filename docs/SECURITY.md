# Security Architecture & Testing

## 1. Overview

The AI Analyst Copilot uses an LLM to generate DuckDB SQL from natural-language business questions.

Allowing an LLM to execute SQL introduces risks such as unauthorized data access, destructive queries, external file access, expensive queries and prompt injection.

The project implements multiple protection layers to reduce these risks.

**Security disclaimer:** These guardrails reduce risk and have been tested, but they are not a security certification or a guarantee of complete protection.

## 2. Security Architecture

| Layer | Implementation | Purpose |
|---|---|---|
| SQL parsing | SQLGlot | Parses generated SQL into an AST |
| Query validation | `validate_sql()` | Allows only approved SELECT-based queries |
| Table restrictions | `ALLOWED_TABLES` | Restricts access to approved analytics tables |
| Function restrictions | `BLOCKED_FUNCTIONS` | Blocks selected risky functions and table functions |
| Join protection | Join-condition validation | Rejects explicit CROSS JOINs, comma joins and constant join conditions |
| Recursive CTE protection | SQLGlot AST inspection | Rejects recursive CTEs |
| Serving database isolation | `olist_serving.duckdb` | Separates approved analytics data from raw tables |
| Read-only access | `read_only=True` | Prevents database modifications |
| External access restriction | `enable_external_access=false` | Blocks external file access |
| Memory limit | `memory_limit=2GB` | Sets a DuckDB memory budget |
| Result limit | `enforce_limit()` | Restricts returned rows to a maximum of 500 |
| Execution timeout | `execute_with_timeout()` | Interrupts queries after 5 seconds |
| Execution logging | `llm_runs.duckdb` | Records questions, SQL, validation, execution status, errors and timings |

## 3. Security Test Evidence

### SQL Validator Tests

| Test | Result |
|---|---|
| Unauthorized raw-table access | Blocked |
| Quoted raw-table access | Blocked |
| Schema-qualified table access | Blocked |
| CTE bypass | Blocked |
| Subquery bypass | Blocked |
| UNION with unauthorized table | Blocked |
| External file functions | Blocked |
| System table access | Blocked |
| Multiple SQL statements | Blocked |
| Non-SELECT statements | Blocked |
| Recursive CTE | Blocked |
| Table-function access | Blocked |
| Prompt injection attempt | Safely rejected |

### Alternative Cartesian Join Tests

| Test | Result |
|---|---|
| Explicit CROSS JOIN | Blocked |
| Comma-separated join | Blocked |
| JOIN with ON 1=1 | Blocked |
| INNER JOIN with ON TRUE | Blocked |
| Legitimate column-based JOIN | Passed |

### Serving Database Tests

Four direct database attempts were tested without calling the SQL validator.

| Test | Result | Protection |
|---|---|---|
| Access raw_orders | Blocked | Raw table absent from serving DB |
| Read external CSV | Blocked | External access disabled |
| DROP fact_orders | Blocked | Read-only connection |
| Re-enable external access | Blocked | DuckDB runtime configuration restriction |

### Execution Protection Tests

| Test | Actual result |
|---|---|
| Five-second query timeout | Interrupted at 5.02 seconds |
| Connection recovery after timeout | Successful |
| Recovery query | Returned 42 |
| No LIMIT supplied | LIMIT 500 added |
| Existing LIMIT 10 | Preserved |
| Existing LIMIT 1000 | Reduced to 500 |
| Truncation notice | Displayed |
| Memory configuration | 2 GB configured; DuckDB reported 1.8 GiB |

### Business Query Regression

Ten legitimate business queries were tested after validator hardening.

| Metric | Result |
|---|---:|
| Total queries | 10 |
| Passed validation and execution | 10 |
| Failed | 0 |
| Success rate | 100% |

Key results matched previously recorded project findings:

- Delivered GMV: R$15,419,773.75
- Total orders: 99,441
- Delivered orders: 96,478
- Repeat customer rate: 3.12%
- January 2018 GMV: R$1,077,887.46
- Late delivery average rating: 2.27
- On-time delivery average rating: 4.29

## 4. Known Limitations

1. SQL validation is not a complete security boundary. New SQL syntax and attack patterns may expose bypasses.
2. Raw-table access was blocked because raw tables are absent from the serving database; this does not prove access-control behavior for raw tables if they are present.
3. Join validation rejects constant conditions and joins without explicit conditions, but column references do not guarantee selective or inexpensive joins.
4. Nested subquery depth is not restricted. A four-level nested query was successfully executed.
5. LIMIT restricts returned rows, not necessarily the computational cost of a query.
6. DuckDB's memory limit does not cap total Python process memory. Actual memory-exhaustion behavior has not been tested.
7. The five-second timeout was tested with an expensive query and connection recovery, but it does not protect LLM API response time.
8. The truncation notice indicates that results may be truncated; exactly 500 rows does not prove additional rows exist.

## 5. Additional Reliability Features

The application also records execution information in `llm_runs.duckdb`, including:

- User question
- Model name
- Generated SQL
- Validation status and message
- Final SQL
- Execution status and errors
- LLM and SQL execution times
- Number of rows returned

The application currently uses `gemini-2.5-flash`, following repeated 503 errors with the previous model.

## 6. Features Not Yet Verified or Implemented

The following features are not confirmed as implemented in the current project:

- Retry with exponential backoff and jitter for 429/503 errors
- Fallback model
- SQL repair loop with a maximum of two attempts
- Query result caching
- Cache-key strategy
- Fake-LLM automated tests
- Explicit nested-subquery depth limit
- Comprehensive memory-exhaustion testing

These should be treated as future improvements, not existing capabilities.

## 7. Test Documentation

Detailed test evidence is maintained separately:

- `docs/day8_manual_check.md`
- `docs/day8_security_tests.md`
- `docs/day9_security_tests.md`

The ten-query regression suite is maintained in:

- `src/evaluate_sql.py`

---

**Conclusion:** The AI Analyst Copilot uses layered SQL validation, database isolation, read-only access, external access restrictions, memory configuration, result limits and execution timeouts. These protections were tested against specific attack patterns and legitimate business queries. Further hardening and broader security testing are required before production use.