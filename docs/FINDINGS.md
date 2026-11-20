# Day 6 — Statistical Analysis and Business Findings

**Project:** Olist AI Analyst Copilot  
**Dataset:** Brazilian E-commerce Public Dataset by Olist  
**Analysis period:** September 2016 – October 2018  
**Currency:** Brazilian Real (R$)  
**Tools:** Python, DuckDB, pandas, SciPy, statsmodels, Matplotlib

---

# Executive Summary

This analysis investigates three business questions using Olist's historical order, customer, delivery and review data.

1. Does late delivery have an association with lower customer satisfaction?
2. Which first-order customer experiences are associated with repeat purchasing?
3. How does delivery performance vary across Brazilian states?

Statistical methods include Welch's t-test, Mann–Whitney U, logistic regression, two-proportion z-tests, confidence intervals, Kruskal–Wallis and chi-square tests.

Holm multiple-comparison correction was applied across six hypothesis tests in the first-order repeat-purchase analysis.

## Key Findings

| Finding | Key result | Statistical evidence |
|---|---|---|
| Late delivery and customer satisfaction | Low-rating share: 62.36% for late orders vs 9.23% for on-time/early orders | Difference: +53.13 percentage points; 95% CI: +51.91 to +54.32 pp |
| First-order experience and repeat purchase | Repeat rate: 2.87% after late first delivery vs 3.86% after on-time/early first delivery | Difference: −0.982 pp; Holm-adjusted p = 0.002333 |
| State delivery performance | Delivery-time distributions and late-delivery proportions differ across states | Kruskal–Wallis ε² = 0.2492; Cramér's V = 0.1361 |

**Overall business implication:** Delivery reliability is an important customer-experience metric. The analysis identifies opportunities to investigate late deliveries, monitor first-order customer experiences and improve state-level logistics performance.

All findings are observational. Statistical associations do not establish causation.

---

# 1. Late Delivery and Customer Satisfaction

## 1.1 Business Question

Does late delivery have an association with lower customer review scores?

The objective is to understand whether customers who receive orders later than their estimated delivery dates report lower satisfaction.

## 1.2 Population and Filters

The analysis includes delivered orders with valid actual delivery dates, valid estimated delivery dates and available customer review scores.

| Population | Orders |
|---|---:|
| Delivered orders | 96,478 |
| Delivered orders with valid delivery dates | 96,470 |
| Valid delivered orders with reviews | 95,824 |
| Valid delivered orders without reviews | 646 |

Final review analysis population:

| Delivery group | Orders |
|---|---:|
| Late | 6,381 |
| On-time or early | 89,443 |
| **Total** | **95,824** |

### Review-response limitation

The missing-review rate differs between delivery groups:

- Late deliveries: 2.34%.
- On-time/early deliveries: 0.55%.

The missing-review rate is higher for late orders, creating some potential response bias. Both rates are relatively low in absolute terms, but the difference should be considered when interpreting the results.

## 1.3 Descriptive Analysis

| Metric | On-time / Early | Late |
|---|---:|---:|
| Orders | 89,443 | 6,381 |
| Mean review score | 4.29 | 2.27 |
| Median review score | 5 | 1 |
| Low-rating share (1–2 stars) | 9.23% | 62.36% |
| One-star review share | 6.58% | 53.69% |

The low-rating share is approximately 53.13 percentage points higher for late deliveries.

### Delivery Delay and Review Score Pattern

A dose-response pattern was observed: longer delivery delays were associated with progressively lower customer ratings.

| Delivery status | Orders | Mean review score | Low-rating share | One-star share |
|---|---:|---:|---:|---:|
| On-time / early | 89,443 | 4.29 | 9.23% | 6.58% |
| 1–3 days late | 1,852 | 3.29 | 32.18% | 25.11% |
| 4–7 days late | 1,748 | 2.11 | 67.56% | 58.47% |
| 8+ days late | 2,781 | 1.70 | 79.14% | 69.72% |

Longer delays correspond to substantially higher shares of low and one-star reviews.

