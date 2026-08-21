# FloatChat-Lite — Product Requirements Document

> **Status:** Draft | **Last updated:** 21 August 2026 (rev. B — QC-filter path, evidence grading, and quantitative evaluation added post-review) | **Owner:** Swarangi Limaye / SIH26 Team

## 1. Overview
FloatChat-Lite is an explainable conversational assistant for exploring Indian Ocean ARGO float data. Users ask natural-language questions about ocean temperature and salinity, and the system returns a plain-language answer, an interactive chart and map, and — where relevant — a data-backed anomaly flag with a clear explanation of how it was computed. It matters now because ARGO data is scientifically valuable but locked behind technical formats (NetCDF, scientific portals), and prior hackathon attempts (SIH25040, 2025) exposed raw data without anomaly awareness or explainability, undermining trust.

## 2. Problem Statement
Oceanographic ARGO data covering the Indian Ocean is publicly available but effectively inaccessible to non-specialists. Forecasters, researchers, students, and policy analysts currently must learn NetCDF/xarray tooling — a process that can take weeks — before they can ask even a simple question like "what was the temperature near Mumbai last July?" Even when analytics exist, anomaly detection is typically a back-end-only process invisible to the end user, and AI-generated answers rarely explain their own reasoning, which erodes trust in high-stakes domains like climate and policy. The 2025 cohort of FloatChat teams demonstrated basic query-to-chart pipelines but did not address anomaly flagging, explainability, or data sufficiency — leaving a clear, evidenced gap this project targets.

## 3. Goals
- Let a non-expert user retrieve and understand Indian Ocean ARGO temperature/salinity data using natural language, with no NetCDF/xarray knowledge required.
- Surface unusual ocean conditions (anomalies/trends) automatically, using a transparent, explainable statistical method rather than a black box.
- Make every answer and every anomaly flag independently explainable: data source, computation method, and a plain-language "why," including how much data backs the answer.
- Ship a working, rehearsed, judge-ready demo within a 48-hour hackathon window without deferring core explainability or anomaly features to "future work."

## 4. Non-Goals
- Multilingual support (Hindi, Marathi, Tamil, etc.) — deferred to Phase 2 (post-hackathon).
- Integration with fishing zone advisories, cyclone tracks, or wave-height data (INCOIS PFZ, IMD, MACHLI app) — future scope only.
- Multi-turn conversational memory / follow-up questions — queries are stateless by design for this build.
- Production-grade authentication, multi-user accounts, or a persistent database (MongoDB, etc.) — out of scope for a 2-day build.
- Fine-tuning an LLM — a prompted pre-trained model is used instead, evaluated against a small test set rather than trained.
- Advanced ML anomaly detection (e.g., Isolation Forest) — a Z-score-vs-climatology model is used instead, by deliberate scope decision.

## 5. Target Users / Personas
| Persona | Description | Primary need |
|---|---|---|
| Climate & Weather Forecaster | Works at IMD, INCOIS, or NCMRWF; uses ocean data for monsoon/cyclone prediction | A fast, trustworthy first read on ocean conditions before running complex models |
| Oceanographer / Researcher | At INCOIS, NIO, IITs, IISc, or C-MMACS; studies Indian Ocean dynamics | Quick exploration of profiles/trends without weeks of NetCDF/xarray setup |
| University Student | Doing coursework or thesis work on ocean temperature/salinity trends | Accessible entry point into real ARGO data for academic work |
| Policy Analyst | At MoES, NITI Aayog, NDMA, or a state coastal authority | Fast, defensible ocean-condition insights without waiting on a scientist |

## 6. User Stories
- As a forecaster, I want to ask "Show temperature profile near Mumbai in July 2024," so that I get an instant depth-profile chart instead of digging through NetCDF files.
- As a researcher, I want to ask "Plot SST time series at 19N, 72.8E for 2015–2024 and tell me if it's unusual," so that I can quickly spot anomalous periods worth deeper investigation.
- As a student, I want to ask "Average salinity in Bay of Bengal in 2023," so that I can pull a defensible regional figure for coursework without learning xarray.
- As a policy analyst, I want every anomaly flag to explain its baseline and Z-score in plain language, so that I can trust and cite the result without needing a statistics background.
- As any user, I want to be told how many ARGO profiles back an answer, so that I know whether to treat a result as precise or merely indicative.
- As any user, I want a friendly message instead of a raw error when my query can't be parsed or no data exists, so that I'm not stuck guessing what went wrong.

## 7. Requirements

