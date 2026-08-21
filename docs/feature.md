# FloatChat-Lite feature status and behaviour

> Last synchronized with source: 21 August 2026

## Status legend

- ✅ Implemented: present in current source for its stated scope
- 🟡 Partially implemented: useful foundation exists, but the feature is not complete or integrated
- 🔵 In development: active work is explicitly evidenced
- 🟠 Planned: accepted scope with no implementation
- 🔴 Blocked: cannot complete until a prerequisite is resolved
- ⚪ Needs verification: artifact or acceptance evidence is missing

No feature is labelled 🔵 because the repository does not prove who is actively working on it.

## Summary

| Feature | Status | Current state | Remaining work |
| --- | --- | --- | --- |
| Illustrative question-and-result UI | ✅ | Four local flows, loading, result, error, reset, charts, static map, confidence, explanations | Preserve during API integration; keep values illustrative until replaced by reviewed fixtures. |
| Scientific preprocessing and manifest | 🔴 | Directories and manifest schema only | Freeze source/QC/subset; implement deterministic NetCDF-to-Parquet build and integrity checks. |
| Production/validation baselines | 🔴 | Separate directories and policy documented | Implement builder and versioned artifacts. |
| Deterministic query parser | ✅ narrow | Four pinned patterns; years/months; `rule_based` tag | Add only grammar needed by frozen queries; test ambiguity and malformed input. |
| Optional LLM parser/fallback | 🟠 | Enum and environment placeholders only | Choose one provider, settings, schema validation, timeout, fallback, and forced-failure evidence. |
| Scientific repository queries | 🔴 | Readiness check/refusal boundary | Implement profile, time-series, then regional average against reviewed Parquet. |
| Anomaly/confidence policy | 🟡 | Backend function/tests and analogous frontend presentation | Connect to production baselines and real counts; validate scientifically. |
| Explanation and provenance response | 🟡 | Illustrative frontend copy and backend fields | Implement real template/service and complete required metadata. |
| Typed errors and health | 🟡 | Liveness/readiness, parse/general errors | Implement success, `no_data`, normalised request validation, integrity-aware readiness. |
| Frontend/API integration | 🔴 | No API client; incompatible types | Freeze real fixtures and add a typed adapter without redesigning the UI. |
| Container/deployment | 🟡 | Dockerfile/Compose recipe | Run with ready data, smoke-test, choose hosting, record evidence. |
| Evaluation/cached demo/rehearsal | 🟠 | Empty evidence log and placeholder directories | Build scripts, record results, sanitize cache, projector-test, rehearse. |

## 1. Illustrative question-and-result UI

### Purpose

Demonstrate how a user can ask a supported Indian Ocean question and read a visual, confidence-aware explanation.

### User flow

The user types a question and submits. A staged local loading sequence runs, a phrase resolver selects one of four bundled responses, and the app renders metadata, an insight, chart or regional value, static map context, confidence, optional anomaly/trend context, and preparation notes. Unsupported text shows one friendly error; reset returns to the input.

### Technical implementation

- React/TypeScript/Vite in `frontend/`.
- Local resolution and data in `frontend/src/data/oceanResponses.ts`.
- Recharts for charts; static local Bhuvan image for geographic context.
- No API call, external data, authentication, database, or external map tiles.

### Dependencies

Local assets and bundled typed response objects only.

### Current status

✅ Implemented for illustrative flows. It is not a real-data feature.

### Remaining work

Preserve its behaviour while replacing the local runtime source with reviewed API responses. Decide explicitly whether to add suggested chips; they are absent today.

## 2. Scientific preprocessing and manifest

### Purpose

Convert reviewed ARGO NetCDF inputs into query-ready, reproducible Parquet artifacts without doing heavy scientific work during requests.

### User flow

No direct user interaction. A data owner runs an explicit offline command before release.

### Technical implementation

The intended script validates selected variables, adjusted/raw precedence, QC flags, time/coordinates/depth, duplicates, and missing values; writes profile Parquet; and creates a manifest with provenance, version, build command, coverage, and hashes.

### Dependencies

