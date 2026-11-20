
# Project Key Numbers

This document is the single source of truth for headline metrics.
Use these definitions and values consistently across project documentation,
the README, dashboard and resume.

## 1. Dataset scale

| Metric | Value | Definition |
|---|---:|---|
| Total orders | 99,441 | Number of unique orders |
| Unique customers | 96,096 | Count of distinct customer_unique_id values |
| Delivered orders | 96,478 | Orders with delivered status |

## 2. Revenue and payments

| Metric | Value | Definition |
|---|---:|---|
| Delivered-order GMV | R$15,419,773.75 | Sum of item price and freight for delivered orders |
| Delivered item sales | R$13,221,498.11 | Sum of item prices for delivered orders |
| Total payment value | R$16,008,872.12 | Sum of cleaned payment values across all orders |

Note: Payment value and delivered-order GMV have different scopes.
Do not treat them as interchangeable.

## 3. Customer metrics

| Metric | Value | Definition |
|---|---:|---|
| Repeat customer rate | 3.12% | Customers with more than one order, regardless of order status |
| Repeat customer rate excluding canceled orders | 3.04% | Repeat rate calculated after excluding canceled orders |

## 4. Delivery performance

| Metric | Value | Definition |
|---|---:|---|
| Late delivery rate | 6.77% | Late delivered orders divided by delivered orders with valid delivery dates |

Delivery metrics must use valid delivered orders.
Exclude delivered orders with missing actual delivery dates from the late-rate denominator.

## 5. Customer satisfaction and delivery

| Metric | On-time / Early | Late |
|---|---:|---:|
| Low-rating share (1–2 stars) | 9.23% | 62.36% |
| Sample size | 89,443 | 6,381 |

- Absolute difference: 53.13 percentage points.
- 95% confidence interval for the difference: +51.91 to +54.32 percentage points.
- The association is observational; do not claim that late delivery alone caused low ratings.

## 6. Metric interpretation rules

- Currency is Brazilian reais (R$), not USD.
- GMV includes item price plus freight and counts delivered orders only.
- Payment total covers cleaned payment records across all order statuses.
- Repeat customer rate uses customer_unique_id, not customer_id.
- The standard repeat rate includes all order statuses.
- Late delivery rate uses delivered orders with valid delivery dates.
- Reviews belong to orders, not directly to customers.
- Aggregate order items, payments and reviews before joining them at order level to avoid fan-out double-counting.

## 7. Source documents

- docs/METRICS.md
- docs/FINDINGS.md
- docs/DATA_QUALITY.md
