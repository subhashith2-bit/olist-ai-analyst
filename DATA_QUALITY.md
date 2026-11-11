# Data Quality Checks

## 1. Purpose

This document describes the automated data quality checks implemented for the Olist dataset.

The checks validate data integrity, consistency, referential integrity, and reconciliation between raw and cleaned tables.

## 2. Execution

Run the checks from the project root:

```bash
python src/checks.py
```

The script saves the latest results in the DuckDB table `dq_results`.

## 3. Severity levels

| Severity | Meaning |
|---|---|
| ERROR | Serious data quality issue. Causes the script to fail. |
| WARN | Anomaly requiring investigation. Does not stop execution. |

## 4. Check categories

The automated suite currently contains 41 checks:

| Category | Checks |
|---|---:|
| Orders and order dates | 6 |
| Order items | 7 |
| Payments | 5 |
| Reviews | 5 |
| Products | 6 |
| Customers and sellers | 6 |
| Raw-to-clean reconciliation | 5 |
| Payment-total reconciliation | 1 |
| **Total** | **41** |

## 5. Known warnings

Two checks currently produce warnings:

- **166 carrier dates before purchase dates:** These records have inconsistent delivery timelines and require investigation.
- **8 delivered orders with missing actual delivery dates:** These records cannot be used in calculations requiring actual delivery dates.

These records are retained rather than deleted. Analyses that depend on valid delivery timelines should handle these anomalies explicitly.

## 6. Cleaning reconciliation

The cleaning pipeline intentionally removes three zero-value payments with payment type `not_defined`.

- Raw payment rows: 103,886
- Clean payment rows: 103,883
- Rows removed: 3
- Payment amount removed: R$0.00

The raw and clean payment totals reconcile to approximately R$16,008,872.12.

## 7. Latest validation result

| Result | Count |
|---|---:|
| Total checks | 41 |
| PASS | 39 |
| WARN | 2 |
| FAIL | 0 |

**Overall status: PASSED**

## 8. Important considerations

- Raw tables are preserved and never modified by the cleaning pipeline.
- Checks run against cleaned tables unless reconciliation requires raw tables.
- Warnings are not automatically treated as invalid data.
- The `dq_results` table stores the latest validation run, not historical runs.
- Data quality checks validate known rules; they do not guarantee that every business assumption is correct.