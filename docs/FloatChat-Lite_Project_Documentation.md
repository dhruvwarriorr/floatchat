**SIH PROJECT HANDBOOK**

# FloatChat-Lite

> Explainable conversational access to Indian Ocean ARGO data

**Focused, explainable, and buildable by a small student team**

Version 1.0

Prepared 14 August 2026

Status: implementation-ready baseline; validation evidence pending

## 1. Executive summary

> **Project in one sentence:** A user asks an ocean-data question in plain language and receives a chart, map, anomaly context, data sufficiency, and a transparent explanation based on preprocessed INCOIS ARGO profiles.

FloatChat-Lite reduces the gap between technically rich ARGO observations and users who do not work directly with NetCDF files, quality-control flags, or scientific Python. The first release is intentionally narrow: three query types, temperature and salinity, a single web screen, one API endpoint, file-based storage, and an explainable z-score baseline. This scope is designed for a six-member student team and can be compressed into a 48-hour hackathon sprint after the data subset is prepared.

| **Decision** | **Project baseline** |
| --- | --- |
| Primary outcome | A judge can ask a pinned question and understand both the result and how it was computed. |
| Core proof | Natural-language query -> structured parameters -> ARGO retrieval -> anomaly scoring -> explained visual response. |
| Build philosophy | Prefer a small reliable pipeline over a broad platform with unfinished integrations. |
| Evidence rule | Do not claim parser accuracy, anomaly validation, or impact until the result has been run and recorded. |

## 2. Problem and evidence

ARGO data provides vertically resolved ocean observations, but the official workflow commonly involves profile files, NetCDF variables, adjusted values, and quality-control flags [E1][E2]. INCOIS and other Argo services provide authoritative access, while selection and visualization tools help users find and download observations [E3][E4]. The remaining product gap is not data availability; it is a lightweight, answer-oriented workflow that joins plain-language access, transparent anomaly context, and answer-specific data sufficiency.

| **Root cause** | **User pain** | **Product response** |
| --- | --- | --- |
| Technical data formats and QC conventions | Non-specialists cannot quickly answer a simple location/time question. | Preprocess once; expose a narrow query contract. |
| Existing tools emphasize selection, files, or plots | Users must manually connect the data, context, and meaning. | Return one complete response with data, chart, map, and explanation. |
| Anomaly logic is often analyst-facing | A flag can look authoritative without baseline or sample context. | Show baseline, z-score meaning, profile count, radius, and confidence. |
| External AI can fail or return malformed output | A live demo becomes dependent on one network call. | Use one LLM parser with a deterministic rule-based fallback. |

## 3. Users and priority scenarios

| **User** | **Immediate need** | **Pinned scenario** |
| --- | --- | --- |
| Forecaster | Quick first read before deeper operational analysis | Temperature profile near Mumbai in July 2024 |
| Researcher | Rapid exploration of a long time series and unusual periods | SST time series at 19N, 72.8E for 2015-2024 |
| Student | Defensible access to real observations without an xarray learning curve | Average salinity in the Bay of Bengal in 2023 |
| Policy analyst | A result that states source, method, and confidence | Explain why a value is unusual and how much data supports it |

## 4. Scope boundaries

### 4.1 Must ship

- A single chat screen with an input, suggested queries, loading/error states, and one result area.
- Three query types: depth profile, regional average, and time series.
- Temperature, salinity, and a clearly disclosed shallow-water SST proxy using the shallowest value at or above the chosen cutoff.
- Preprocessed ARGO data in Parquet, plus separate production and validation baseline tables.
- Optional anomaly scoring using a transparent monthly regional z-score.
- Data-sufficiency output on every successful response and confidence-aware anomaly presentation.
- Friendly no-data, parse-error, and general-error responses.
- A rule-based parsing fallback and a visible degraded-mode disclosure.

### 4.2 Explicit non-goals for the first release

- No user accounts, authentication, persistent chat history, or multi-turn memory.
- No database server; use versioned Parquet/CSV artifacts for the read-only demo dataset.
- No LangChain, fine-tuning, vector database, agent framework, or multiple LLM providers.
- No Isolation Forest or deep-learning anomaly detector; the statistical baseline is the explainable proof.
- No fishing-zone, cyclone, wave-height, multilingual, mobile-app, or WhatsApp integrations during the core build.
- No unsupported claim that the solution is first, unique, production-ready, or validated until evidence exists.

## 5. Functional requirements