## 1.4 Statistical Methods and Results

### Welch's t-test

**Purpose:** Compare average review scores between late and on-time/early deliveries without assuming equal group variances.

| Statistic | Result |
|---|---:|
| Mean difference (late − on-time) | −2.0188 |
| t-statistic | −100.7444 |
| p-value | <0.001 |
| 95% confidence interval | −2.0580 to −1.9795 |

The mean review score for late deliveries is approximately 1.98–2.06 points lower.

### Mann–Whitney U Test

**Purpose:** Compare the rank distributions of review scores. This provides a complementary test because review scores are ordinal and concentrated at particular values.

| Statistic | Result |
|---|---:|
| Mann–Whitney U | 103,308,952.5 |
| p-value | <0.001 |
| Rank-biserial correlation | −0.638 |

The negative rank-biserial correlation indicates that the late-delivery group tends to have lower review scores. Its magnitude indicates a strong difference between the two groups.

### Difference in Low-Rating Proportions

| Metric | Result |
|---|---:|
| Late low-rating share | 62.36% |
| On-time/early low-rating share | 9.23% |
| Risk difference | +53.13 percentage points |
| 95% confidence interval | +51.91 to +54.32 percentage points |

The difference is statistically significant and substantial in practical terms.

### Logistic Regression

A logistic regression model examined the association between late delivery and low customer ratings while controlling for:

- Customer state.
- Log-transformed order GMV.
- Freight share of order GMV.

Dependent variable:

- 1 = Low review (score ≤ 2).
- 0 = Review score above 2.

HC3 robust standard errors were used.

| Metric | Result |
|---|---:|
| Observations | 95,824 |
| Adjusted odds ratio for late delivery | 16.0331 |
| 95% confidence interval | 15.1430–16.9754 |
| p-value | <0.001 |

After adjustment, late deliveries were associated with approximately 16 times the odds of receiving a low review compared with on-time/early deliveries.

**Interpretation caution:** An odds ratio of 16 does not mean that the probability of a low review is 16 times higher. Odds and probabilities are different measures.

### Additional Robustness Check — Product Category Adjustment

A supplementary logistic regression assessed whether the late-delivery association was explained by differences in product-category mix.

Each order was assigned one dominant category: the category with the highest total item price in that order. Categories with fewer than 100 observations were grouped into `Other`.

The category-adjusted model controlled for customer state, log-transformed order GMV, freight share and grouped dominant product category.

| Metric | Category-adjusted model |
|---|---:|
| Observations | 95,824 |
| Estimated parameters | 82 |
| Converged | Yes |
| Pseudo R-squared | 0.1488 |
| Adjusted odds ratio for late delivery | 16.199 |
| 95% confidence interval | 15.287–17.164 |
| p-value | <0.001 |

The odds ratio changed only slightly from 16.033 in the original model to 16.199 after adding dominant product category.

This suggests that the observed association is not explained by dominant product-category mix alone.

The model remains observational and does not control for seller, carrier, delivery distance or all product-level characteristics.

## 1.5 Business Recommendations

Prioritize delivery reliability improvements, especially for orders delayed by four or more days.

Recommended actions:

1. Identify carriers and sellers associated with repeated delivery delays.
2. Monitor orders approaching or exceeding their estimated delivery dates.
3. Introduce proactive customer communication when delays occur.
4. Investigate long-delay orders separately, especially those delayed by eight or more days.
5. Monitor low-rating and one-star review shares as customer-experience indicators.

A useful operational dashboard should track delivery-delay categories alongside customer review scores.

## 1.6 Limitations

- Review data is not available for every eligible delivered order.
- Late orders have a higher missing-review rate, which may introduce response bias.
- The original logistic regression controls for state, log GMV and freight share. A supplementary model also controls for dominant product category.
- Neither model controls for every possible confounder, including seller, carrier, delivery distance, product weight or order complexity.
- The analysis is observational and cannot establish that late delivery alone causes lower review scores.
- Statistical significance does not necessarily indicate the exact financial impact of delivery delays.

