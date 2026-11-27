# Day 10 — AI Analyst Copilot Evaluation Report

## 1. Objective

Evaluate the reliability of the AI Analyst Copilot's natural-language-to-SQL workflow using a manually prepared benchmark based on the Olist e-commerce dataset.

The evaluation measures:
- SQL correctness
- Business metric interpretation
- Date and aggregation logic
- Handling of ambiguous questions
- Handling of unsupported questions
- Query execution reliability
- Response latency

## 2. Evaluation dataset

The benchmark contains 30 questions.

| Split | Questions |
|---|---:|
| Development | 20 |
| Holdout | 10 |
| Total | 30 |

Question categories include:
- Easy lookups
- Medium analytical queries
- Definition-based questions
- Date logic
- SQL traps
- Ambiguous questions
- Out-of-scope questions

The benchmark contains 24 SQL-scored questions and 6 manually evaluated behavioural questions.

## 3. Benchmark audit and corrections

An initial benchmark audit identified several inconsistencies.

| Question | Issue identified | V2 correction |
|---|---|---|
| M04 | Sorting and rounding requirements were insufficiently explicit | Clarified sorting by rounded average |
| M06 | "Item sales" was ambiguous | Explicitly requested monetary sales value in Brazilian reais |
| D05 | Reference SQL returned a proportion instead of a percentage | Corrected percentage calculation |
| M02 | General percentage instruction conflicted with share calculations | Distinguished percentages from raw proportions |
| D01 | Two-decimal rounding requirement was insufficiently explicit | Added rounding requirement |

Additional evaluator improvements:
- Corrected API error classification for 429, 503 and 504 errors.
- Corrected schema loading so V2 uses its own schema file.
- Corrected Python module import paths.
- Passed all five scorer self-tests.

The original Day 10 benchmark and results were preserved separately from V2.

## 4. V2 development evaluation

**Final result: 16/16 correct**

| Metric | Result |
|---|---:|
| Development questions | 20 |
| Scored SQL questions | 16 |
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

## 5. V2 holdout evaluation

**Final result: 8/8 correct**

| Metric | Result |
|---|---:|
| Holdout questions | 10 |
| Scored SQL questions | 8 |
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

The holdout questions were selected from the frozen V2 question bank and evaluated separately from development.

## 6. Combined SQL evaluation

| Evaluation | Correct | Scored | Accuracy |
|---|---:|---:|---:|
| Development | 16 | 16 | 100% |
| Holdout | 8 | 8 | 100% |
| Combined | 24 | 24 | 100% |

The combined result represents SQL-scored questions only. It does not represent all 30 questions.

## 7. Behavioural evaluation limitations

Six questions require manual behavioural evaluation rather than SQL comparison.

- Four development questions were marked MANUAL_REVIEW.
- Two holdout questions were marked MANUAL_REVIEW.

The A03 and O02 holdout responses were not captured in the saved CSV because of a response-variable mismatch in the evaluator.

The response-capture issue was identified and corrected in the evaluator code after the holdout run. The original holdout was not rerun.

Consequently, A03 and O02 cannot be graded retrospectively. No behavioural accuracy claim is made for these two questions.

## 8. Known limitations

1. The benchmark contains only 24 SQL-scored questions.
2. A perfect score on this benchmark does not establish perfect performance on unseen business questions.
3. Behavioural evaluation requires manual grading.
4. The original holdout responses for A03 and O02 were not captured.
5. The evaluation measures correctness on the prepared dataset and does not establish production-scale reliability.
6. Latency results reflect these evaluation runs and may vary with API load and network conditions.

## 9. Reproducibility and artifacts

Important project artifacts:

| Artifact | Purpose |
|---|---|
| `eval/questions_day10_frozen.csv` | Original question bank |
| `eval/questions_v2_frozen.csv` | Corrected V2 question bank |
| `docs/schema_v2_frozen.md` | Frozen V2 schema |
| `eval/expected_results_v2.json` | V2 reference results |
| `eval/development_results_v2_final.csv` | Final V2 development results |
| `eval/holdout_results_v2.csv` | Final V2 holdout results |
| `eval/run_eval_v2.py` | Development evaluator |
| `eval/run_holdout_v2.py` | Holdout evaluator |

## 10. Conclusion

The AI Analyst Copilot achieved 100% SQL accuracy across 24 scored questions in the corrected V2 development and holdout evaluations.

The benchmark audit also identified weaknesses in question wording, metric definitions, reference SQL and response logging.

The results demonstrate successful performance on the prepared benchmark, while the small sample size and incomplete behavioural evaluation remain important limitations.

**Final reported SQL benchmark result: 24/24 correct (100%).**