| **ID** | **Requirement** | **Acceptance evidence** |
| --- | --- | --- |
| FR-01 | Parse a free-text query into query type, location, parameter, dates, and anomaly intent. | Recorded parser output for the evaluation set. |
| FR-02 | Use a deterministic fallback after LLM timeout, failure, or malformed output. | Forced-timeout test returns parser_used=rule_based. |
| FR-03 | Retrieve profile, regional-average, and time-series data from the prepared subset. | One passing fixture and one real pinned query for each type. |
| FR-04 | Compute z-score anomaly context only from the production baseline. | Unit tests cover thresholds and zero/insufficient standard deviation. |
| FR-05 | Return profile count, search radius, and low/medium/high confidence. | Contract test verifies every data response. |
| FR-06 | Suppress colored severity when confidence is low. | Frontend component tests cover all confidence tiers. |
| FR-07 | Explain source, aggregation, radius, time range, baseline, and proxy caveats. | Pinned responses contain complete explanation text. |
| FR-08 | Render a chart and map pin appropriate to the returned query type. | Projector-size browser check for three pinned queries. |
| FR-09 | Convert failures into typed, friendly messages without internal traces. | End-to-end tests for no_data, parse_error, general_error. |

## 6. Simple technical architecture

> **Recommended stack:** React + TypeScript frontend; FastAPI backend; pandas/xarray preprocessing; Parquet read model; NumPy z-score analytics; Plotly.js and Leaflet; one structured-output LLM API with a Python fallback parser; one container deployment.

| **Layer** | **Choice** | **Reason for a small team** |
| --- | --- | --- |
| Web UI | React + TypeScript (Vite) | Fast component development and typed API handling. |
| Charts/maps | Plotly.js + Leaflet | Mature, editable visualizations with little custom graphics code. |
| API | FastAPI + Pydantic | Small endpoint surface and explicit request/response validation. |
| Offline data | Python, pandas, xarray | Direct support for NetCDF preprocessing and tabular checks. |
| Serving data | Parquet | Fast local reads, no database setup or maintenance. |
| Anomaly | NumPy z-score + precomputed baselines | Explainable, testable, and cheap at request time. |
| Query parsing | One LLM API + rule fallback | Natural language without making the demo depend on the network. |
| Deployment | Single container / Hugging Face Space | One artifact to start and verify. |

### 6.1 Request flow

1. The browser sends POST /chat with one query string.
1. The backend asks the selected LLM for a strict JSON parse and validates the result with Pydantic.
1. On timeout, malformed JSON, or provider failure, the rule parser extracts supported cities, coordinates, dates, parameters, and query type.
1. The data service filters the local Parquet data by space, time, depth, and parameter, then prepares chart-ready arrays.
1. If anomaly intent is present and the baseline is sufficient, the analytics service computes a z-score against the correct region and calendar month.
1. The response composer adds plain-language method, source, proxy caveat, and data-sufficiency information.
1. The frontend renders the summary, chart, map, anomaly state, explanation, and fallback disclosure as one complete result.

## 7. Component responsibilities

| **Component** | **Owns** | **Must not own** |
| --- | --- | --- |
| Chat page | Input state, suggested queries, request state, result layout | Scientific calculations or parsing rules |
| Parser service | LLM call, schema validation, timeout, fallback | Data access or UI wording |
| Data repository | Spatial/temporal/depth filters and aggregations | Anomaly labels or HTTP concerns |
| Baseline builder | Production and validation mean/std/count tables | Live request handling |
| Anomaly service | z-score, thresholds, insufficient-baseline outcome | UI color decisions |
| Explanation service | Template-based method and caveat text | Unverified claims or invented values |
| API route | Orchestration, response validation, typed error mapping | Heavy data preprocessing |
| Anomaly badge | Confidence-aware visual state | Recomputing confidence or the anomaly |

## 8. Data design and governance

### 8.1 Prepared profile table

| **Field** | **Type** | **Rule** |
| --- | --- | --- |
| float_id | string | Stable float identifier |
| time | UTC datetime | Validated and normalized during preprocessing |
| lat / lon | float | Degrees; reject out-of-range values |
| depth_m | float | Non-negative; derive consistently from pressure if needed |
| temperature_c | float/null | Use adjusted value when available and acceptable QC |
| salinity_psu | float/null | Use adjusted value when available and acceptable QC |
| qc flags | string/int | Retain provenance and exclude unacceptable measurements |

### 8.2 Baseline table

| **Field** | **Meaning** |
| --- | --- |
| region_id | Named region or deterministic spatial cell used consistently at build and request time. |
| month | Calendar month 1-12. |
| parameter | temperature, salinity, or shallow SST proxy. |
| baseline_type | production or validation; never interchangeable. |
| period_start / period_end | Exact years used so the explanation can state the baseline honestly. |
| mean / std / n | Statistics and supporting profile count. |
| dataset_version | Hash or release label for reproducibility. |

> **Data integrity rule:** Keep the 2015-2018 validation baseline separate from the full-history production baseline. Validation tests a known event; production serves user queries. Mixing them invalidates both the evidence and the live explanation.

## 9. API contract