---

# 2. First-Order Customer Experience and Repeat Purchase

## 2.1 Business Question

Which first-order customer experiences are associated with repeat purchasing?

Three factors were investigated:

1. First-order delivery status.
2. First-order review rating.
3. First-order GMV.

## 2.2 Population and Follow-up Restriction

Customers with insufficient observation time may appear not to have repeated simply because the dataset ended before they had an opportunity to purchase again.

To reduce this right-censoring problem, the analysis was restricted to customers whose first order occurred at least six months before the end of the observation window.

Six-month eligibility cutoff:

**17 April 2018, 17:30:18**

| Population | Customers |
|---|---:|
| Customers with at least six months of follow-up | 68,169 |
| First orders delivered with valid delivery status | 65,841 |
| Delivered first orders with available review scores | 65,353 |

Repeat purchase was defined using `customer_metrics.is_repeat`, where a customer is classified as a repeat customer if they have more than one order in the dataset.

## 2.3 Comparison 1 — First-Order Delivery Status

### Descriptive Results

| First-order delivery status | Customers | Repeat customers | Repeat rate |
|---|---:|---:|---:|
| On-time / early | 60,691 | 2,340 | 3.86% |
| Late | 5,150 | 148 | 2.87% |

Customers whose first order arrived late had a lower observed repeat-purchase rate.

### Statistical Test

A two-proportion z-test compared repeat-purchase rates. Newcombe's method was used to calculate the 95% confidence interval for the difference in proportions.

| Metric | Result |
|---|---:|
| Late first-order repeat rate | 2.87% |
| On-time/early first-order repeat rate | 3.86% |
| Risk difference (late − on-time) | −0.982 percentage points |
| 95% confidence interval | −1.432 to −0.467 percentage points |
| Z-statistic | −3.5476 |
| Original p-value | 0.000389 |
| Holm-adjusted p-value | 0.002333 |

The confidence interval does not include zero, and the Holm-adjusted p-value remains below 0.05.

The late first-order group had approximately 25.46% lower relative repeat-purchase rate than the on-time/early group.

**Interpretation:** Late first delivery is associated with a lower repeat-purchase rate, although the absolute difference is approximately one percentage point.

## 2.4 Comparison 2 — First-Order Review Rating

Customers with delivered first orders and available review scores were grouped into three rating categories.

Half-star values in the dataset were retained.

Groups:

- Low rating: 1.0–2.5 stars.
- Middle rating: 3.0–3.5 stars.
- High rating: 4.0–5.0 stars.

### Descriptive Results

| First-order rating | Customers | Repeat customers | Repeat rate |
|---|---:|---:|---:|
| 1–2.5 stars | 9,093 | 312 | 3.43% |
| 3–3.5 stars | 5,717 | 210 | 3.67% |
| 4–5 stars | 50,543 | 1,947 | 3.85% |
| **Total** | **65,353** | **2,469** | |

The observed repeat-purchase rate increases slightly across the rating groups.

### Statistical Test

The low-rating group (1–2.5 stars) was compared with the high-rating group (4–5 stars) using a two-proportion z-test.

| Metric | Result |
|---|---:|
| Low-rating repeat rate | 3.43% |
| High-rating repeat rate | 3.85% |
| Risk difference (low − high) | −0.421 percentage points |
| 95% confidence interval | −0.815 to +0.006 percentage points |
| Z-statistic | −1.9357 |
| Original p-value | 0.052900 |
| Holm-adjusted p-value | 0.148093 |

The confidence interval includes zero, and the adjusted p-value is above 0.05.

**Interpretation:** There is insufficient statistical evidence at the 5% significance level to conclude that repeat-purchase rates differ between the low- and high-rating groups.

This does not prove that customer satisfaction has no relationship with repeat purchasing.

## 2.5 Comparison 3 — First-Order GMV

Customers were divided into three spending groups using the 33rd and 67th percentiles of first-order GMV.

Observed cutoffs:

- 33rd percentile: approximately R$69.61.
- 67th percentile: approximately R$143.03.

