# FloatChat-Lite scientific and evaluation policy

**Policy version:** prompt-v4-runtime-1

**Decision date:** 22 August 2026

**Status:** Implemented; external scientific validation remains open

## Product and data scope

FloatChat-Lite accepts free-form Indian Ocean questions about ARGO temperature, salinity, shallow-water temperature proxy, profiles, time series, regional averages, and anomaly screening for 2000–2026. Query understanding is broader than installed data coverage.

The installed 11 project-supplied INCOIS CSV exports are an Arabian Sea subset. Their exact spatial/temporal coverage, hashes, row counts, and artifact identities are recorded in `data/manifest.json` and `data/coverage_report.json`. Questions outside that coverage return typed `no_data`; the application must never fabricate or substitute observations.

Request handling is offline with respect to scientific data. It reads the versioned Parquet and production baseline only. No data provider is contacted during `POST /chat`.

## Mandatory QC boundary

Scientific aggregation accepts only observations meeting every condition:

1. `position_qc == "1"`;
2. `data_mode` is `A` or `D`;
3. the selected adjusted parameter QC flag is `"1"`; and
4. the selected adjusted value is present.

Rejected observations remain auditable through counts/reasons and never reach aggregation or anomaly scoring. The shallow-water proxy uses the shallowest QC-passed observation from 0–10 dbar and is not satellite SST.

## Aggregation and anomaly policy

- Profiles use fixed 0–500 dbar bins, a per-profile median in each bin, then the median across profiles.
- Time series use a per-profile aggregate, then monthly means. The shallow proxy uses the shallowest retained 0–10 dbar observation.
- Regional averages use 0–100 dbar per-profile medians, monthly means, then the mean of represented months.
- Anomaly scoring uses only the production baseline and the matching QC-passed representative aggregate.
- A zero/non-finite baseline standard deviation or `Insufficient` evidence suppresses the Z-score.
- Sparse ARGO Z-scores are called upper-ocean temperature or salinity anomalies, never marine heatwaves.

Production and validation baseline files are physically separate. Runtime code rejects any non-production baseline at the production path. The current build uses all available 2000–2026 observations for the production artifact and 2000–2009 for the separately stored validation artifact, as required by the supplied build specification.

## Evidence grade

The supplied implementation thresholds are centralized and versioned:

- fewer than 5 valid profiles: `Insufficient`;
- production baseline `n` below 10: `Insufficient`;
- baseline standard deviation at or below zero: `Insufficient`;
- fewer than 2 distinct floats: at most `Indicative`;
- QC pass rate below 0.30: at most `Indicative`;
- all conditions met: `Supported`.

These values define deterministic product behaviour; they are not presented as externally validated scientific cut-offs. Every response discloses grade reasons.

## Provenance and traceability

Every success exposes selection dates/geometry, source/version, artifact SHA-256, QC rule, raw/valid/excluded counts, distinct floats, pass rate, aggregation, baseline statistics, grade/reasons, parser used, and relevant caveats. Each displayed bin/month includes contributing profile IDs, float IDs, and source-file row samples so it can be traced to observations without exposing local filesystem paths.

## Evaluation and claim gate

Parser/API reliability uses 20–30 frozen prompts and covers provider enabled/disabled, forced provider failure, malformed output, no data, sparse data, malformed dates, mean latency, and p95 latency. Live-provider runs must respect the caller's request cap.

Anomaly evaluation compares regional-average, unfiltered Z-score, and the QC-filtered/evidence-graded pipeline on the same independently reviewed cases. No accuracy, precision, recall, F1, false-alert, provider-reliability, deployment, or rehearsal claim is pitch-approved until its exact run is reviewed and recorded in `docs/evidence/evidence-log.csv`.
