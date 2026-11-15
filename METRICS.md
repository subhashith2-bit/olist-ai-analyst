
# Business Metrics Documentation

## 1. Purpose

This document defines the business metrics used in the Olist AI Analyst Copilot project.

It explains how each metric is calculated, its business meaning, source tables, assumptions, and limitations.

The goal is to ensure that analytics results are consistent, reproducible, and interpretable.

All financial and operational metrics should follow the definitions documented here. This document acts as the project's metric dictionary and single source of truth.

## 2. Analytics Tables

| Table | Grain | Purpose |
|---|---|---|
| `fact_orders` | One row per order | Central order-level analytical table |
| `customer_metrics` | One row per unique customer | Customer purchase behaviour and lifetime value |
| `category_metrics` | One row per product category | Product category performance |
| `monthly_kpis` | One row per calendar month | Monthly business performance |

### 2.1 Analytics Layer Design

The project uses a simplified analytics layer built around one central order-level fact table and three aggregated analytical tables.

- `fact_orders` is the central order-level fact table.
- `customer_metrics` and `category_metrics` are aggregated analytical tables, not true dimension tables.
- `monthly_kpis` provides pre-aggregated monthly business metrics.

This design simplifies analytical queries and provides reusable datasets for reporting and analysis.

A full star schema for Power BI could be developed further by introducing `dim_customer`, `dim_product`, and `dim_date`.

## 3. Currency

All monetary values are expressed in Brazilian Real (R$).

The dataset represents Brazilian e-commerce transactions.

## 4. Financial Metrics

### 4.1 Gross Merchandise Value (GMV)

**Business meaning:** Total value of products and freight associated with successfully delivered orders.

**Formula:**

GMV = Item Price + Freight Value

**Implementation:**

- Only orders with `order_status = 'delivered'` contribute to GMV.
- Canceled, created, approved, unavailable, and other non-delivered statuses contribute zero.
- Orders without items are retained with `n_items = 0`, `items_value = 0`, `freight_value = 0`, and GMV = 0.
- Freight is included in GMV.
- GMV is calculated at order level.

**Source:** `fact_orders`

**Total Delivered-Order GMV:** R$15,419,773.75

### 4.2 Average Order Value (AOV)

**Business meaning:** Average GMV generated per delivered order.

**Formula:**

AOV = Delivered-Order GMV / Number of Delivered Orders

**Implementation:**

- At customer level: Customer Lifetime GMV / Customer Delivered-Order Count.
- At monthly level: Monthly Delivered-Order GMV / Monthly Delivered-Order Count.
- Only delivered orders are included in both the numerator and denominator.
- `NULLIF` is used to prevent division by zero.

**Source:** `customer_metrics`, `monthly_kpis`

### 4.3 Item Sales

**Business meaning:** Total value of products sold, excluding freight.

**Formula:**

Item Sales = SUM(Item Price)

**Implementation:**

- Canceled orders are excluded from category sales.
- Other non-canceled order statuses are included.
- Freight is reported separately.
- This is a different measure from delivered-order GMV.

**Source:** `category_metrics`

**Total Category Sales:** R$13,496,408.43

### 4.4 Payment Total

**Business meaning:** Total amount recorded across customer payment records.

**Formula:**

Payment Total = SUM(Payment Value)

**Source:** `fact_orders`, aggregated from `clean_order_payments`.

**Total Payment Value:** R$16,008,872.12

**Reconciliation:**

- Raw payment total: R$16,008,872.12
- Clean payment total: R$16,008,872.12
- Difference: R$0.00

Three zero-value `not_defined` payment records were removed during cleaning. Their removal did not change the payment total.

Note: Payment total, item sales, and GMV are different business measures. They represent different aspects of transactions and should not be expected to match.

### 4.5 Freight Share

**Business meaning:** Freight cost relative to item sales.

**Formula:**

Freight Share = Total Freight Value / Total Item Sales

**Source:** `category_metrics`

Note: This metric is calculated separately for each product category.

## 5. Customer Metrics

### 5.1 Total Customers

**Business meaning:** Number of distinct customers identified by `customer_unique_id`.

**Formula:**

COUNT(DISTINCT customer_unique_id)

**Source:** `customer_metrics`

**Total Customers:** 96,096

### 5.2 Repeat Customer Rate

**Business meaning:** Percentage of unique customers who placed more than one order.

**Formula:**

Repeat Rate = (Customers with 2+ Orders / Total Unique Customers) × 100

Two versions are calculated to show the effect of canceled orders.

| Definition | Repeat Rate |
|---|---:|
| All orders | 3.12% |
| Excluding canceled orders | 3.04% |
| Difference | 0.08 percentage points |

**Implementation:**

