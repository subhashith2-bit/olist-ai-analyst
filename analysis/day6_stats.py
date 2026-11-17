from pathlib import Path

import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import mannwhitneyu, ttest_ind, kruskal, chi2_contingency
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "olist.duckdb"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

# Create figures directory if it doesn't exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Connect to DuckDB
con = duckdb.connect(str(DB_PATH), read_only=True)

print("Database connected successfully.")
print("Figures directory:", FIGURES_DIR)

# ==========================================
# FINDING 1: LATE DELIVERY VS REVIEW SCORES
# ==========================================

review_df = con.sql("""
    SELECT
        order_id,
        customer_state,
        review_score,
        is_late,
        delay_days,
        gmv,
        freight_value
    FROM fact_orders
    WHERE is_delivered
      AND delivery_days IS NOT NULL
      AND is_late IS NOT NULL
      AND review_score IS NOT NULL
""").df()

print("\nFINDING 1: DATASET SUMMARY")
print("Total reviewed orders:", len(review_df))
print("\nLate delivery groups:")
print(review_df["is_late"].value_counts())

# Descriptive statistics by delivery group
review_summary = (
    review_df
    .groupby("is_late")["review_score"]
    .agg(["count", "mean", "median"])
)

# Calculate low-rating and one-star percentages
review_summary["low_rating_pct"] = (
    review_df.groupby("is_late")["review_score"]
    .apply(lambda x: (x <= 2).mean() * 100)
)

review_summary["one_star_pct"] = (
    review_df.groupby("is_late")["review_score"]
    .apply(lambda x: (x == 1).mean() * 100)
)

print("\nREVIEW SCORE SUMMARY")
print(review_summary.round(2))

# Separate review scores
on_time = review_df.loc[
    ~review_df["is_late"], "review_score"
]

late = review_df.loc[
    review_df["is_late"], "review_score"
]

# Welch's t-test
welch_result = ttest_ind(
    late, on_time, equal_var=False
)

# Mean difference: late - on-time
mean_diff = late.mean() - on_time.mean()

# 95% confidence interval for mean difference
from scipy.stats import t

se = np.sqrt(
    late.var(ddof=1) / len(late)
    + on_time.var(ddof=1) / len(on_time)
)

df_num = (
    late.var(ddof=1) / len(late)
    + on_time.var(ddof=1) / len(on_time)
) ** 2

df_den = (
    (late.var(ddof=1) / len(late)) ** 2 / (len(late) - 1)
    + (on_time.var(ddof=1) / len(on_time)) ** 2 / (len(on_time) - 1)
)

welch_df = df_num / df_den
critical_value = t.ppf(0.975, welch_df)

ci_lower = mean_diff - critical_value * se
ci_upper = mean_diff + critical_value * se

# Mann-Whitney U test
mw_result = mannwhitneyu(
    late, on_time, alternative="two-sided"
)

print("\nSTATISTICAL TESTS")
print("Mean difference (late - on-time):", round(mean_diff, 4))
print("Welch t-statistic:", round(welch_result.statistic, 4))
print("Welch p-value:", welch_result.pvalue)
print("95% CI:", round(ci_lower, 4), "to", round(ci_upper, 4))

print("\nMann-Whitney U:", mw_result.statistic)
print("Mann-Whitney p-value:", mw_result.pvalue)

# Rank-biserial correlation
n_late = len(late)
n_on_time = len(on_time)

rank_biserial = (
    (2 * mw_result.statistic)
    / (n_late * n_on_time)
) - 1

print("\nEFFECT SIZE")
print("Rank-biserial correlation:", round(rank_biserial, 4))

# Chart 1: Low ratings by delivery status

chart_data = review_summary["low_rating_pct"]

plt.figure(figsize=(8, 5))

bars = plt.bar(
    ["On-time / Early", "Late"],
    [chart_data.loc[False], chart_data.loc[True]]
)