Frozen source/access/licence decision, subset, QC policy, schema, region definitions, and local scientific Python dependencies.

### Current status

🔴 Blocked. `data/manifest.schema.json` and directories exist, but no preprocessing script, manifest, or scientific artifact exists.

### Remaining work

Resolve the data decisions, implement `scripts/preprocess_argo.py`, manually review sample profiles, validate hashes/schema, and record the build.

## 3. Production and validation baselines

### Purpose

Provide transparent monthly/region/parameter mean, standard deviation, and count while keeping serving and validation evidence independent.

### User flow

No direct interaction. Baselines are built offline from the reviewed profile artifact.

### Technical implementation

Planned `build_baselines.py` outputs separately versioned production and validation artifacts. Live queries read only production baselines; validation scripts read only validation baselines.

### Dependencies

Feature 2 plus frozen regions, parameters, periods, sufficiency policy, and dataset version.

### Current status

🔴 Blocked by absent data/preprocessing. Separate directories and manifest kinds exist.

### Remaining work

Implement the builder, verify period separation and zero/low-sample cells, and record artifacts/hashes.

## 4. Query parsing

### Purpose

Map supported natural-language questions into validated query parameters without making the demo depend on an external provider.

### User flow

An API caller submits text. Supported pinned wording becomes a profile, regional-average, or time-series request; unsupported wording receives `parse_error`.

### Technical implementation

`parse_rule_based()` recognizes four narrow phrase families, full English month names, and one/two years. It returns Pydantic `QueryParams` with `parser_used=rule_based`.

### Dependencies

Backend models only.

### Current status

✅ Implemented for the frozen narrow grammar and covered by backend tests. Older city-gazetteer/general-coordinate claims were incorrect.

### Remaining work

Freeze the final grammar after real data coverage is known. Add ambiguity, reversed-year, coordinate, missing-date, and malformed-input cases only where supported.

## 5. Optional LLM parser with deterministic fallback

### Purpose

Broaden accepted phrasing while preserving deterministic operation during provider failure.

### User flow

The backend may ask one provider for a strict parse. Timeout, malformed output, quota failure, or missing configuration must fall back to the deterministic parser and disclose `rule_based`.

### Technical implementation

No adapter exists. `.env.example` lists model/key/timeout variables, but backend `Settings` does not read them.

### Dependencies

Stable query schema, working deterministic end-to-end flow, one provider decision, server-side secret configuration, and a labelled evaluation set.

### Current status

🟠 Planned.

### Remaining work

Implement one adapter with strict validation and timeout, add failure tests, measure the frozen set, and record exact evidence. Do not add multiple providers or LangChain.

## 6. Scientific repository queries

### Purpose

Return profile, time-series, and—only if stable—regional-average results from reviewed prepared data.

### User flow

A parsed request filters observations by supported location/region, time, depth, and parameter. No matches produce `no_data`; matches produce chart-ready data and sufficiency context.

### Technical implementation

`DataRepository.readiness()` currently checks manifest status and declared file existence. `query()` always raises `DataUnavailable`; it performs no Parquet read, filter, aggregation, or no-data classification.

### Dependencies

Features 2–4, frozen spatial rules, chart-data contract, and deterministic fixtures.

### Current status

🔴 Blocked by missing scientific artifacts and repository implementation.

### Remaining work

Implement profile first, then time-series, then regional average if stable. Add schema/hash checks, spatial/time/depth tests, real fixture review, and provenance output.

## 7. Anomaly and data sufficiency

### Purpose

Explain how unusual a supported aggregate is without overstating thin evidence.

### User flow

When anomaly intent is supported, the system compares a current value with the matching production baseline. Low confidence suppresses severity; medium is provisional; high may show full severity.

### Technical implementation

Backend `score_anomaly()` implements z-score labels at absolute thresholds 1.5 and 2.5, returns no score for non-positive standard deviation or zero profiles, and uses confidence tiers 1–5/6–20/21+. Frontend status/confidence components mirror the presentation policy for illustrative data.

### Dependencies

Real query result, profile count, matching production baseline, and exact baseline period.