### 9.1 Request

{"query": "Plot SST time series at 19N, 72.8E for 2015-2024 and tell me if it is unusual"}

### 9.2 Successful response fields

| **Field** | **Required** | **Purpose** |
| --- | --- | --- |
| summary | Yes | Plain-language restatement of what was answered. |
| query_type | Yes | profile, regional_average, or time_series. |
| params | Yes | Validated location, parameter, and date window. |
| data | Yes | Chart-ready arrays or aggregate value. |
| anomaly | Conditional | Score, label, baseline metadata, and explanation. |
| answer_explanation | Yes | Source, method, radius, time range, and proxy caveat. |
| data_sufficiency | Yes | Profile count, radius, and confidence. |
| parser_used | Yes | llm or rule_based. |
| source | Yes | Dataset label such as INCOIS ARGO. |

### 9.3 Error contract

| **Type** | **When** | **User-facing guidance** |
| --- | --- | --- |
| parse_error | Both parsers cannot create a valid supported query. | Show a working example and request a location/date/parameter. |
| no_data | The query is valid but no acceptable observations match. | Suggest a wider radius or different period. |
| general_error | Unexpected internal failure. | Invite retry/rephrase; log details server-side only. |

## 10. Query parsing

- Ask the LLM to return only the supported schema. Reject extra query types and unknown parameters.
- Set a short timeout and allow only one retry if it does not threaten demo latency.
- Validate latitude, longitude, dates, enum values, and date order before data access.
- The fallback parser supports explicit coordinates, a small Indian coastal city gazetteer, one year or year ranges, parameter keywords, and anomaly intent keywords.
- Always return parser_used. The UI displays a subtle simplified-matching disclosure for fallback results.
- Measure parser accuracy on a labeled 20-25 query set and report the observed value, not an assumed target.

## 11. Anomaly and confidence logic

> **Formula:** z = (current aggregated value - baseline mean) / baseline standard deviation. Skip scoring when the baseline standard deviation is zero or supporting data is insufficient.

| **Condition** | **Label** | **Presentation** |
| --- | --- | --- |
| abs(z) < 1.5 | normal | Green only when response confidence is medium or high. |
| 1.5 <= abs(z) < 2.5 | mild positive/negative | Amber; add provisional qualifier for medium confidence. |
| abs(z) >= 2.5 | strong positive/negative | Red; still explain baseline and sample size. |
| 1-5 matching profiles | low confidence | Neutral 'not enough data to assess'; suppress severity color. |
| 6-20 matching profiles | medium confidence | Show severity as provisional. |
| 21+ matching profiles | high confidence | Show severity at full visual weight. |

These thresholds are project policy, not a universal scientific standard. The final implementation must state them in documentation and verify that they match the data density of the selected subset.

## 12. User experience and accessibility

| **State** | **What the user sees** |
| --- | --- |
| Empty | One input, four suggested questions, short statement of supported data and regions. |
| Loading | Disabled submit and a simple progress state; no partial result without its confidence context. |
| Success | Summary, chart, map, anomaly state when requested, method explanation, and data sufficiency. |
| Fallback parser | The normal result plus a subtle simplified-matching disclosure. |
| No data | Clear reason and a suggestion to broaden the location or time range. |
| Parse error | A supported example query; no technical error details. |
| General error | A safe retry/rephrase message. |

- Use text and icons in addition to anomaly colors.
- Make input, query chips, submit, and chart controls keyboard accessible.
- Provide a text summary that conveys the same conclusion as the chart.
- Use responsive width and test the exact laptop/projector setup used for judging.

## 13. Validation and testing strategy

| **Level** | **Minimum checks** | **Evidence artifact** |
| --- | --- | --- |
| Preprocessing | Schema, ranges, timestamps, QC filtering, duplicate profiles, missing values | Data validation report and sample rows |
| Repository | Spatial, time, depth filters and all three aggregations | Unit tests against deterministic fixtures |
| Parser | Valid, ambiguous, malformed, city, coordinate, missing-date queries | Labeled eval set and measured accuracy |
| Anomaly | Threshold boundaries, negative values, zero std, insufficient baseline | Unit tests and validation script output |
| API | Response schema, timeout fallback, typed errors, no stack traces | Contract/integration test report |
| Frontend | All confidence tiers, chart types, empty/loading/error/fallback states | Component tests plus browser screenshots |
| Demo | Three pinned queries repeated on presentation network and machine | 20-run checklist and cached fallback |

> **Pitch evidence gate:** The heatwave result and parser accuracy may enter the presentation only after the exact command, dataset version, output, date, and owner are recorded. A negative result is acceptable; a placeholder result is not.

## 14. Deployment and demo runbook