plt.title("Low Review Ratings by Delivery Status")
plt.ylabel("Orders with 1–2 Star Reviews (%)")
plt.xlabel("Delivery Status")
plt.ylim(0, 75)

# Add percentage labels
for bar, group_key in zip(bars, [False, True]):
    height = bar.get_height()
    sample_n = int(review_summary.loc[group_key, "count"])
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height + 1,
        f"{height:.1f}%\n(n={sample_n:,})",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "finding1_late_delivery_reviews.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# Logistic regression: factors associated with low reviews

review_df["low_review"] = (
    review_df["review_score"] <= 2
).astype(int)

review_df["log_gmv"] = np.log(review_df["gmv"])

review_df["freight_share"] = (
    review_df["freight_value"] / review_df["gmv"]
)

logit_model = smf.logit(
    "low_review ~ is_late + log_gmv + freight_share + C(customer_state)",
    data=review_df
).fit(disp=False, cov_type="HC3")

# Extract adjusted odds ratio for late delivery
late_term = "is_late[T.True]"

coef = logit_model.params[late_term]
conf = logit_model.conf_int().loc[late_term]

odds_ratio = np.exp(coef)
or_ci_lower = np.exp(conf.iloc[0])
or_ci_upper = np.exp(conf.iloc[1])

print("\nLOGISTIC REGRESSION")
print("Observations:", int(logit_model.nobs))
print("Adjusted odds ratio:", round(odds_ratio, 4))
print(
    "95% CI:",
    round(or_ci_lower, 4),
    "to",
    round(or_ci_upper, 4)
)
print("P-value:", f"{logit_model.pvalues[late_term]:.3e}")


# Supplementary logistic regression: adjust for dominant product category.
# Each order is assigned the category contributing the highest total item price.
dominant_category_df = con.sql("""
    WITH order_category_value AS (
        SELECT
            oi.order_id,
            p.product_category_name AS dominant_category,
            SUM(oi.price) AS category_item_value
        FROM clean_order_items oi
        JOIN clean_products p
            ON oi.product_id = p.product_id
        GROUP BY oi.order_id, p.product_category_name
    ),
    ranked_categories AS (
        SELECT
            order_id,
            dominant_category,
            ROW_NUMBER() OVER (
                PARTITION BY order_id
                ORDER BY category_item_value DESC, dominant_category
            ) AS category_rank
        FROM order_category_value
    )
    SELECT order_id, dominant_category
    FROM ranked_categories
    WHERE category_rank = 1
""").df()

category_review_df = review_df.merge(
    dominant_category_df,
    on="order_id",
    how="left"
)

# Group rare categories to reduce sparse-category estimation problems.
category_counts = category_review_df["dominant_category"].value_counts()
rare_categories = category_counts[category_counts < 100].index

category_review_df["category_grouped"] = (
    category_review_df["dominant_category"]
    .where(~category_review_df["dominant_category"].isin(rare_categories), "Other")
    .fillna("Unknown")
)

logit_category = smf.logit(
    "low_review ~ is_late + log_gmv + freight_share + "
    "C(customer_state) + C(category_grouped)",
    data=category_review_df
).fit(disp=False, maxiter=200, cov_type="HC3")

category_coef = logit_category.params[late_term]
category_conf = logit_category.conf_int().loc[late_term]

print("\nCATEGORY-ADJUSTED LOGISTIC REGRESSION")
print("Observations:", int(logit_category.nobs))
print("Converged:", bool(logit_category.mle_retvals["converged"]))
print("Parameters:", len(logit_category.params))
print("Pseudo R-squared:", round(logit_category.prsquared, 4))
print("Adjusted odds ratio:", round(np.exp(category_coef), 3))
print(
    "95% CI:",
    round(np.exp(category_conf.iloc[0]), 3),
    "to",
    round(np.exp(category_conf.iloc[1]), 3)
)
print("P-value:", f"{logit_category.pvalues[late_term]:.3e}")