### Current status

🟡 Partially implemented and unit-tested in isolation. It is not connected to `/chat` or scientifically validated.

### Remaining work

Connect only to production baselines, define insufficient baseline `n`, verify negative and sparse cases, and record validation output without changing thresholds to force a result.

## 8. Explanation and provenance

### Purpose

Let a user understand what was selected, how it was aggregated, how much evidence supports it, and what caveats apply.

### User flow

The result shows source/version, aggregation, dates, radius/region, profile count, confidence, parser, anomaly baseline, and shallow-water proxy caveat where relevant.

### Technical implementation

Illustrative preparation/explanation content exists in the frontend. `ChatResponse` contains `answer_explanation`, `data_sufficiency`, `parser_used`, and `source`, but no backend explanation composer or reachable success response exists.

### Dependencies

Features 5–7 and reviewed terminology.

### Current status

🟡 Partially implemented as UI demonstration and contract vocabulary.

### Remaining work

Implement deterministic templates from real metadata, prevent invented values, add contract tests, and render parser disclosure.

## 9. Errors and health

### Purpose

Fail safely and distinguish process health, data readiness, unsupported input, no matches, and internal failure.

### User flow

API callers can check liveness/readiness. Unsupported query text receives a friendly project error. The frontend currently shows only a generic unrecognized-question state.

### Technical implementation

`/health/live`, `/health/ready`, `422 parse_error`, and `503 general_error` are implemented. `404 no_data` is modelled but unreachable. Standard Pydantic request errors are not normalized.

### Dependencies

Repository query outcomes and frontend/API integration for the remaining states.

### Current status

🟡 Partially implemented.

### Remaining work

Add integrity-aware readiness, success/no-data mapping, normalized validation decision, forced general-error test, and distinct accessible frontend states.

## 10. Frontend/API integration

### Purpose

Make the accepted interface render validated real responses through the single backend boundary.

### User flow

The browser submits to `/chat`, waits, and renders success or the typed error returned by the backend.

### Technical implementation

No API client exists. `OceanResponse` and `ChatResponse` differ, so integration requires a frozen backend data union or a narrow adapter.

### Dependencies

One real repository query, reviewed response fixtures, success contract tests, and feature 9 error shapes.

### Current status

🔴 Blocked by the data/repository/contract path.

### Remaining work

Freeze fixtures, reconcile types, add the adapter, preserve UI behaviour, and run browser/projector acceptance.

## 11. Container and deployment

### Purpose

Provide one reproducible artifact that serves the API and built frontend with read-only data.

### User flow

Operators build/start the container; users open the served application.

### Technical implementation

A multi-stage Dockerfile and Compose service exist. FastAPI mounts static build output when present. No confirmed hosting target or recorded container run exists.

### Dependencies

Ready scientific artifacts, integrated frontend, secret policy, and smoke tests.

### Current status

🟡 Recipe implemented; runtime/deployment acceptance ⚪ needs verification.

### Remaining work

Run liveness/readiness/pinned/error smoke checks, verify read-only artifact mounting and secrets, then choose/record hosting.

## 12. Evaluation, cached fallback, and rehearsal

### Purpose

Support truthful claims and keep the presentation usable during provider/network/runtime failure.

### User flow

The team measures parser/scientific behaviour, captures sanitized real responses, and switches to clearly labelled cached material when necessary.

### Technical implementation

The evidence CSV has headers only. Evaluation scripts and cached artifacts do not exist; demo directories contain `.gitkeep` placeholders.

### Dependencies

Stable integrated build, versioned data/baselines, frozen test sets, and presentation environment.

### Current status

🟠 Planned.

### Remaining work

Implement evaluations, record positive/negative outputs, sanitize cached JSON/screenshots, run projector/offline checks, and record actual rehearsal results.

## Deferred features

Multilingual support, PFZ/wave/cyclone domains, multi-turn memory, authentication/accounts, database migration, fine-tuning, native mobile, and WhatsApp integration are outside the core roadmap. They remain long-term options only after the real-data core is complete and a verified need exists.
