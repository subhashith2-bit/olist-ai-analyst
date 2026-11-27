# Day 10 — Text-to-SQL Evaluation

## Evaluation setup
- Total questions: 30
- Difficulty: 10 Easy, 10 Medium, 10 Hard
- Models: Gemini 2.5 Flash and Gemini 3.5 Flash Lite (fallback)
- Production query cache: Bypassed
- SQL validation: Enabled
- Database: Read-only serving database
- Result comparison: Numeric tolerance, column matching, additional-column handling and order-independent row comparison

## Initial evaluation
- Passed: 24
- Failed: 6
- Initial result: 80%

## Failure investigation
- Q4: Numeric precision and output alias differences.
- Q12: Reference query corrected to use monthly_kpis.
- Q21: Additional generated columns were incorrectly treated as a failure.
- Q28: Numeric precision and output alias differences.
- Q24 and Q26: Gemini free-tier API quota exhaustion; SQL was not generated.

## Corrected evaluation
The comparison logic was improved to handle numeric tolerance, additional columns, aliases and unordered results.

The four apparent SQL mismatches were resolved through comparison-logic corrections and local verification.

- Completed LLM evaluations: 28
- Corrected comparisons: 28 passed
- API quota failures: 2
- Effective result on completed evaluations: 100%

## Limitations
- Only 30 predefined business questions were evaluated.
- Two questions could not be evaluated because of API quota limits.
- Results do not establish general-purpose SQL accuracy.
- Evaluation quality depends on the correctness of reference queries and comparison logic.

## Key learning
A query that executes successfully is not necessarily correct. Text-to-SQL evaluation must compare business results against trusted reference queries and account for numeric precision, output structure and metric definitions.