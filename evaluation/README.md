# Quantitative evaluation workspace

This directory contains the frozen 59-query parser fixture, the schema-only anomaly case fixture, and ignored generated reports. No accuracy, precision, reliability, or latency claim is approved merely because a report was generated.

```text
evaluation/
├── fixtures/    Frozen, small, reviewable labels/prompts/region definitions
├── notebooks/   Optional reproducible notebooks
└── results/     Generated reports; ignored until deliberately reviewed
```

## Required evaluations

1. **Anomaly-method comparison:** on one fixed reviewed ARGO subset, compare a regional-average baseline, an unfiltered Z-score, and the full QC-filtered/evidence-graded pipeline. Report confusion counts, precision, recall, F1, false-alert rate, query coverage, and response time with the labeling method and denominator.
2. **Parser/API reliability:** use the frozen 59-query suite and repeated requests to report parsing success, invalid-output rate, deterministic behaviour with the provider explicitly disabled, average/p95 latency, and no-data, sparse-data, malformed-date, and simulated-provider-failure outcomes.

Commands:

```bash
.venv/bin/python scripts/test_parser_reliability.py
.venv/bin/python scripts/evaluate_methods.py
```

The method comparison exits non-zero until `anomaly_cases.csv` contains reviewed labels and references. That failure is intentional.

## Rules

- Inputs, labels, region definitions, dataset/build versions, seeds, environment, commands, and package versions must be recorded.
- A notebook must run from a clean environment using repository-relative or explicit input paths.
- Generated reports do not become pitch evidence until reviewed and entered in `docs/evidence/evidence-log.csv`.
- Negative results and failed cases remain in the output. Never edit a metric or denominator to improve a claim.
- Large or redistribution-sensitive ARGO data stays under `data/` and is not copied into fixtures.