- `is_repeat` identifies customers with more than one order, including canceled orders.
- `is_repeat_non_canceled` identifies customers with more than one non-canceled order.
- Both rates use the total number of unique customers as the denominator.

The difference is small, but both definitions are retained for transparency.

**Source:** `customer_metrics`

### 5.3 Customer Lifetime GMV

**Business meaning:** Total delivered-order GMV generated by a customer across all their orders.

**Formula:**

Lifetime GMV = SUM(Customer Delivered-Order GMV)

**Implementation:**

- Only delivered orders contribute to lifetime GMV.
- Non-delivered orders contribute zero.

**Source:** `customer_metrics`

### 5.4 Customer Average Order Value

**Business meaning:** Average delivered-order GMV generated by an individual customer.

**Formula:**

Customer AOV = Customer Lifetime GMV / Customer Delivered-Order Count

**Implementation:**

- Only delivered orders are included in the denominator.
- Customers with zero delivered orders have a NULL AOV.

**Source:** `customer_metrics`

### 5.5 Days to Second Order

**Business meaning:** Number of calendar-day boundaries between a customer's first and second order timestamps.

**Formula:**

Days to Second Order = Second Order Date - First Order Date

**Implementation:**

- Calculated only for customers with at least two orders.
- Customers without a second order have NULL.
- `ROW_NUMBER()` identifies the first and second orders.
- `order_id` is used as a tie-breaker when purchase timestamps are identical.

**Source:** `customer_metrics`

## 6. Delivery Metrics

### 6.1 Late Delivery Rate

**Business meaning:** Percentage of delivered orders that arrived after their estimated delivery date.

**Formula:**

Late Rate = (Late Delivered Orders / Delivered Orders with Valid Delivery Dates) × 100

**Implementation:**

- Uses date-level comparison rather than exact timestamp comparison.
- Actual and estimated delivery timestamps are cast to DATE before comparison.
- A delivery is late only when the actual delivery date is later than the estimated delivery date.
- Same-day deliveries are not late, even if the actual delivery time is later than midnight.
- Only delivered orders with both actual and estimated delivery dates are included.
- Orders with missing delivery dates are excluded.

**Validated Results:**

| Measure | Value |
|---|---:|
| Delivered orders with valid dates | 96,470 |
| Late orders | 6,534 |
| Late delivery rate | 6.77% |

**Previous timestamp-based rate:** 8.11%

The earlier calculation compared full timestamps. Since estimated delivery timestamps are stored at midnight, same-day deliveries could incorrectly be classified as late.

The corrected date-level calculation avoids these false positives.

**Source:** `fact_orders`

### 6.2 Delivery Days

**Business meaning:** Calendar-day difference between purchase date and actual delivery date.

**Formula:**

Delivery Days = Actual Delivery Date - Purchase Date

**Implementation:**

- Calculated for delivered orders with valid delivery timestamps.
- Uses calendar-day difference rather than exact elapsed hours.

**Source:** `fact_orders`

### 6.3 Delivery Delay Days

**Business meaning:** Calendar-day difference between estimated and actual delivery dates.

**Formula:**

Delay Days = Actual Delivery Date - Estimated Delivery Date

**Implementation:**

- Positive values indicate late delivery.
- Negative values indicate early delivery.
- Zero indicates delivery on the estimated calendar date.
- Calculated only for delivered orders with valid actual and estimated delivery dates.

**Validation:**

- Late flag count: 6,534
- Positive delay count: 6,534
- Mismatches: 0

This confirms that `is_late` and `delay_days > 0` use consistent date-level logic.

**Source:** `fact_orders`

## 7. Monthly KPI Metrics

### 7.1 Monthly Orders

Total number of orders placed during a calendar month, including all order statuses.

**Source:** `monthly_kpis`

### 7.2 Monthly Delivered Orders

Number of delivered orders placed during a calendar month.

**Source:** `monthly_kpis`

### 7.3 Monthly GMV

Total delivered-order GMV generated during a calendar month.

**Formula:**

Monthly GMV = SUM(Delivered-Order GMV)

**Source:** `monthly_kpis`

### 7.4 Monthly AOV

Average GMV generated per delivered order during a calendar month.

**Formula:**

Monthly AOV = Monthly GMV / Monthly Delivered Orders

**Implementation:**

Both numerator and denominator use delivered orders only.

**Source:** `monthly_kpis`

### 7.5 New Customers

Number of distinct customers whose first recorded order occurred during that month.

**Implementation:**

- First order date is determined using the earliest order timestamp.
- The current implementation considers all order statuses.
- Therefore, a customer's first canceled order can determine their new-customer month.

**Source:** `monthly_kpis`, `customer_metrics`

### 7.6 Returning Customer Orders

Number of orders placed in a month by customers whose first recorded order occurred in an earlier month.

**
