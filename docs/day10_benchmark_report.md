# Day 10 — AI Analyst Copilot: Benchmark Evaluation and Audit

## 1. Objective

Evaluate the reliability of the Olist AI Analyst Copilot's natural-language-to-SQL workflow using a manually prepared benchmark.

The evaluation examines:

- SQL correctness
- Business metric interpretation
- Date and aggregation logic
- Ambiguous-question handling
- Out-of-scope question handling
- SQL execution reliability
- API reliability
- Response latency
- Benchmark and evaluator correctness

The benchmark uses the Olist Brazilian e-commerce dataset. All monetary values are expressed in Brazilian reais (R$).

## 2. Benchmark structure

The original benchmark contains 30 questions.

| Split | Questions |
|---|---:|
| Development | 20 |
| Holdout | 10 |
| Total | 30 |

The questions cover:

- Easy lookups
- Medium analytical queries
- Definition-based questions
- Date logic
- SQL traps
- Ambiguous questions
- Out-of-scope questions

There are 24 SQL-scored questions and 6 behaviour questions requiring manual evaluation.

## 3. V1 baseline results

The original V1 development evaluation produced:

| Metric | Result |
|---|---:|
| Development questions | 20 |
| Correct SQL | 15 |
| Execution errors | 1 |
| API errors | 2 |
| Manual review | 2 |

The SQL accuracy was 15/16 (93.75%), counting the execution failure as an unsuccessful SQL attempt and excluding the two API errors.

### V1 model distribution

| Model | Correct | Execution errors | API errors | Manual review |
|---|---:|---:|---:|---:|
| Gemini 2.5 Flash | 0 | 0 | 2 | 0 |
| Gemini 3.5 Flash Lite | 15 | 1 | 0 | 2 |

Gemini 2.5 Flash had two API errors. Gemini 3.5 Flash Lite generated one SQL execution failure.

### Original execution failure: T04

Question:

"Identify the partial calendar months in the dataset and show each month's order count and delivered GMV."

Generated SQL included:

`WHERE is_is_partial_month = TRUE OR is_partial_month = TRUE`

DuckDB raised a BinderException because `is_is_partial_month` was not a valid column. The documented column was `is_partial_month`.

Classification: SQL-generation and schema-grounding failure.

The other two V1 failures were API errors, not SQL-generation failures.

## 4. Benchmark audit and V2 corrections

The V1 results exposed weaknesses in benchmark wording, reference SQL and evaluation logic.

The following changes were made for V2:

| Question | Correction |
|---|---|
| M02 | Clarified percentage/share interpretation |
| M04 | Clarified average delivery-time rounding and sorting |
| M06 | Clarified monetary item-sales terminology |
| D01 | Explicitly requested percentage rounding to two decimal places |
| D05 | Corrected reference SQL to return a percentage rather than an unscaled proportion |

The scorer was also improved to handle column ordering, extra generated columns, row alignment and numeric normalization. Five scorer self-tests passed.

### Important benchmark limitation

V2 is a corrected and clarified benchmark, not an untouched reproduction of V1.

Three of the ten V2 holdout questions were changed after V1 results:

- M04: wording clarified
- M06: wording clarified
- D05: reference SQL corrected

M02 and D01 were also revised, but they belong to development.

The V2 schema was updated from the original schema and used in both final V2 evaluation runs.

Consequently, the V2 holdout should be described as a separately evaluated, post-audit holdout, not a pristine independent holdout.

## 5. V2 evaluation configuration

| Setting | Value |
|---|---|
| Primary model | Gemini 2.5 Flash |
| Fallback model | Gemini 3.5 Flash Lite |
| Prompt version | v1 |
| Evaluation database | `olist_serving.duckdb` |
| Development evaluator | `eval/run_eval_v2.py` |
| Holdout evaluator | `eval/run_holdout_v2.py` |
| Frozen question bank | `eval/questions_v2_frozen.csv` |
| Frozen schema | `docs/schema_v2_frozen.md` |
| Reference results | `eval/expected_results_v2.json` |

Final V2 schema SHA256:

`50145341a9d96c2bad8b02d46569f45430a7155d85d8a09c3e2c533f6e0d3f7c2f`

The development and holdout runs reported the same schema hash.

### Cache behaviour

All three evaluation runs bypassed the production query cache.

Evidence:

- The original V1 evaluator calls `generate_valid_sql()` directly.
- The V2 development evaluator calls `generate_valid_sql()` directly.
- The V2 holdout evaluator calls `generate_valid_sql()` directly.
- `generate_valid_sql()` calls `llm.call_llm(prompt)` directly.
- The generation function does not invoke `get_cached_sql()` or `save_cached_sql()`.

The production application has caching, but these evaluation scripts bypass that application workflow.

Therefore, the recorded evaluation results represent fresh model-generation attempts rather than cached SQL reuse.

## 6. V2 development results

**Final result: 16/16 SQL questions correct.**

| Metric | Result |
|---|---:|
| Development questions | 20 |
| SQL-scored questions | 16 |
| Correct SQL | 16 |
| Incorrect SQL | 0 |
| SQL accuracy | 100% |
| Manual review | 4 |
| Validation rejected | 0 |
| Execution errors | 0 |
| Timeouts | 0 |
| API errors | 0 |
| Median latency | 2.693 seconds |
| Slowest latency | 4.243 seconds |

### Development accuracy by model

| Model | Correct | Scored | Accuracy |
|---|---:|---:|---:|
| Gemini 2.5 Flash | 7 | 7 | 100% |
| Gemini 3.5 Flash Lite | 9 | 9 | 100% |

