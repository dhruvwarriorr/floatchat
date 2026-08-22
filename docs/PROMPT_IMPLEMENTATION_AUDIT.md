# PROMPT.md implementation audit

> Audited against the supplied `PROMPT.md` on 22 August 2026. “Implemented” means code and local automated checks exist; it does not imply external scientific, provider, browser, container, or pitch acceptance.

## Phase status

| Prompt phase | Status | Repository evidence |
| --- | --- | --- |
| 1. Data pipeline | Implemented and executed | `scripts/preprocess_argo.py`, `scripts/build_baselines.py`, ready manifest, 14,413,526 observations, separate production/validation Parquet artifacts, hashes, coverage report. |
| 2. Config/models | Implemented | Central evidence thresholds, timeout/radius/CORS, `.env` loading, typed request/location/query/anomaly/evidence/multi-parameter models. |
| 3A. LLM parser | Implemented; live credential rejected | Gemini `generateContent` structured JSON Schema, Pydantic validation, OpenAI Responses/Anthropic compatibility, safe provider errors, server-only secrets. |
| 3B. Deterministic parser | Implemented | 51 city/place aliases plus 7 named-region aliases, hemispheric coordinates, radii, dates, parameters, query types, out-of-scope rejection. |
| 3C. Parser failover | Implemented and tested | Any provider exception falls back; model-disabled, malformed JSON, unexpected exception, and forced-failure tests disclose `rule_based`. |
| 3. Data/QC/aggregation/anomaly/evidence/explain | Implemented and tested | Column-pruned Parquet retrieval, haversine/region filters, mandatory adjusted A/D QC, all three aggregations, production guard, Z-score boundaries, multi-signal grade, provenance composition. |
| 4. API | Implemented and exercised | `POST /chat`, CORS, `health/live`, `health/ready`, safe 404/422/500/503 mapping, single and independent dual-parameter pipelines. |
| 5. Dependencies | Implemented | Runtime `httpx`/`python-dotenv`; pandas/NumPy/PyArrow data extra; Leaflet/react-leaflet; zero current npm audit findings. |
| 6. Frontend | Implemented and compiled | Typed fetch/adapter, real results, typed errors, suggested chips, QC/grade/parser disclosure, expandable evidence, lazy visual bundles. |
| 6i. Interactive map | Implemented | CARTO/OpenStreetMap Leaflet tiles, exact marker, query radius, named-region rectangle, recenter/fly, pan/zoom, attribution, pulsing marker, tile-failure disclosure. |
| 6j. Multi-parameter charts | Implemented | Temperature/Salinity/SST-proxy series, Temperature/Salinity/All controls, independent units/axes, overlays and legends for profile/time-series/regional views. |
| 7. Tests | Implemented and passing | Backend parser/data/QC/aggregation/anomaly/evidence/API/health/manifest integrity tests and frontend build/contract tests. |
| 8. Demo cache | Implemented honestly | Generator writes the three prescribed filenames and in-coverage successes. Prescribed Mumbai/Chennai/Bay examples are typed `no_data` because installed data is Arabian-Sea-only; no values are fabricated. |
| 9. Evaluation | Tooling implemented; scientific labels blocked | 24-query frozen reliability suite, request cap, API scenarios, three-method evaluator, schema-only reviewed-case fixture, reproducible notebook. Method metrics refuse to run without independent labels. |

## Definition-of-done audit

| Requirement | Result |
| --- | --- |
| One-command setup/build sequence | Implemented; preprocessing, baselines, `make check`, and dev servers run locally. |
| Any Indian Ocean natural-language question | Parser accepts the supported temperature/salinity domain; real values appear only where the installed Arabian Sea subset has observations, otherwise typed `no_data`. |
| Evidence/QC/provenance response | Verified on real in-coverage single and dual-parameter API queries. |
| Chart, toggle, interactive map, grade, expandable evidence | Implemented and TypeScript/build tested. Live visual inspection is unverified because no browser runtime was available in this environment. |
| Friendly bad-query/no-data/system errors | Implemented and tested without stack traces, API keys, or local paths. |
| Suggested query chips | Implemented, including a dual-parameter in-coverage query and explicit no-data examples. |
| Temperature/Salinity/All on charts | Implemented for responses that contain multiple parameter results. |
| Exact map location and pan/zoom | Implemented; browser acceptance remains unverified locally. |
| `make check` | Passes. |
| Trace displayed values to observations | Each bin/month includes profile IDs, float IDs, and source-file rows; the UI exposes these in a collapsible trace table. |

## Acceptance evidence and blockers

- Gemini live allowance used: 27 requests total (3 authentication/contract probes plus one 24-prompt suite), below the requested maximum of 50.
- Gemini result: the configured credential returned `401 UNAUTHENTICATED`; 0 of 20 supported live prompts used the LLM and all safely fell back. Four out-of-scope prompts were safely rejected. Replace the root `.env` value with a valid Google AI Studio key, then rerun the same capped command.
- Deterministic parser: 24/24 correct in the recorded single-run frozen suite.
- Simulated provider failure: 24/24 correct fallback results.
- API safety scenarios: 5/5 correct.
- Browser acceptance: unavailable because the browser runtime reported no available browser surface.
- Container acceptance: unavailable because Docker is not installed/running in this environment.
- Scientific method metrics: deliberately blocked because `evaluation/fixtures/anomaly_cases.csv` has no independently reviewed cases; no metrics were invented.
- Dataset boundary: the installed exports cover only the Arabian Sea. Mumbai, Chennai, and Bay-of-Bengal answers correctly return `no_data`.