### 7.1 Functional Requirements
1. The system must accept a free-text natural-language query and parse it into a structured query (`query_type`, `lat`, `lon`, `parameter`, `date_from`, `date_to`, `include_anomaly`) using an LLM parser.
2. The system must fall back to a rule-based parser (city gazetteer + regex) if the LLM call fails or times out, and must tag every response with `parser_used: "llm" | "rule_based"`.
3. The system must support three query types: single-location depth `profile`, `regional_average`, and `time_series`.
4. The system must retrieve matching ARGO data (temperature and/or salinity) from preprocessed CSV/Parquet files and return it as chart-ready data.
5. Before any anomaly scoring, the system must filter retrieved ARGO observations through a **QC Filter (data-quality path)**: exclude records marked bad by the ARGO quality-control flag, and prefer adjusted/delayed-mode data over raw real-time data for historical analysis. This is a distinct pipeline stage from anomaly scoring, not a combined step — a strange value can be a sensor/profile error rather than a real event, and must be caught before it reaches the anomaly model.
6. If too few valid observations remain after QC filtering, the system must set a `data_quality_warning` flag and the frontend must surface it, rather than silently scoring thin or unfiltered data.
7. On QC-passed data only, the system must compute an anomaly score (`z = (x − μ) / σ` vs. a precomputed regional/monthly climatology baseline) when a query implies or requests anomaly assessment, and must classify it as `normal`, `mild_positive`, `mild_negative`, `strong_positive`, or `strong_negative`. Results must be labeled "upper-ocean temperature anomaly" or "salinity anomaly" — never "marine heatwave," since that term requires daily SST above a seasonally varying percentile threshold for a sustained duration, a different method than sparse-profile Z-scoring.
8. The system must return an **evidence grade** — `Insufficient`, `Indicative`, or `Supported` — computed from valid profile count, baseline sample size, distinct float count, and QC pass rate together (not from profile count alone). This field replaces the previous `data_sufficiency.confidence` (`low`/`medium`/`high`) tiering.
   - **Insufficient:** fewer than 5 valid current profiles, or too few baseline observations.
   - **Indicative:** enough observations to score, but limited spatial coverage (e.g., too few distinct floats).
   - **Supported:** sufficient valid profiles, sufficient baseline `n`, multiple distinct floats, and acceptable QC pass rate, all at once.
9. The system must suppress the colored anomaly severity badge and show a neutral "not enough data to assess" state whenever `evidence_grade` is `"Insufficient"`, and must show a "provisional" qualifier when `"Indicative"`.
10. The system must return a real, expandable **"Why this result?" evidence panel** containing actual computed values and provenance (e.g., valid profile count, distinct float IDs, current-period mean, baseline mean/std/n, QC rule applied, Z-score) — not a natural-language template with no underlying numbers. This is documented as **computation transparency / provenance reporting**, never described as explainable AI (SHAP/LIME-style model attribution) unless that technique is actually added.
11. The system must return an `answer_explanation` field describing the data source, aggregation method, and any proxy assumptions (e.g., SST derived from the shallowest measurement ≤10m).
12. The system must return friendly, specific error messages for `no_data`, `parse_error`, and `general_error` cases — never a raw stack trace or generic failure.
13. The frontend must render, for every response: a query summary header, a chart (Plotly.js), a map pin (Leaflet), an anomaly badge (when applicable), and an evidence panel (expandable) with a data-sufficiency line.
14. The frontend must display a visible disclosure line when `parser_used == "rule_based"`, informing the user the query was parsed in a simplified/degraded mode.
15. The anomaly model's production baseline must be computed once during preprocessing from the full available pre-query-year history (target 8–9 years) per region/month, and must never be conflated with the shorter 2015–2018 validation-only baseline used in `validate_heatwave.py`.
16. The team must produce one reproducible evaluation notebook that, on a fixed ARGO subset and a fixed set of prompts/regions, compares three methods — (a) a simple regional-average baseline, (b) an unfiltered Z-score with no QC or evidence grading, and (c) FloatChat-Lite's full QC-filtered, evidence-graded pipeline — and reports precision, recall, F1, false-alert rate, query coverage, and response time for each. No claimed accuracy or precision figure may appear in the pitch or report unless it was produced by this notebook.
17. The team must produce an LLM-parser reliability test covering: parsing success/invalid-output rate over 20–30 paraphrased queries, rule-based fallback behavior with the LLM explicitly disabled (not just failing), average and p95 response latency over repeated requests, and behavior under no-data, sparse-data, malformed-date, and simulated API-failure conditions.

### 7.2 Non-Functional Requirements
- **Explainability:** every answer and every anomaly flag must be explainable in plain language without requiring the user to understand Z-scores or statistics — with the underlying computed values available in the evidence panel for anyone who wants them.
- **Scientific integrity:** anomaly detection must never conflate a data-quality issue with a genuine oceanographic event; the QC Filter stage is mandatory and cannot be bypassed for any query type that includes anomaly scoring.
- **Honesty over polish:** no unverified claim (e.g., heatwave validation result, LLM parsing accuracy, anomaly precision/recall) may be presented in the demo/pitch unless it has been run and recorded against real output from the evaluation notebook (FR16) or reliability test (FR17); placeholder numbers are explicitly banned.
- **Resilience:** the demo must survive a live infrastructure hiccup via a cached fallback (screenshots or precomputed JSON responses) for the three pinned demo queries.
- **Latency:** anomaly scoring must use precomputed baselines (no live heavy computation) to keep responses fast enough for a live demo; p95 latency must be measured, not assumed (FR17).
- **Reliability of core flow:** the three pinned demo queries must be rehearsed 20+ times and work reliably before presentation.
- **Simplicity/maintainability:** the stack deliberately avoids LangChain, MongoDB, Isolation Forest, and multi-turn memory to minimize failure surface within the 48-hour build window.