These are small samples and should not be interpreted as proof of equal general performance.

## 7. V2 holdout results

**Final result: 8/8 SQL questions correct.**

| Metric | Result |
|---|---:|
| Holdout questions | 10 |
| SQL-scored questions | 8 |
| Correct SQL | 8 |
| Incorrect SQL | 0 |
| SQL accuracy | 100% |
| Manual review | 2 |
| Validation rejected | 0 |
| Execution errors | 0 |
| Timeouts | 0 |
| API errors | 0 |
| Median latency | 1.682 seconds |
| Slowest latency | 3.158 seconds |

### Holdout accuracy by model

| Model | Correct | Scored | Accuracy |
|---|---:|---:|---:|
| Gemini 2.5 Flash | 5 | 5 | 100% |
| Gemini 3.5 Flash Lite | 3 | 3 | 100% |

The holdout model distribution was evenly split between the two models.

## 8. Combined V2 SQL performance

| Evaluation | Correct | Scored | Accuracy |
|---|---:|---:|---:|
| Development | 16 | 16 | 100% |
| Holdout | 8 | 8 | 100% |
| Combined | 24 | 24 | 100% |

The combined accuracy applies only to the 24 SQL-scored questions. The six behaviour questions are excluded.

### Wilson 95% confidence intervals

Because the benchmark has a small sample size, a 100% observed score should not be interpreted as proof of perfect generalisation.

| Evaluation | Result | Wilson 95% confidence interval |
|---|---:|---:|
| Development | 16/16 | 80.6%–100% |
| Holdout | 8/8 | 67.6%–100% |
| Combined | 24/24 | 86.2%–100% |

These are descriptive binomial intervals. They do not remove benchmark-selection bias or establish unbiased performance on unseen questions.

## 9. Behavioural evaluation and logging limitation

Six questions require manual behavioural evaluation rather than SQL comparison.

### Development questions

| ID | Question | Required behaviour |
|---|---|---|
| A01 | What was the business's revenue? | Ask for clarification or state a defensible assumption |
| A02 | Who were the best customers? | Ask for clarification or state a defensible assumption |
| O01 | What was the net profit margin for each product category? | State that required data is unavailable; do not invent columns or values |
| O03 | What is the average age of customers in each state? | State that required data is unavailable; do not invent columns or values |

### Holdout questions

| ID | Question | Required behaviour |
|---|---|---|
| A03 | Show recent customer activity. | Ask for clarification or state a defensible assumption |
| O02 | How much seller commission did the platform earn from each seller? | State that required data is unavailable; do not invent columns or values |

### Response-capture defect

All six saved CSV records contain blank `behavior_response` values.

The evaluator used a response variable that was not correctly assigned in the original response-capture code. The mismatch was identified and corrected after the V2 evaluations.

The corrected code now assigns the LLM result to `response` and saves that variable as `behavior_response`.

The original evaluations were not rerun.

Consequently:

- None of the six behavioural responses can be graded retrospectively.
- No behavioural pass rate is claimed.
- These questions are reported as ungraded due to evaluator logging failure, not as model successes or model failures.

## 10. Independent data validation

Five independent cross-checks were performed using the clean source tables.

| Metric | Independent source | Result |
|---|---|---:|
| Total orders | `clean_orders` | 99,441 |
| Delivered orders | `clean_orders` | 96,478 |
| Delivered GMV | `clean_orders` + `clean_order_items` | R$15,419,773.75 |
| Recorded payment total | `clean_order_payments` | R$16,008,872.12 |
| Distinct people | `clean_customers` | 96,096 |

These checks independently validate important business metrics used in the benchmark.

They do not constitute independent validation of every generated SQL query.

## 11. Git provenance limitation

The frozen V2 files were not tracked by Git when their history was inspected.

The following files had no Git history under their frozen paths:

- `eval/questions_v2_frozen.csv`
- `docs/schema_v2_frozen.md`
- `eval/run_holdout_v2.py`

`git ls-files` also returned no tracked entries for these paths.

Therefore, the exact commit timestamps and the precise chronological relationship between benchmark corrections and holdout freezing cannot be established from Git history.

This is a reproducibility and provenance limitation.

The final V2 evaluation did use the same reported schema hash for development and holdout, but that does not independently prove when the schema was frozen.

## 12. Known limitations

1. The V2 benchmark contains only 24 SQL-scored questions.
2. Five benchmark items were corrected or reworded after V1 results.
3. Three of those changes affected the V2 holdout questions.
4. The holdout's historical freeze date cannot be verified through Git.
5. Six behavioural responses were lost due to an evaluator logging defect.
6. The V2 schema was revised from the original schema.
7. The confidence intervals are wide because of the small sample.
8. Model-specific results are based on small sample sizes.
9. Evaluation latency may vary with API load and network conditions.
10. The benchmark does not establish production-scale reliability or performance on arbitrary unseen questions.

## 13. Conclusion

The corrected V2 benchmark produced 24 correct SQL results out of 24 scored questions across development and holdout evaluations.

The evaluation process also identified important weaknesses in benchmark wording, reference SQL, schema grounding, response logging and benchmark provenance.

The result demonstrates successful performance on the prepared V2 SQL benchmark. It does not establish perfect generalisation or behavioural reliability.

The next evaluation stage should use a fresh, independently prepared challenge set, with reference SQL and expected results frozen before any model calls.

**Final reported result: 24/24 SQL-scored questions correct (100%), with a Wilson 95% confidence interval of approximately 86.2%–100%.**