### Descriptive Results

| First-order GMV group | Customers | Repeat customers | Repeat rate |
|---|---:|---:|---:|
| Low GMV | 22,724 | 903 | 3.97% |
| Medium GMV | 22,722 | 886 | 3.90% |
| High GMV | 22,723 | 805 | 3.54% |

### Statistical Test

A chi-square test compared repeat-purchase status across all three GMV groups. Pairwise two-proportion z-tests were also examined.

| Overall test metric | Result |
|---|---:|
| Chi-square statistic | 6.5924 |
| Degrees of freedom | 2 |
| Raw p-value | 0.037023 |
| Cramér's V | Approximately 0.0098 |

The overall test is statistically significant before correction, but Cramér's V indicates an extremely small association.

Pairwise comparisons:

| Comparison | Risk difference | Raw p-value | Holm-adjusted p-value |
|---|---:|---:|---:|
| Low vs Medium GMV | +0.074 pp | 0.683144 | 0.683144 |
| Low vs High GMV | +0.431 pp | 0.015683 | 0.078416 |
| Medium vs High GMV | +0.357 pp | 0.044602 | 0.148093 |

After Holm correction across the full six-test family, none of the GMV comparisons is statistically significant at the 5% level.

**Interpretation:** The low-GMV group had a slightly higher observed repeat-purchase rate than the high-GMV group, but this difference does not remain statistically significant after correction. The effect size is also very small.

This does not demonstrate that lower first-order spending causes greater customer loyalty.

## 2.6 Multiple-Comparison Correction

Holm's correction was applied across six reported hypothesis tests to control the family-wise error rate.

The family includes:

- First-order delivery status comparison.
- First-order review rating comparison.
- Overall three-group GMV test.
- All three GMV pairwise comparisons.

| Comparison | Original p-value | Holm-adjusted p-value | Significant at 5%? |
|---|---:|---:|---|
| First-order delivery status vs repeat purchase | 0.000389 | 0.002333 | Yes |
| First-order rating vs repeat purchase | 0.052900 | 0.148093 | No |
| Overall GMV groups | 0.037023 | 0.148093 | No |
| Low vs Medium GMV | 0.683144 | 0.683144 | No |
| Low vs High GMV | 0.015683 | 0.078416 | No |
| Medium vs High GMV | 0.044602 | 0.148093 | No |

Only the first-order delivery-status comparison remains statistically significant at the 5% level after this six-test correction.

The rating and GMV comparisons are statistically inconclusive under this correction; this is not proof that no relationship exists.

## 2.7 Robustness Check — Uniform 180-Day Repeat-Purchase Window

The six-month eligibility analysis uses `customer_metrics.is_repeat`, which identifies customers with more than one order over the available dataset.

Although the cutoff ensures a minimum observation period, customers still have different amounts of follow-up time.

As a robustness check, repeat purchase was recalculated using the same 180-day window after each eligible customer's first order. Only first orders with at least 180 days remaining before the end of the dataset were included.

### Actual Results from Updated Script

| First-order delivery status | Eligible customers | Repeat within 180 days | Repeat rate |
|---|---:|---:|---:|
| On-time / early | 61,412 | 1,687 | 2.75% |
| Late | 5,178 | 121 | 2.34% |

The late-minus-on-time risk difference was approximately −0.41 percentage points.

| Metric | Result |
|---|---:|
| Risk difference | −0.41 percentage points |
| 95% confidence interval | −0.81 to +0.055 percentage points |
| Two-proportion z-test p-value | 0.081127 |

The direction is consistent with the original six-month eligibility analysis, but the difference is smaller and is not statistically significant at the 5% level.

This indicates that the strength of the repeat-purchase finding depends partly on how follow-up time and repeat purchase are defined. The result should be interpreted cautiously.

## 2.8 Business Recommendations

First-order delivery experience is a useful early indicator of potential retention risk.

Recommended actions:

