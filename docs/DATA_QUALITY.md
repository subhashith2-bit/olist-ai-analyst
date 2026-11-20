# Data Quality Checks — Olist Project

## 1. Purpose

This document describes the automated data quality checks implemented for the Olist Brazilian e-commerce dataset.

The checks validate data integrity, completeness, consistency, referential integrity and reconciliation between raw and cleaned tables.

## 2. Severity vs. Status

**Severity** describes the importance of a check's rule. **Status** describes the result of executing that check.

- An ERROR-severity check that finds violations produces FAIL and causes the script to exit with code 1.
- A WARN-severity check that finds violations produces WARN and allows the script to exit with code 0.
- A check with zero violations produces PASS, regardless of severity.

| Severity | Meaning |
|---|---|
| ERROR | Serious issue that should stop the pipeline. |
| WARN | Anomaly requiring investigation but does not stop execution. |

| Status | Meaning |
|---|---|
| PASS | No violations found. |
| WARN | Violations found in a WARN-severity check. |
| FAIL | Violations found in an ERROR-severity check. |

## 3. Execution

Run the checks from the project root:

```bash
python src/checks.py
```

The script saves the latest results in the DuckDB table `dq_results`.

## 4. Data Quality Concepts

| Term | Meaning | Olist example |
|---|---|---|
| Data Quality | How reliable, accurate, complete and consistent data is. | Checking whether order IDs and timestamps are valid. |
| Data Profiling | Examining data to understand its structure, distributions, missing values and anomalies. | Inspecting order statuses and NULL delivery dates before cleaning. |
| Data Validation | Testing data against predefined rules. | Checking whether review scores are between 1 and 5. |
| Completeness | Whether required data values are present. | Checking for NULL `order_id` values. |
| Validity | Whether values follow an accepted format, range or rule. | Review scores must be between 1 and 5. |
| Consistency | Whether related values agree logically. | Delivery should not occur before purchase. |
| Uniqueness | Whether identifiers or key combinations uniquely identify records. | Checking for duplicate `product_id` values. |
| Accuracy | How closely data represents a real-world event or value. | Whether a recorded delivery date reflects actual delivery. Automated checks alone cannot fully establish this. |
| Anomaly | A value or pattern that differs from expected behaviour. | A carrier handoff timestamp before purchase. |
| Business Rule | A condition data must satisfy based on business logic. | A review score must be between 1 and 5. |
| Threshold | A defined boundary used to decide whether a result is acceptable. | Our review-score check uses the allowed range of 1–5. We have not introduced arbitrary percentage thresholds for missing values. |

## 5. Validation and Integrity Terms

| Term | Meaning | Olist example |
|---|---|---|
| NULL Check | Identifies missing values. | Checking whether `customer_unique_id` is NULL. |
| Range Check | Verifies that a numeric value falls within an allowed range. | `review_score` must be from 1 to 5. |
| Primary Key | A column or combination of columns that uniquely identifies a row. | `order_id` identifies an order in `clean_orders`, after uniqueness is verified. |
| Composite Key | A key formed using multiple columns together. | `order_id` + `order_item_id` identifies an order-item row. |
| Foreign Key Relationship | A relationship where one table references another table's identifier. | `clean_order_items.order_id` references `clean_orders.order_id`. |
| Referential Integrity | Ensures references between related tables point to existing records. | Every order item should have a matching order. |
| Orphan Record | A record that references a parent record that does not exist. | An order item whose `order_id` is missing from `clean_orders`. |
| Duplicate Group | A value or key combination appearing more than once. | Multiple rows with the same `order_id` and `order_item_id`. |

**DuckDB note:** Tables loaded from CSV do not automatically have declared primary-key, foreign-key or other constraints. Our `DESCRIBE` output showed `key = NULL`. Therefore, we implement uniqueness and referential-integrity checks ourselves.

## 6. Reconciliation and Financial Terms

| Term | Meaning | Olist example |
|---|---|---|
| Reconciliation | Comparing two datasets to confirm that they agree. | Comparing raw and clean payment totals. |
| Row-count Reconciliation | Checking whether record counts changed as expected. | Raw payments: 103,886;