# ==========================================
# FINDING 2: FIRST-ORDER EXPERIENCE VS REPEAT
# ==========================================

first_order_df = con.sql("""
    WITH ranked_orders AS (
        SELECT
            f.order_id,
            f.customer_id,
            c.customer_unique_id,
            f.order_purchase_timestamp,
            f.is_delivered,
            f.is_late,
            f.review_score,
            f.gmv,
            f.customer_state,

            ROW_NUMBER() OVER (
                PARTITION BY c.customer_unique_id
                ORDER BY f.order_purchase_timestamp, f.order_id
            ) AS order_rank

        FROM fact_orders f
        JOIN clean_customers c
            ON f.customer_id = c.customer_id
    ),

    eligible_first_orders AS (
        SELECT *
        FROM ranked_orders
        WHERE order_rank = 1
          AND order_purchase_timestamp <= (
              SELECT MAX(first_order_date) - INTERVAL '6 months'
              FROM customer_metrics
          )
    )

    SELECT
        e.*,
        cm.is_repeat
    FROM eligible_first_orders e
    JOIN customer_metrics cm
        ON e.customer_unique_id = cm.customer_unique_id
""").df()

print("\nFINDING 2: FIRST-ORDER COHORT")
print("Customers with at least 6 months follow-up:",
      len(first_order_df))

# Keep first orders that were delivered with valid delivery status
delivery_repeat_df = first_order_df[
    first_order_df["is_delivered"]
    & first_order_df["is_late"].notna()
].copy()

print("First orders delivered with valid delivery status:",
      len(delivery_repeat_df))

print("\nRepeat purchase by first-order delivery status:")
print(
    delivery_repeat_df.groupby("is_late")["is_repeat"]
    .agg(["count", "sum", "mean"])
)

from statsmodels.stats.proportion import (
    proportions_ztest,
    confint_proportions_2indep
)

# Extract group counts
late_group = delivery_repeat_df[
    delivery_repeat_df["is_late"]
]

on_time_group = delivery_repeat_df[
    ~delivery_repeat_df["is_late"]
]

late_n = len(late_group)
late_repeats = int(late_group["is_repeat"].sum())

on_time_n = len(on_time_group)
on_time_repeats = int(on_time_group["is_repeat"].sum())

# Repeat rates
late_rate = late_repeats / late_n
on_time_rate = on_time_repeats / on_time_n

# Two-proportion z-test
z_stat, p_value = proportions_ztest(
    [late_repeats, on_time_repeats],
    [late_n, on_time_n]
)

delivery_repeat_p = p_value

# Risk difference: late minus on-time
risk_difference = late_rate - on_time_rate

# Newcombe 95% confidence interval
ci_low, ci_high = confint_proportions_2indep(
    late_repeats,
    late_n,
    on_time_repeats,
    on_time_n,
    method="newcomb"
)

print("\nREPEAT PURCHASE STATISTICAL TEST")
print("Late repeat rate:", round(late_rate * 100, 2), "%")
print("On-time repeat rate:", round(on_time_rate * 100, 2), "%")
print("Risk difference:", round(risk_difference * 100, 3), "pp")
print("95% CI:", round(ci_low * 100, 3), "to",
      round(ci_high * 100, 3), "pp")
print("Z-statistic:", round(z_stat, 4))
print("P-value:", p_value)


