# Evidence and claim gate

> Current status: `evidence-log.csv` contains no observed result rows.

No anomaly accuracy, precision, recall, F1, false-alert rate, query coverage, parser reliability, response latency, deployment, projector, cached-fallback, or rehearsal claim is verified.

## Required quantitative evidence

### Anomaly-method comparison

Using one frozen reviewed ARGO subset and labels, compare:

1. regional-average baseline;
2. unfiltered Z-score without QC/evidence grading; and
3. the full QC-filtered, evidence-graded pipeline.

Report confusion counts, precision, recall, F1, false-alert rate, query coverage, and response time for every method. Include label construction, denominators, exclusions, uncertainty, dataset/build version, and command/notebook.

### Parser/API reliability

Use 20–30 frozen paraphrases and repeated requests to report parsing success, invalid-output rate, deterministic behavior with the LLM explicitly disabled, average and p95 latency, plus no-data, sparse-data, malformed-date, and simulated-provider-failure outcomes.

## Logging rules

Each evidence row records date, owner, claim/test, exact command/method, dataset/build, observed result, pitch permission, and evidence path. Negative results remain unchanged. Generated files under `evaluation/results/` are not claim evidence until reviewed and logged.

Automated lint/build/unit tests are engineering checks, not scientific, provider, deployment, projector, or rehearsal acceptance.