1. Build and version the processed Parquet files and baseline tables before deployment.
1. Build the React frontend and serve it with the FastAPI application from one container where practical.
1. Store the selected LLM key only in the hosting platform secret settings; never in the deck, video, or frontend bundle.
1. Run a health check and all three pinned queries after each deployment.
1. Capture the exact successful JSON and screenshots for offline fallback.
1. Before judging, open the app, warm the service, verify the network, and keep the cached demo ready in a separate tab.
1. If the live LLM fails, allow the rule parser to continue and explain the disclosure honestly.

## 15. Security, privacy, and responsible claims

- The first release stores no accounts, personal profiles, or chat history.
- Treat every query as untrusted text; do not execute it, use it as a file path, or insert it into generated code.
- Keep API keys server-side and remove secrets from screenshots and screen recordings.
- Return sanitized error messages and keep detailed logs private.
- Name data sources and transformations; do not imply satellite SST when using a shallow ARGO proxy.
- Use 'target', 'planned', or 'to be validated' for metrics not yet measured.
- For first-round materials, use only Team ID, Team Name, and Member 1/2 labels; do not reveal personal or institutional identity.

## 16. Key risks and decisions

| **Risk** | **Trigger** | **Response** |
| --- | --- | --- |
| ARGO ingestion delay | No query-ready subset by the agreed checkpoint | Switch to a pre-vetted subset that covers the pinned queries; label it internally. |
| Sparse observations | Low matching profile count or baseline n | Increase radius only within documented limits or return low confidence; never force a colored anomaly. |
| LLM instability | Timeout, quota, malformed JSON | Use deterministic fallback; avoid adding a second provider during the sprint. |
| Validation misses known event | No region exceeds the defined threshold | Report honestly, inspect data/region, or select another real event under a fixed time box. |
| Scope overrun | Integration incomplete by the hardening checkpoint | Cut regional average first, then map interactivity; keep profile and time-series+anomaly. |
| Unsupported claims | Metric has no stored run artifact | Remove from deck/video or label as a target. |

## 17. Definition of done

- The source and license/provenance of the chosen ARGO subset are recorded.
- Production and validation baselines are versioned separately.
- All three query types work against real or clearly labeled fallback data.
- Every successful response includes method and data-sufficiency context.
- All failure paths are friendly and reveal no internal details.
- The parser eval and anomaly validation outputs are recorded without edited numbers.
- The web experience has been checked on the presentation laptop at projector scale.
- Three pinned queries have 20 successful rehearsals or a documented failure rate and mitigation.
- The slide deck contains exactly nine slides, traceable citations, and no personal/institutional identity.
- A cached offline demonstration exists and contains no credentials or private data.

## 18. Open decisions for the team

| **Decision** | **Recommended default** | **Owner / deadline** |
| --- | --- | --- |
| Live LLM provider | Choose one after a quota and latency test; keep the interface provider-neutral. | Tech lead, before parser integration |
| Region definitions | Use explicit documented boxes or cells that match baseline generation. | Data + anomaly owners, before preprocessing |
| Error HTTP status policy | Use standard HTTP status codes with the same typed error body. | Backend owner, before contract freeze |
| Chip behavior | Populate input first; allow the presenter to submit deliberately. | Frontend owner, before UI polish |
| Fallback subset | Prepare it before the main ingestion deadline and ensure all pinned queries are covered. | Data owner, before the sprint |

## 19. References and source pack

1. [E1] Argo Program. 'Argo data sources.' https://argo.ucsd.edu/data/ (accessed 14 August 2026).
1. [E2] Argo Program. 'How to use Argo profile files.' https://argo.ucsd.edu/data/how-to-use-argo-files/ (accessed 14 August 2026).
1. [E3] INCOIS. 'INDIAN ARGO Floats Data' ERDDAP dataset. https://erddap.incois.gov.in/erddap/tabledap/Indian_ARGO_Floats.html (accessed 14 August 2026).
1. [E4] Euro-Argo RISE. 'Report on new products - D7.14 v1.1.' https://www.euro-argo.eu/content/download/157270/file/D7.14_v1.1.pdf (accessed 14 August 2026).
1. [E5] Kelley, D. E. et al. (2021). 'argoFloats: An R Package for Analyzing Argo Data.' Frontiers in Marine Science 8:635922. https://doi.org/10.3389/fmars.2021.635922.
1. [E6] Holbrook, N. J. et al. (2019). 'A global assessment of marine heatwaves and their drivers.' Nature Communications 10, 2624. https://doi.org/10.1038/s41467-019-10206-z.
1. Project source pack supplied by the team: prd.md, architecture.md, design.md, feature.md, phases.md, todo.md, and FloatChat-Lite_Master_v3.md.
1. Submission rules supplied by the team: First_Round_Shortlisting_Rubric_PPT_Video_Guidelines.pdf and SIH Internal Template.pptx.
