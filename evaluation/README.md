# Quantitative evaluation workspace

This directory is the repository boundary for the two reproducible evaluations required by `docs/prd.md` Rev. B. It contains structure only; no dataset, notebook, result, accuracy, precision, reliability, or latency claim exists yet.

```text
evaluation/
├── fixtures/    Frozen, small, reviewable labels/prompts/region definitions
├── notebooks/   Reproducible comparison and reliability notebooks
└── results/     Generated reports; ignored until deliberately reviewed
```

## Required evaluations

1. **Anomaly-method comparison:** on one fixed reviewed ARGO subset, compare a regional-average baseline, an unfiltered Z-score, and the full QC-filtered/evidence-graded pipeline. Report confusion counts, precision, recall, F1, false-alert rate, query coverage, and response time with the labeling method and denominator.
2. **Parser/API reliability:** use 20–30 frozen paraphrases and repeated requests to report parsing success, invalid-output rate, deterministic behaviour with the LLM explicitly disabled, average/p95 latency, and no-data, sparse-data, malformed-date, and simulated-provider-failure outcomes.

## Rules

- Inputs, labels, region definitions, dataset/build versions, seeds, environment, commands, and package versions must be recorded.
- A notebook must run from a clean environment using repository-relative or explicit input paths.
- Generated reports do not become pitch evidence until reviewed and entered in `docs/evidence/evidence-log.csv`.
- Negative results and failed cases remain in the output. Never edit a metric or denominator to improve a claim.
- Large or redistribution-sensitive ARGO data stays under `data/` and is not copied into fixtures.