# Robustness check: calculate repeat purchase within the same 180-day window
# for every eligible first-time customer.
repeat_180d_df = con.sql("""
    WITH ranked_orders AS (
        SELECT
            f.order_id,
            c.customer_unique_id,
            f.order_purchase_timestamp,
            f.is_delivered,
            f.is_late,
            ROW_NUMBER() OVER (
                PARTITION BY c.customer_unique_id
                ORDER BY f.order_purchase_timestamp, f.order_id
            ) AS order_rank
        FROM fact_orders f
        JOIN clean_customers c
            ON f.customer_id = c.customer_id
    ),
    eligible_first_orders AS (
        SELECT *
        FROM ranked_orders
        WHERE order_rank = 1
          AND order_purchase_timestamp <= (
              SELECT MAX(order_purchase_timestamp) - INTERVAL '180 days'
              FROM fact_orders
          )
    ),
    first_order_repeat_flag AS (
        SELECT
            first_order.*,
            EXISTS (
                SELECT 1
                FROM fact_orders later_order
                JOIN clean_customers later_customer
                    ON later_order.customer_id = later_customer.customer_id
                WHERE later_customer.customer_unique_id =
                      first_order.customer_unique_id
                  AND later_order.order_purchase_timestamp >
                      first_order.order_purchase_timestamp
                  AND later_order.order_purchase_timestamp <=
                      first_order.order_purchase_timestamp + INTERVAL '180 days'
            ) AS repeat_within_180d
        FROM eligible_first_orders first_order
    )
    SELECT
        is_late,
        COUNT(*) AS customers,
        COUNT(*) FILTER (WHERE repeat_within_180d) AS repeat_customers,
        AVG(repeat_within_180d::INT) AS repeat_rate
    FROM first_order_repeat_flag
    WHERE is_delivered
      AND is_late IS NOT NULL
    GROUP BY is_late
""").df()

repeat_180d_summary = repeat_180d_df.set_index("is_late")
late_180d_n = int(repeat_180d_summary.loc[True, "customers"])
late_180d_repeats = int(repeat_180d_summary.loc[True, "repeat_customers"])
on_time_180d_n = int(repeat_180d_summary.loc[False, "customers"])
on_time_180d_repeats = int(repeat_180d_summary.loc[False, "repeat_customers"])

z_180d, p_180d = proportions_ztest(
    [late_180d_repeats, on_time_180d_repeats],
    [late_180d_n, on_time_180d_n]
)
rd_180d = (
    late_180d_repeats / late_180d_n
    - on_time_180d_repeats / on_time_180d_n
)
ci_180d_low, ci_180d_high = confint_proportions_2indep(
    late_180d_repeats,
    late_180d_n,
    on_time_180d_repeats,
    on_time_180d_n,
    method="newcomb"
)

print("\nUNIFORM 180-DAY REPEAT-PURCHASE ROBUSTNESS CHECK")
print(repeat_180d_df.round(5).to_string(index=False))
print("Risk difference (late - on-time):", round(rd_180d * 100, 3), "pp")
print(
    "95% CI:",
    round(ci_180d_low * 100, 3),
    "to",
    round(ci_180d_high * 100, 3),
    "pp"
)
print("P-value:", p_180d)

# Repeat purchase by first-order review rating

rating_df = first_order_df[
    first_order_df["is_delivered"]
    & first_order_df["review_score"].notna()
].copy()

rating_df["rating_group"] = np.select(
    [
        rating_df["review_score"] <= 2.5,
        (rating_df["review_score"] > 2.5) &
        (rating_df["review_score"] < 4),
        rating_df["review_score"] >= 4
    ],
    [
        "1-2.5 stars",
        "3-3.5 stars",
        "4-5 stars"
    ],
    default="Unknown"
)

rating_summary = (
    rating_df.groupby("rating_group")["is_repeat"]
    .agg(["count", "sum", "mean"])
)

rating_summary["repeat_rate_pct"] = (
    rating_summary["mean"] * 100
)

print("\nREPEAT PURCHASE BY FIRST-ORDER RATING")
print(rating_summary.round(3))

# Low-rating vs high-rating repeat purchase

low_group = rating_df[
    rating_df["rating_group"] == "1-2.5 stars"
]

high_group = rating_df[
    rating_df["rating_group"] == "4-5 stars"
]

low_n = len(low_group)
low_repeats = int(low_group["is_repeat"].sum())

