# SQL Evaluation Set

This file contains business questions and verified SQL queries used to evaluate the AI analyst's SQL generation accuracy.

## 1. What is the total delivered GMV?

```sql
SELECT ROUND(SUM(gmv), 2) AS total_gmv
FROM fact_orders;
```

## 2. How many orders were placed?

```sql
SELECT COUNT(*) AS total_orders
FROM fact_orders;
```
## 3. What is the monthly delivered GMV trend?

```sql
SELECT
    month,
    gmv
FROM monthly_kpis
ORDER BY month;
```

## 4. Which 10 product categories generate the highest sales?

```sql
SELECT
    product_category_name,
    sales
FROM category_metrics
ORDER BY sales DESC
LIMIT 10;
```

## 5. What percentage of customers are repeat customers?

```sql
SELECT
    ROUND(
        COUNT(*) FILTER (WHERE is_repeat = TRUE) * 100.0
        / COUNT(*),
        2
    ) AS repeat_customer_rate
FROM customer_metrics;
```