1. Monitor first-time customers whose first delivery is late.
2. Consider proactive customer communication and service recovery for delayed first orders.
3. Track repeat-purchase rates by first-order delivery experience.
4. Evaluate retention interventions through controlled experiments before claiming that they improve repeat purchasing.
5. Avoid using first-order GMV alone as a customer-loyalty indicator.

The observed GMV difference is small in absolute terms and should not be treated as a reason to prioritize low-spending customers without additional business analysis.

## 2.9 Limitations

- The six-month follow-up restriction reduces unequal observation time but does not eliminate all censoring or observation-window effects.
- Repeat purchase is measured using all order statuses, not only completed purchases.
- First-order delivery, rating and GMV are observational customer characteristics.
- The rating comparison excludes customers without a first-order review.
- The rating comparison uses the actual half-star values present in the dataset.
- The analysis does not control for every potential factor influencing repeat purchasing, such as customer acquisition channel, product category, seller, promotions or customer preferences.
- Statistical significance does not establish causation or guarantee meaningful financial impact.

---

# 3. State-Level Delivery Performance

## 3.1 Business Question

How does delivery performance vary across Brazilian states?

The objective is to identify states with higher late-delivery rates, understand delivery-time differences and evaluate whether estimated delivery dates provide different amounts of time across states.

## 3.2 Population and Filters

The state-level analysis includes delivered orders with:

- Valid actual delivery duration.
- Valid late-delivery status.
- Available customer state.

The analysis includes 27 Brazilian states.

For the Wilson confidence intervals and estimated-date analysis, delivered orders with valid actual and estimated delivery dates were used.

Late-delivery definition:

An order is late when its actual delivery date is later than its estimated delivery date.

## 3.3 Descriptive Results

The five states with the highest observed late-delivery rates were:

| State | Delivered orders | Late orders | Late rate |
|---|---:|---:|---:|
| AL | 397 | 85 | 21.41% |
| MA | 717 | 125 | 17.43% |
| SE | 335 | 51 | 15.22% |
| PI | 476 | 66 | 13.87% |
| CE | 1,279 | 176 | 13.76% |

The five states with the lowest observed late-delivery rates were:

| State | Delivered orders | Late orders | Late rate |
|---|---:|---:|---:|
| AM | 145 | 4 | 2.76% |
| RO | 243 | 7 | 2.88% |
| AP | 67 | 2 | 2.99% |
| AC | 80 | 3 | 3.75% |
| PR | 4,923 | 199 | 4.04% |

Small sample sizes in states such as RR, AC and AP mean their estimated late-delivery rates have greater uncertainty.

## 3.4 Confidence Intervals

Wilson 95% confidence intervals were calculated for state-level late-delivery proportions.

Selected results:

| State | Delivered orders | Late rate | 95% Wilson CI |
|---|---:|---:|---:|
| AL | 397 | 21.41% | 17.66%–25.71% |
| MA | 717 | 17.43% | 14.83%–20.38% |
| SE | 335 | 15.22% | 11.77%–19.46% |
| RJ | 12,350 | 12.11% | 11.54%–12.69% |
| SP | 40,494 | 4.49% | 4.30%–4.70% |
| AM | 145 | 2.76% | 1.08%–6.88% |
| AP | 67 | 2.99% | 0.82%–10.25% |
| AC | 80 | 3.75% | 1.28%–10.45% |

States with smaller delivery volumes have wider confidence intervals and less precise estimates.

## 3.5 Statistical Methods and Results

### Kruskal–Wallis Test

**Purpose:** Compare delivery-time distributions across states.

Kruskal–Wallis was selected because delivery durations are skewed and may not satisfy the assumptions of a standard one-way ANOVA.

| Statistic | Result |
|---|---:|
| H-statistic | 24,063.9734 |
| Degrees of freedom | 26 |
| p-value | <0.001 |
| Epsilon-squared | 0.2492 |

The test provides strong evidence that delivery-time distributions differ across states.

The epsilon-squared effect size indicates a substantial difference in the distributions.

This is an overall test and does not identify which specific state pairs differ.