high_n = len(high_group)
high_repeats = int(high_group["is_repeat"].sum())

z_stat, p_value = proportions_ztest(
    [low_repeats, high_repeats],
    [low_n, high_n]
)

rating_repeat_p = p_value

risk_diff = (
    low_repeats / low_n
    - high_repeats / high_n
)

ci_low, ci_high = confint_proportions_2indep(
    low_repeats,
    low_n,
    high_repeats,
    high_n,
    method="newcomb"
)

print("\nLOW VS HIGH FIRST-ORDER RATING")
print("Risk difference:", round(risk_diff * 100, 3), "pp")
print("95% CI:", round(ci_low * 100, 3),
      "to", round(ci_high * 100, 3), "pp")
print("Z-statistic:", round(z_stat, 4))
print("P-value:", p_value)

# Repeat purchase by first-order GMV

gmv_df = first_order_df.copy()

print("\nFIRST-ORDER GMV DISTRIBUTION")
print(
    gmv_df["gmv"].describe(
        percentiles=[0.33, 0.50, 0.67]
    )
)

# Calculate tertile boundaries
p33 = gmv_df["gmv"].quantile(1/3)
p67 = gmv_df["gmv"].quantile(2/3)

# Assign spending groups
gmv_df["gmv_group"] = np.select(
    [
        gmv_df["gmv"] <= p33,
        (gmv_df["gmv"] > p33) & (gmv_df["gmv"] <= p67),
        gmv_df["gmv"] > p67
    ],
    [
        "Low GMV",
        "Medium GMV",
        "High GMV"
    ],
    default="Unknown"
)

# Summarize repeat purchase
gmv_summary = (
    gmv_df.groupby("gmv_group")["is_repeat"]
    .agg(["count", "sum", "mean"])
)

gmv_summary["repeat_rate_pct"] = (
    gmv_summary["mean"] * 100
)

print("\nREPEAT PURCHASE BY FIRST-ORDER GMV")
print(gmv_summary.round(3))
print("\nGMV cutoffs:")
print("Low:", round(p33, 2))
print("Medium:", round(p67, 2))

# Overall association between GMV group and repeat-purchase status.
gmv_contingency = pd.crosstab(
    gmv_df["gmv_group"],
    gmv_df["is_repeat"]
).reindex(["Low GMV", "Medium GMV", "High GMV"])

gmv_chi2, gmv_omnibus_p, gmv_dof, _ = chi2_contingency(gmv_contingency)

gmv_n = int(gmv_contingency.to_numpy().sum())
gmv_min_dimension = min(
    gmv_contingency.shape[0] - 1,
    gmv_contingency.shape[1] - 1
)
gmv_cramers_v = np.sqrt(gmv_chi2 / (gmv_n * gmv_min_dimension))

print("\nOVERALL GMV-GROUP CHI-SQUARE TEST")
print("Chi-square:", round(gmv_chi2, 4))
print("Degrees of freedom:", gmv_dof)
print("P-value:", gmv_omnibus_p)
print("Cramer's V:", round(gmv_cramers_v, 4))

# Pairwise two-proportion tests, with risk differences and Newcombe CIs.
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

gmv_pairwise_results = []

gmv_groups = {
    name: gmv_df[gmv_df["gmv_group"] == name]
    for name in ["Low GMV", "Medium GMV", "High GMV"]
}

