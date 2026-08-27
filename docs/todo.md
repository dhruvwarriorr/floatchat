# FloatChat-Lite executable todo

> Rev. C synchronization: 24 August 2026

## Completed structure/foundation

- [x] Preserve the accepted visual language while integrating real API behaviour.
- [x] Provide FastAPI/parser/health/safe-error foundation.
- [x] Implement the production-only anomaly policy and boundary tests.
- [x] Add manifest/data/baseline/demo/evidence/container boundaries.
- [x] Implement `qc.py`, `aggregation.py`, `evidence.py`, `explain.py`, fixtures, and evaluation commands.

## P0 — freeze policy

- [x] Record ARGO source/licence/subset and region/radius definitions in the manifest, coverage report, and architecture decision records.
- [x] Freeze accepted QC flags, raw/adjusted precedence, `data_mode`, retained audit fields, and shallow-water cutoff.
- [x] Implement the supplied baseline `n`, distinct-float, QC-pass thresholds, and grade reasons with a validation caveat.
- [x] Freeze anomaly ground truth/labeling method, exclusions, and coverage denominator.
- [x] Keep Recharts and migrate geographic context to interactive Leaflet/CARTO.

## P0 — data and QC-gated backend

- [x] Implement deterministic preprocessing with QC/data-mode fields and manifest/hashes.
- [ ] Manually review representative profiles.
- [x] Build independent production and validation baselines.
- [x] Implement schema-aware profile, time-series, and regional retrieval.
- [x] Implement QC Filter retained/excluded outputs and warning.
- [x] Test that rejected observations cannot reach anomaly scoring.
- [x] Refactor anomaly service to accept QC-passed aggregates only.
- [x] Implement fail-closed Evidence Grade/reasons from centralized policy.
- [x] Implement actual provenance-panel composition.
- [x] Migrate target Pydantic models and add success/no-data/QC-warning/grade/zero-std tests.

## P1 — UI and evaluation

- [x] Migrate the frontend contract through a typed adapter.
- [x] Add independent Temperature/Salinity/All pipelines and chart toggles.
- [x] Add an exact query marker/radius or named-region overlay on an interactive map.
- [x] Trace displayed chart points to profile, float, and source-row samples.
- [x] Render typed errors, QC warning, evidence-grade badge policy, parser disclosure, and expandable panel.
- [x] Create and expand the frozen parser fixture to 59 queries plus the anomaly-case schema.
- [ ] Add reviewed anomaly labels/references under `evaluation/fixtures/`.
- [x] Build a reproducible three-method comparison script that fails closed without reviewed labels.
- [ ] Report confusion counts, precision, recall, F1, false-alert rate, coverage, and response time.
- [x] Build a 59-query parser reliability evaluation.
- [x] Generate disabled/fallback/no-data/sparse-data/malformed-date/simulated-failure and average/p95 latency results.
- [ ] Run and review provider-enabled and malformed-provider-output behavior with an authorized provider configuration.
- [ ] Review reports and add exact evidence rows.

## P1 — release

- [ ] Verify container with ready data and all health/success/error paths.
- [x] Generate sanitized cache with QC/grade/provenance fields and an explicit no-data case.
- [ ] Test browser, narrow screen, projector, keyboard/accessibility-focused behavior, and recovery.
- [ ] Record rehearsals and audit pitch claims.

## P2 / deferred

- [x] Add Gemini as the one primary optional provider with schema validation and deterministic fallback.
- [ ] Include regional average only if QC-passed coverage is stable.
- [ ] Defer multilingual, other data domains, memory/accounts, database, advanced ML, mobile, and scaling.
