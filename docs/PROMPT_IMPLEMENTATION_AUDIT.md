# PROMPT.md implementation audit

> Audited against the supplied base prompt plus v7 parsing and v7b transparency
> prompts on 24 August 2026. “Implemented” means code and local automated checks
> exist; it does not imply external scientific, provider, browser, container, or
> pitch acceptance.

## Phase status

| Prompt phase | Status | Repository evidence |
| --- | --- | --- |
| 1. Data pipeline | Implemented and executed | `scripts/preprocess_argo.py`, `scripts/build_baselines.py`, ready manifest, 14,413,526 observations, separate production/validation Parquet artifacts, hashes, coverage report. |
| 2. Config/models | Implemented | Central evidence thresholds, timeout/radius/CORS, `.env` loading, typed request/location/query/anomaly/evidence/multi-parameter models. |
| 3A. LLM parser | Implemented; live credential rejected | Gemini `generateContent` structured JSON Schema, Pydantic validation, OpenAI Responses/Anthropic compatibility, safe provider errors, server-only secrets. |
| 3B. Deterministic parser | Implemented | 114 canonical place/region aliases, hemispheric coordinates, radii, point-over-region priority, combined ranges with recurring months/seasons, relative dates, casual parameter/intent language, multi-parameter questions, and injection/out-of-scope rejection. |
| 3C. Parser failover | Implemented and tested | Any provider exception falls back; model-disabled, malformed JSON, unexpected exception, and forced-failure tests disclose `rule_based`. |
| 3. Data/QC/aggregation/anomaly/evidence/explain | Implemented and tested | Column-pruned Parquet retrieval, haversine/region filters, mandatory adjusted A/D QC, all three aggregations, production guard, Z-score boundaries, multi-signal grade, provenance composition. |
| 4. API | Implemented and exercised | `POST /chat`, CORS, `health/live`, `health/ready`, safe 404/422/500/503 mapping, single and independent dual-parameter pipelines. |
| 5. Dependencies | Implemented | Runtime `httpx`/`python-dotenv`; pandas/NumPy/PyArrow data extra; Leaflet/react-leaflet; zero current npm audit findings. |
| 6. Frontend | Implemented and compiled | Typed fetch/adapter, real results, diagnostic typed errors, suggested queries, QC/grade/parser disclosure, actual-value anomaly/evidence/baseline/QC explainers, a clickable glossary, and explanations for every chart variant. |
| 6i. Interactive map | Implemented | CARTO/OpenStreetMap Leaflet tiles, honest query anchor, actual contributing float positions, query radius, named-region rectangle, recenter/fly, pan/zoom, attribution, and tile-failure disclosure. |
| 6j. Multi-parameter charts | Implemented | Temperature/Salinity/SST-proxy series, Temperature/Salinity/All controls, independent units/axes, overlays and legends for profile/time-series/regional views. |
| 7. Tests | Implemented and passing | 311 backend parser/data/QC/aggregation/anomaly/evidence/API/health/manifest tests and 17 frontend build/rendered-contract checks. |
| 8. Demo cache | Implemented honestly | Generator writes the three prescribed filenames and in-coverage successes. Prescribed Mumbai/Chennai/Bay examples are typed `no_data` because installed data is Arabian-Sea-only; no values are fabricated. |
| 9. Evaluation | Tooling implemented; scientific labels blocked | 59-query frozen parser suite, request cap, API scenarios, three-method evaluator, schema-only reviewed-case fixture, and reproducible notebook. Method metrics refuse to run without independent labels. |

## Definition-of-done audit

| Requirement | Result |
| --- | --- |
| One-command setup/build sequence | Implemented; preprocessing, baselines, `make check`, and dev servers run locally. |
| Any Indian Ocean natural-language question | Parser accepts the supported temperature/salinity domain; real values appear only where the installed Arabian Sea subset has observations, otherwise typed `no_data`. |
| Evidence/QC/provenance response | Verified on real in-coverage API scenarios, including recurring month selection, structured threshold checks, selected baseline metadata, trace data, and float positions. |
| Chart, toggle, interactive map, grade, expandable evidence | Implemented and TypeScript/build tested. Live visual inspection is unverified because no browser runtime was available in this environment. |
| Friendly bad-query/no-data/system errors | Implemented and tested without stack traces, API keys, or local paths. |
| Suggested query chips | Implemented, including a dual-parameter in-coverage query and explicit no-data examples. |
| Temperature/Salinity/All on charts | Implemented for responses that contain multiple parameter results. |
| Exact map location and pan/zoom | Implemented; browser acceptance remains unverified locally. |
| `make check` | Passes. |
| Trace displayed values to observations | Each bin/month includes profile IDs, float IDs, and source-file rows; the UI exposes these in a collapsible trace table. |

## Acceptance evidence and blockers

- Historical 22 August Gemini run: 27 requests total (3 authentication/contract probes plus one then-current 24-prompt suite), below the requested maximum of 50. The 24 August v7 run was provider-disabled and made zero live calls.
- Gemini result: the configured credential returned `401 UNAUTHENTICATED`; 0 of 20 supported live prompts used the LLM and all safely fell back. Four out-of-scope prompts were safely rejected. Replace the root `.env` value with a valid Google AI Studio key, then rerun the same capped command.
- Deterministic parser: 59/59 expected outcomes in the 24 August local
  single-run suite, including 49 accepted queries and 10 expected safe errors.
  The report remains `generated_not_reviewed`; this is engineering evidence,
  not reviewed accuracy or a pitch claim.
- Provider-authority and provider-failure paths are covered by isolated tests;
  the v7 run made zero live-provider calls.
- API safety scenarios: 5/5 correct.
- Browser acceptance: unavailable because the browser runtime reported no available browser surface.
- Container acceptance: unavailable because Docker is not installed/running in this environment.
- Scientific method metrics: deliberately blocked because `evaluation/fixtures/anomaly_cases.csv` has no independently reviewed cases; no metrics were invented.
- Dataset boundary: the installed exports cover only the Arabian Sea. Mumbai, Chennai, and Bay-of-Bengal answers correctly return `no_data`.