for group_a, group_b in [
    ("Low GMV", "Medium GMV"),
    ("Low GMV", "High GMV"),
    ("Medium GMV", "High GMV")
]:
    a = gmv_groups[group_a]
    b = gmv_groups[group_b]

    a_n = len(a)
    a_repeat = int(a["is_repeat"].sum())
    b_n = len(b)
    b_repeat = int(b["is_repeat"].sum())

    pair_z, pair_p = proportions_ztest(
        [a_repeat, b_repeat],
        [a_n, b_n]
    )

    pair_rd = a_repeat / a_n - b_repeat / b_n
    pair_ci_low, pair_ci_high = confint_proportions_2indep(
        a_repeat, a_n, b_repeat, b_n, method="newcomb"
    )

    gmv_pairwise_results.append({
        "comparison": f"{group_a} vs {group_b}",
        "risk_difference_pp": pair_rd * 100,
        "ci_lower_pp": pair_ci_low * 100,
        "ci_upper_pp": pair_ci_high * 100,
        "p_value": pair_p
    })

gmv_pairwise_df = pd.DataFrame(gmv_pairwise_results)

print("\nPAIRWISE GMV-GROUP COMPARISONS")
print(gmv_pairwise_df.round(6).to_string(index=False))

# Chart 2: Repeat purchase by first-order GMV

gmv_plot = gmv_summary.reindex(
    ["Low GMV", "Medium GMV", "High GMV"]
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    gmv_plot.index,
    gmv_plot["repeat_rate_pct"]
)

plt.title("Repeat Purchase Rate by First-Order GMV")
plt.xlabel("First-Order GMV Group")
plt.ylabel("Repeat Purchase Rate (%)")

plt.ylim(0, 5)

for bar, group_name in zip(bars, gmv_plot.index):
    height = bar.get_height()
    sample_n = int(gmv_plot.loc[group_name, "count"])
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height + 0.08,
        f"{height:.2f}%\n(n={sample_n:,})",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "finding2_repeat_by_gmv.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# Holm correction across the six reported hypothesis tests.
# Family: first-order delivery, first-order rating, GMV omnibus,
# and the three GMV pairwise comparisons.
holm_labels = [
    "Late delivery vs repeat purchase",
    "Review rating vs repeat purchase",
    "GMV groups overall",
    "Low vs Medium GMV",
    "Low vs High GMV",
    "Medium vs High GMV"
]

holm_p_values = [
    delivery_repeat_p,
    rating_repeat_p,
    gmv_omnibus_p,
    *gmv_pairwise_df["p_value"].tolist()
]

holm_reject, holm_adjusted_p, _, _ = multipletests(
    holm_p_values,
    method="holm"
)

holm_summary = pd.DataFrame({
    "comparison": holm_labels,
    "raw_p_value": holm_p_values,
    "holm_adjusted_p": holm_adjusted_p,
    "significant_5_percent": holm_reject
})

print("\nSIX-TEST HOLM-ADJUSTED P-VALUES")
print(holm_summary.round(6).to_string(index=False))

# ==========================================
# FINDING 3: STATE DELIVERY PERFORMANCE
# ==========================================

state_df = con.sql("""
    SELECT
        customer_state,
        COUNT(*) AS delivered_orders,
        COUNT(*) FILTER (
            WHERE is_late
        ) AS late_orders,
        MEDIAN(delivery_days) AS median_delivery_days
    FROM fact_orders
    WHERE is_delivered
      AND delivery_days IS NOT NULL
      AND is_late IS NOT NULL
      AND customer_state IS NOT NULL
    GROUP BY customer_state
""").df()

state_df["late_rate_pct"] = (
    state_df["late_orders"]
    / state_df["delivered_orders"] * 100
)

print("\nFinding 3:STATE DELIVERY PERFORMANCE")
print(
    state_df.sort_values(
        "late_rate_pct",
        ascending=False
    ).round(2).to_string(index=False)
)

# Wilson 95% confidence intervals for state late rates

ci_low, ci_high = proportion_confint(
    state_df["late_orders"],
    state_df["delivered_orders"],
    method="wilson"
)

state_df["ci_lower_pct"] = ci_low * 100
state_df["ci_upper_pct"] = ci_high * 100

state_df = state_df.sort_values(
    "late_rate_pct",
    ascending=False
)

print("\nSTATE LATE RATE WITH 95% CONFIDENCE INTERVALS")