## 8. Success Metrics
| Metric | Target | Timeframe |
|---|---|---|
| Pinned demo queries working reliably | 3 of 3 (profile, time-series+anomaly, regional average) | By end of Day 2, hour 5 |
| Heatwave validation check completed | `validate_heatwave.py` run and result recorded (flagged or honestly not-flagged) | By Day 1, hour 5 |
| Evaluation notebook completed (FR16) | Precision/recall/F1/false-alert rate/coverage/latency recorded for all 3 compared methods | By Day 2, before pitch |
| LLM parser reliability test completed (FR17) | Real parsing success rate, invalid-output rate, and p95 latency reported (no target inflated pre-measurement) | By Day 2, before pitch |
| Demo rehearsal reps on pinned queries | 20+ full run-throughs | Before final presentation |
| Judge comprehension of architecture + explainability value | Judges can restate the QC → anomaly → evidence-grade → provenance pipeline and why each stage exists, in post-demo Q&A | Live judging session |

## 9. Constraints & Assumptions
- **Constraint:** total build time is 48 hours across a 6-person team; anything not shippable in that window is explicitly deferred (see Non-Goals).
- **Constraint:** ARGO data must be sourced from INCOIS and preprocessed from NetCDF into CSV/Parquet before the demo; no live NetCDF parsing at query time.
- **Constraint:** deployment target is Hugging Face Spaces, following the precedent set by SIH25040 (2025) teams.
- **Assumption:** a prompted pre-trained LLM (GPT-4o-mini / Claude 3.5 / Ollama Llama 3.1) is sufficient for the fixed query schema without fine-tuning.
- **Assumption:** a Z-score-vs-climatology model is statistically sufficient and easier to explain to judges than a more complex anomaly detector.
- **Assumption:** ARGO floats' shallowest reported depth bin (2–10m) can serve as a reasonable SST proxy when explicitly disclosed as such.
- **Assumption:** if real ARGO ingestion is not query-ready by Day 1, hour 4, the team will fall back to a small pre-vetted subset (1–2 regions, 2 years) rather than delay the whole build.

## 10. Dependencies
- **INCOIS** (Indian National Centre for Ocean Information Services) — source of ARGO float NetCDF data (temperature, salinity, pressure/depth, lat/lon, time), 2015–2024 subset.
- **LLM API provider** (OpenAI GPT-4o-mini, Anthropic Claude, or a locally hosted Ollama Llama 3.1) — powers the primary query parser.
- **Hugging Face Spaces** — hosting/deployment target for the demo.
- **Plotly.js** and **Leaflet** — frontend charting and mapping libraries.
- **FastAPI, pandas, numpy, xarray, scikit-learn** — backend data processing and anomaly-scoring stack.

## 11. Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ARGO NetCDF-to-Parquet ingestion isn't query-ready in time | Medium | High | Hour-4 Day-1 checkpoint; pre-vetted fallback subset (1–2 regions, 2 years) kept ready as a swap-in |
| 2019 heatwave validation doesn't actually flag as anomalous | Medium | Medium | Honest reporting, region widening, or swapping to a different real event, time-boxed to 1 hour on Day 2 morning — never a placeholder number |
| LLM parser fails or times out live during the demo | Low–Medium | High | Rule-based fallback parser with city gazetteer, always tagged `parser_used`, disclosed in the UI |
| Anomaly badge shown on statistically thin data, misleading judges | Medium | Medium | Badge suppressed and replaced with a neutral "not enough data" state whenever confidence is low |
| Schedule overrun eats into testing/rehearsal time | Medium | High | Day 2 hours 5–7 are protected time; if Day 1 overruns 2+ hours, cut `regional_average` query type first, never rehearsal time |
| Unbenchmarked accuracy or validation claims get cited in the pitch by mistake | Low | High | All such claims explicitly gated behind Section 17-style resolution log / checklist ownership (Member 3) before pitch finalization |

## 12. Open Questions
- [ ] Which LLM provider (GPT-4o-mini vs. Claude 3.5 vs. local Ollama) will be used for the live demo, and is API quota/latency confirmed for demo day?
- [ ] What is the final confirmed number of years in the production baseline (8 vs. 9) once real data volume is known?
- [ ] Will the fallback ARGO subset (if triggered) cover the same regions used in the three pinned demo queries?
- [ ] Who validates the LLM parser eval set (Appendix D) — is this Member 3, Member 4, or shared?