### Chi-Square Test

**Purpose:** Determine whether late-delivery status is associated with customer state.

A contingency table of customer state against late/on-time delivery status was used.

| Statistic | Result |
|---|---:|
| Chi-square statistic | 1,785.7928 |
| Degrees of freedom | 26 |
| p-value | <0.001 |
| Cramér's V | 0.1361 |

The result indicates a statistically significant association between customer state and late-delivery status.

Cramér's V indicates a smaller association than the delivery-time distribution effect measured by epsilon-squared.

This test also does not identify which particular pairs of states differ.

## 3.6 Estimated Delivery Date vs Actual Delivery Date

To understand differences in delivery speed and estimated delivery promises, three measures were compared:

- **Actual delivery days:** Calendar days between purchase and actual delivery.
- **Estimated delivery days:** Calendar days between purchase and estimated delivery.
- **Estimate buffer days:** Estimated delivery days minus actual delivery days, calculated at the order level.

Interpretation:

- Positive buffer: delivered earlier than estimated.
- Negative buffer: delivered later than estimated.
- Zero buffer: delivered on the estimated date.

Selected state-level results:

| State | Median actual days | Median estimated days | Median estimate buffer | Late rate |
|---|---:|---:|---:|---:|
| AL | 22 | 32 | 10 | 21.41% |
| MA | 19 | 31 | 11 | 17.43% |
| RJ | 12 | 25 | 13 | 12.11% |
| SP | 7 | 19 | 11 | 4.49% |
| AM | 26 | 46 | 19 | 2.76% |
| AP | 25 | 48 | 22 | 2.99% |
| AC | 18 | 41 | 22 | 3.75% |

### Key Observations

**1. AL and MA have high late-delivery rates despite having estimate buffers.**

AL has a median 10-day buffer and a 21.41% late-delivery rate.

MA has an 11-day median buffer and a 17.43% late-delivery rate.

These states deserve investigation into carrier performance, seller dispatch delays and logistics capacity.

**2. RJ is an important high-volume priority.**

RJ has a 12.11% late-delivery rate across 12,350 deliveries.

Its delivery volume means even a moderate late-delivery rate affects a substantial number of orders.

**3. SP provides a useful large-volume benchmark.**

SP has:

- 40,494 delivered orders.
- 4.49% late deliveries.
- Median actual delivery time of 7 days.
- Median estimated delivery time of 19 days.

Its large sample makes it a useful operational comparison.

**4. A low late-delivery rate does not necessarily indicate fast delivery.**

AM has a late-delivery rate of only 2.76%, but its median actual delivery time is 26 days.

Its median estimated delivery time is 46 days.

Similarly, AP has a 2.99% late-delivery rate but a median actual delivery time of 25 days.

These observations demonstrate why delivery speed and delivery reliability should be monitored separately.

## 3.7 Business Recommendations

Use two separate operational KPIs:

1. **Delivery speed:** Median actual delivery days.
2. **Delivery reliability:** Percentage of orders delivered after their estimated dates.

Recommended actions:

- Investigate carrier and seller performance in AL and MA.
- Prioritize RJ because of its high delivery volume and late-order count.
- Use SP as a large-volume benchmark for delivery performance.
- Review estimated delivery promises in slower states such as AM and AP.
- Avoid ranking states solely by raw late-delivery percentages when sample sizes differ substantially.
- Monitor both median delivery duration and late-delivery rate in state-level operational dashboards.

## 3.8 Limitations

- State-level differences may reflect shipping distance, carrier availability, seller location, product mix and other operational factors.
- Small states have less precise late-delivery estimates.
- Kruskal–Wallis and chi-square are omnibus tests; pairwise post-hoc comparisons were not performed.
- State-level associations do not establish that geography itself causes delivery delays.
- Estimated delivery buffers may reflect operational planning decisions rather than actual logistics performance alone.

---

# 4. Overall Business Recommendations

Based on the three findings, the following actions are recommended.