print(
    state_df[
        [
            "customer_state",
            "delivered_orders",
            "late_orders",
            "late_rate_pct",
            "ci_lower_pct",
            "ci_upper_pct"
        ]
    ].round(2).to_string(index=False)
)

# Kruskal-Wallis: compare delivery days across states

delivery_df = con.sql("""
    SELECT
        customer_state,
        delivery_days,
        is_late
    FROM fact_orders
    WHERE is_delivered
      AND delivery_days IS NOT NULL
      AND is_late IS NOT NULL
      AND customer_state IS NOT NULL
""").df()

groups = [
    group["delivery_days"].values
    for _, group in delivery_df.groupby("customer_state")
]

H, p_kw = kruskal(*groups)

n = len(delivery_df)
k = len(groups)

epsilon_sq = (H - k + 1) / (n - k)

print("\nKRUSKAL-WALLIS TEST")
print("H-statistic:", H)
print("P-value:", p_kw)
print("Epsilon-squared:", epsilon_sq)

# Chi-square: compare late-delivery proportions across states

contingency = pd.crosstab(
    delivery_df["customer_state"],
    delivery_df["is_late"]
)

chi2, p_chi, dof, expected = chi2_contingency(contingency)

cramers_v = np.sqrt(
    chi2 / (n * min(contingency.shape[0] - 1,
                    contingency.shape[1] - 1))
)

print("\nCHI-SQUARE TEST")
print("Chi-square:", chi2)
print("Degrees of freedom:", dof)
print("P-value:", p_chi)
print("Cramer's V:", cramers_v)

# Estimated delivery date vs actual delivery date

estimate_df = con.sql("""
    SELECT
        customer_state,
        COUNT(*) AS delivered_orders,

        MEDIAN(delivery_days) AS median_actual_days,

        MEDIAN(
            DATE_DIFF(
                'day',
                CAST(order_purchase_timestamp AS DATE),
                CAST(order_estimated_delivery_date AS DATE)
            )
        ) AS median_estimated_days,

        MEDIAN(
            DATE_DIFF(
                'day',
                CAST(order_purchase_timestamp AS DATE),
                CAST(order_estimated_delivery_date AS DATE)
            ) - delivery_days
        ) AS median_estimate_buffer,

        COUNT(*) FILTER (
            WHERE is_late
        ) * 100.0 / COUNT(*) AS late_rate_pct

    FROM fact_orders
    WHERE is_delivered
      AND delivery_days IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
      AND customer_state IS NOT NULL
    GROUP BY customer_state
""").df()

print("\nESTIMATED VS ACTUAL DELIVERY")
print(
    estimate_df.sort_values(
        "median_estimate_buffer"
    ).round(2).to_string(index=False)
)

# Chart 3: State late-delivery rates with 95% CI

plot_df = state_df.sort_values("late_rate_pct").copy()

lower_error = (
    plot_df["late_rate_pct"] - plot_df["ci_lower_pct"]
)

upper_error = (
    plot_df["ci_upper_pct"] - plot_df["late_rate_pct"]
)

plt.figure(figsize=(10, 9))

plt.errorbar(
    plot_df["late_rate_pct"],
    plot_df["customer_state"],
    xerr=[lower_error, upper_error],
    fmt="o",
    capsize=3
)

plt.title("Late Delivery Rate by State (95% Wilson CI)")
plt.xlabel("Late Delivery Rate (%)")
plt.ylabel("Customer State")
plt.grid(axis="x", alpha=0.3)

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "finding3_state_late_delivery.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ==========================================
# FINAL OUTPUT CHECK
# ==========================================

print("\nDAY 6 ANALYSIS COMPLETED")

print("\nGENERATED CHARTS:")

for file in sorted(FIGURES_DIR.glob("finding*.png")):
    print(file.name, "|", round(file.stat().st_size / 1024, 2), "KB")

con.close()