# Day 8 — SQL Validator Security Tests

## Objective
Test whether the SQL validator blocks indirect access to unauthorized tables, external files, and DuckDB system tables.

## Results

| Test | Attempt | Result |
|---|---|---|
| CTE bypass | Access `raw_orders` through a CTE | Blocked |
| Subquery bypass | Access `raw_orders` through a subquery | Blocked |
| File access | Access `read_csv_auto()` | Blocked |
| System tables | Access `duckdb_tables()` | Blocked |

## Outcome
All four tested bypass attempts were rejected by the SQL validator.

## Limitation
These tests cover specific attack attempts only. They do not prove that the validator is secure against all possible SQL bypass techniques. Additional hardening is planned.
