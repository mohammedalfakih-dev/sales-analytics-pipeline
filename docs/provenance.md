# Source history and credits

This repository consolidates Mohammed Alfakih's completed HackYourFuture Data Track sales assignments. It retains one pipeline instead of duplicating the Week 4 and Week 5 implementations.

| Source | Snapshot | Reused work |
|---|---|---|
| [Week 4 solution branch](https://github.com/mohammedalfakih-dev/c55-data-week-4/tree/week4/mohammed-alfakih) | `2b86e742eabcf795d2fc5aed739068ae7448252b` | `sample_data/messy_sales.csv` and `sample_data/messy_customers.csv`, moved to `data/sample/`; original sales-analysis context |
| [Week 5 main](https://github.com/mohammedalfakih-dev/c55-data-week-5/tree/5a8abdb40a9501f223d668ffbd32e124fce5ac79) | `5a8abdb40a9501f223d668ffbd32e124fce5ac79` | Implemented cleaning, join, report logic, and initial Python tests; Docker/CI continuation |

HackYourFuture / HackYourAssignment supplied the educational assignment structure, teaching inputs, and starter components. Mohammed implemented the source assignment solutions. The original forks and their commits remain available through the links above. The teaching CSVs are copied unchanged; no claim is made that their customer records are real business data.

## Changes in the consolidated version

- Default to local fixtures; require cloud settings only when a cloud transfer is requested.
- Replace assignment-specific `API_KEY` / `GITHUB_USERNAME` assumptions with one documented configuration.
- Make Azure account and container names configurable, with optional dependencies and explicit transfer functions.
- Validate quantities, normalize missing category labels, and prevent duplicate customer keys from multiplying sales rows.
- Include ISO year in weekly metrics and write the loyalty report as well as the original outputs.
- Add an offline end-to-end test and regressions for reporting errors.
- Replace assignment grading/deployment workflows with a local-data validation workflow and container run.
- Provide project documentation and sample reports generated from the included inputs.

The current repository has no new license grant for the inherited starter material or teaching dataset. Source links preserve its origin; the original source repositories should be consulted for their terms.