| Priority | Business action | Supporting finding |
|---|---|---|
| High | Improve late-delivery monitoring and proactive customer communication | Late deliveries are strongly associated with low review scores |
| High | Monitor first-time customers experiencing late deliveries | Late first delivery is associated with a lower repeat-purchase rate |
| High | Investigate delivery operations in AL and MA | High observed state-level late-delivery rates |
| High | Review RJ logistics because of its high delivery volume | Large number of late orders despite a moderate rate |
| Medium | Monitor delivery speed separately from late-delivery rate | Slow states may still report low late-delivery rates |
| Medium | Evaluate retention interventions through controlled experiments | Observational repeat-purchase findings cannot establish causation |
| Medium | Review estimated delivery promises in slower states | Large estimate buffers may conceal slow delivery experiences |

---

# 5. Statistical Methodology Summary

| Method | Application | Reason |
|---|---|---|
| Welch's t-test | Mean review scores by delivery status | Compares means without assuming equal group variances |
| Mann–Whitney U | Review scores by delivery status | Compares rank distributions for ordinal, skewed scores |
| Rank-biserial correlation | Review-score comparison | Measures magnitude and direction of rank differences |
| Logistic regression | Low review vs delivery status | Estimates adjusted odds while controlling for selected factors |
| Two-proportion z-test | Repeat-purchase comparisons | Compares proportions between two customer groups |
| Newcombe confidence interval | Repeat-purchase risk differences | Estimates uncertainty around differences in proportions |
| Holm correction | Six reported hypothesis tests | Controls family-wise error across the reported test family |
| Wilson confidence interval | State late-delivery rates | Provides confidence intervals for proportions |
| Kruskal–Wallis | Delivery days across states | Compares distributions without assuming normality |
| Chi-square test | Late-delivery status across states | Tests association between categorical variables |
| Epsilon-squared | Kruskal–Wallis effect size | Quantifies magnitude of distribution differences |
| Cramér's V | Chi-square effect size | Quantifies strength of categorical association |

## Statistical Interpretation Principles

- A p-value below 0.05 is treated as statistically significant for the stated hypothesis tests.
- A p-value is not the probability that the null hypothesis is true.
- Statistical significance does not automatically imply business importance.
- Confidence intervals communicate uncertainty around estimated effects.
- Effect sizes help assess the practical magnitude of differences.
- Multiple-comparison correction reduces the risk of false-positive conclusions.
- Observational associations should not be presented as causal effects.

---

# 6. Deliverables and Reproducibility

The statistical analysis is implemented in:

`analysis/day6_stats.py`

The script:

- Connects to the existing DuckDB database in read-only mode.
- Reproduces the three core findings.
- Performs the original and category-adjusted logistic regressions.
- Calculates first-order repeat-purchase comparisons.
- Performs the uniform 180-day repeat-purchase robustness check.
- Calculates six-test Holm-adjusted p-values.
- Generates and verifies the charts.

## Generated Visualizations

All three charts are saved in:

`reports/figures/`

| File | Description |
|---|---|
| `finding1_late_delivery_reviews.png` | Low-rating share by delivery status |
| `finding2_repeat_by_gmv.png` | Repeat-purchase rate by first-order GMV |
| `finding3_state_late_delivery.png` | State-level late-delivery rates with 95% Wilson confidence intervals |

## Reproducibility

Run the analysis from the project root:

```bash
python analysis/day6_stats.py
```

The script prints the statistical results and verifies the generated chart files.

## Final Conclusion

The analysis identifies delivery reliability as an important area for customer-experience improvement.

Late deliveries are strongly associated with lower customer review scores. The first-order late-delivery/repeat-purchase association remains statistically significant in the six-month eligibility analysis after six-test Holm correction, but the uniform 180-day robustness check is weaker and is not significant at the 5% level.

Delivery performance varies substantially across Brazilian states. Operational decisions should consider both delivery speed and delivery reliability, while accounting for differences in sample size and uncertainty.

These findings provide a foundation for further operational analysis and controlled experiments to evaluate the impact of delivery improvements on customer satisfaction and retention.