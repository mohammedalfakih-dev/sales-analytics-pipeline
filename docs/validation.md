# Local verification

The proposed portfolio version was verified on 1 October 2026:

- Ruff lint checks passed for `src` and `tests`.
- Ruff formatting checks passed after formatting.
- All 22 Python tests passed on Python 3.12.
- The local sample run read 122 sales rows and 37 customer rows, retained 102 cleaned transactions, and joined 98 transactions to customers.
- Report revenue totals reconcile to 18,017.22 source currency units.
- The Docker image built successfully and ran with networking disabled, producing the same transaction count and revenue total.
- The category chart was inspected for readable labels and correct relative values.

The optional Azure transfer functions were not run against a live account. GitHub Actions results must be checked on the review PR; local verification does not establish a remote CI result.

The pinned Matplotlib version emits dependency deprecation warnings with the resolved Pyparsing version. These warnings did not fail the tests or chart generation.
