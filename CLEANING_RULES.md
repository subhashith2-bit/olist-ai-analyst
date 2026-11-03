# Data Cleaning Rules

## Purpose

This document records the cleaning decisions applied to the Olist raw data before creating the `clean_*` tables.

The `raw_*` tables are never modified. Cleaning creates separate `clean_*` tables so the original data remains available for auditing and reproducibility.

---

## 1. Orders with no order items

**Issue:** 775 orders have no corresponding rows in `raw_order_items`.

**Observed statuses:** unavailable, canceled, created, invoiced, and shipped.

**Rule:** Keep all 775 orders in `clean_orders`.

**Business reason:** A missing item record does not automatically make the order record invalid. Removing these orders would lose potentially useful order-level information.

**Impact:** 775 affected orders; 0 orders removed.

---

## 2. Delivered orders with missing delivery date

**Issue:** 8 delivered orders have a missing actual delivery date.

**Rule:** Keep these orders in `clean_orders`.

**Business reason:** The order itself can still be valid. These records should simply be excluded when calculating metrics that require an actual delivery date, such as delivery duration and late-delivery rate.

**Impact:** 8 affected orders; 0 orders removed.

---

## 3. Multiple reviews per order

**Issue:** 547 orders have more than one review row, and 789 `review_id` values are repeated.

**Rule:** Keep all review records.

**Business reason:** There were 0 exact duplicate rows, so repeated review records were not automatically treated as invalid. Deleting them without further evidence could remove legitimate information.

**Impact:** 547 affected orders / 789 repeated review IDs; 0 rows removed.

---

## 4. Zero-value `not_defined` payments

**Issue:** 9 zero-value payments were identified:
- 6 with payment type `voucher`
- 3 with payment type `not_defined`

**Rule:** Remove only rows where:
- `payment_value = 0`
- `payment_type = 'not_defined'`

**Business reason:** These 3 records represent undefined zero-value payment records and are not useful as valid payment transactions.

**Impact:** 3 rows removed.

**Validation:** After cleaning, 0 zero-value `not_defined` payment records remain.

---

## 5. Missing product categories

**Issue:** 610 products have a missing `product_category_name`.

**Rule:** Replace NULL category values with `unknown`.

**Business reason:** The product records themselves remain useful. Replacing the missing category with `unknown` preserves the products while allowing category-level analysis without dropping records.

**Impact:** 610 product records affected; 0 products removed.

**Validation:** `clean_products` contains 610 records with category `unknown`.

---

## 6. Multiple geolocation records per ZIP prefix

**Issue:** 17,972 ZIP prefixes have multiple geolocation records.

**Rule:** Keep all geolocation records.

**Business reason:** Multiple geographic coordinates can legitimately exist within the same ZIP prefix. Deduplicating based only on ZIP prefix could incorrectly remove valid geographic information.

**Impact:** 17,972 ZIP prefixes affected; 0 rows removed.

---

## Summary

Only one rule removes rows:

- 3 invalid `not_defined` zero-value payment records removed.

All other cleaning decisions preserve the original records and handle data-quality issues without unnecessary deletion.

The `raw_*` tables remain unchanged, while cleaned data is stored in corresponding `clean_*` tables.
