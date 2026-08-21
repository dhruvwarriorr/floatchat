# FloatChat-Lite executable todo

> Last synchronized: 21 August 2026
> Check an item only when source/artifacts and proportionate verification exist. Evidence-gated claims also require a row in `evidence/evidence-log.csv`.

## Completed foundation

- [x] Preserve the accepted React/TypeScript/Vite frontend under `frontend/`.
- [x] Implement illustrative local depth, SST/anomaly, salinity, and warming/trend views.
- [x] Use Recharts and a static local Bhuvan map image; keep runtime free of external map tiles.
- [x] Implement query submit/Enter, empty-input protection, staged loading, unsupported error, and reset.
- [x] Define backend Pydantic request/response/error vocabulary.
- [x] Implement liveness/readiness endpoints and safe missing-data behaviour.
- [x] Implement the narrow deterministic grammar for four pinned phrase families.
- [x] Implement/test confidence and z-score policy boundaries in isolation.
- [x] Add CI, local check targets, manifest schema, artifact directories, evidence log, and container recipe.

## P0 — next: scientific data source of truth

- [ ] Freeze the exact ARGO source URL/access method and review licence/redistribution terms.
- [ ] Freeze the subset coverage needed for Mumbai profile/time-series first.
- [ ] Freeze region/radius definitions, QC policy, adjusted/raw precedence, depth conversion, and shallow-water proxy cutoff.
- [ ] Implement `scripts/preprocess_argo.py` with explicit paths, deterministic output, validation, and non-zero failure.
- [ ] Manually inspect representative processed profiles and record the result.
- [ ] Write profile Parquet and a draft manifest with provenance, coverage, version, command, and hashes.
- [ ] Implement manifest schema/hash/integrity validation; do not rely only on file existence.
- [ ] Implement `scripts/build_baselines.py` with separate production and validation artifacts.
- [ ] Verify production/validation periods and artifacts cannot be interchanged.

## P0 — repository and API success path

- [ ] Implement Parquet schema validation and prepared-data loading.
- [ ] Implement spatial, date, depth, parameter, and acceptable-observation filters.
- [ ] Implement `profile` query and verify one manually checked real result.
- [ ] Implement `time_series` query and shallow-water proxy caveat.
- [ ] Implement profile count, coverage text, and confidence from real matches.
- [ ] Connect production-baseline anomaly scoring; skip insufficient/zero-std cases.
- [ ] Implement deterministic explanation composition from result metadata.
- [ ] Return validated `ChatResponse` success bodies.
- [ ] Emit `404 no_data` for valid queries with no acceptable matches.
- [ ] Decide and test the Pydantic request-validation error policy.
- [ ] Freeze reviewed real response fixtures and chart-data variants.

## P1 — accepted frontend integration

- [ ] Reconcile `OceanResponse` and `ChatResponse` without importing illustrative field semantics into the API.
- [ ] Replace local runtime resolution with a typed `/chat` adapter while preserving UI behaviour.
- [ ] Render distinct parse, no-data, general, and request-validation failures.
- [ ] Render a subtle `rule_based` parser disclosure.
- [ ] Ensure source/version, method, selection, dates, profile count, confidence, and proxy caveats are visible.
- [ ] Verify keyboard, narrow-screen, desktop, and projector behaviour; record evidence.
- [ ] Decide whether suggested-query chips remain omitted or are explicitly added.

## P1 — evidence, resilience, and release

- [ ] Implement `scripts/validate_heatwave.py` (or another frozen known-event evaluation) and record the exact result.
- [ ] Run API success/error/trace-safety checks against the release dataset.
- [ ] Build/start the container with ready data and run health/pinned smoke checks.
- [ ] Capture sanitized cached JSON/screenshots with dataset/build version and origin.
- [ ] Test offline fallback and failure recovery on the presentation machine.
- [ ] Rehearse the complete demo and record actual passes/failures.
- [ ] Audit the pitch for claims that lack evidence rows.

## P2 — optional after the deterministic core

- [ ] Decide whether one LLM provider is needed and verify quota/latency/secret handling.
- [ ] Add LLM settings and one strict validated provider adapter.
- [ ] Force timeout, malformed output, missing config, and quota failure; verify deterministic fallback.
- [ ] Implement a frozen labelled parser evaluation and record the result.
- [ ] Implement `regional_average` only if the first two real flows and coverage are stable.
- [ ] Strengthen readiness to report integrity separately from scientific validation.

## Blocked

- Frontend/API success integration is blocked until a reviewed real response fixture exists.
- Real anomaly results are blocked until production baselines exist.
- Scientific validation is blocked until separate validation artifacts exist.
- Provider evaluation is blocked until the deterministic end-to-end path and provider decision exist.
- Release/demo acceptance is blocked until real data, integration, and evidence artifacts exist.

## Long-term / unscheduled

- [ ] Evaluate multilingual support only after a verified user need.
- [ ] Evaluate PFZ, wave-height, cyclone, or forecast domains as separate scoped projects.
- [ ] Evaluate multi-turn memory, authentication, persistence, mobile, or WhatsApp only after core acceptance.
- [ ] Consider a database only if measured scale/update requirements exceed file-based artifacts.
