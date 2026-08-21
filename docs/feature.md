# FloatChat-Lite — Feature List

> **Status:** Draft | **Last updated:** 13 August 2026

## Feature Summary

| # | Feature | Category | Phase | Priority | Status |
|---|---|---|---|---|---|
| 1 | ARGO Data Ingestion & Preprocessing | Data Pipeline | Phase 1 | Must-have | Planned |
| 2 | Anomaly Baseline Precomputation | Data Pipeline | Phase 1 | Must-have | Planned |
| 3 | Heatwave Validation Check | Validation | Phase 1 | Must-have | Planned |
| 4 | Chat UI Shell | Frontend | Phase 2 | Must-have | Planned |
| 5 | Suggested Query Chips | Frontend | Phase 2 | Should-have | Planned |
| 6 | Natural Language Query Parsing (LLM) | Query Parsing | Phase 3 | Must-have | Planned |
| 7 | Rule-Based Fallback Parser | Query Parsing | Phase 3 | Must-have | Planned |
| 8 | Profile Query (Depth Profile) | Data Retrieval | Phase 3 | Must-have | Planned |
| 9 | Regional Average Query | Data Retrieval | Phase 3 | Must-have | Planned |
| 10 | Time-Series Query | Data Retrieval | Phase 3 | Must-have | Planned |
| 11 | Anomaly Detection (Z-score Scoring) | Anomaly Detection | Phase 3 | Must-have | Planned |
| 12 | Data Sufficiency Indicator | Explainability | Phase 3 | Must-have | Planned |
| 13 | Answer Explainability Text | Explainability | Phase 3 | Must-have | Planned |
| 14 | Friendly Error Handling | Reliability | Phase 3 | Must-have | Planned |
| 15 | Confidence-Aware Anomaly Badge | Frontend / Explainability | Phase 4 | Must-have | Planned |
| 16 | Degraded-Mode Disclosure | Frontend | Phase 4 | Should-have | Planned |
| 17 | LLM Parser Eval Set | QA | Phase 5 | Should-have | Planned |
| 18 | Cached Demo Fallback | Reliability | Phase 5 | Must-have | Planned |

*Priority: Must-have / Should-have / Nice-to-have. Status: Planned / In progress / Done.*

---

## 1. ARGO Data Ingestion & Preprocessing
**Category:** Data Pipeline
**Phase:** Phase 1
**Priority:** Must-have

**What it does:**
Converts raw ARGO NetCDF files from INCOIS into query-able CSV/Parquet tables of temperature and salinity profiles.

**User story:**
As any user, I want the system to have real ARGO data ready before I ask a question, so that my query returns an actual answer instead of an error.

**How it works:**
1. Trigger: run offline, before the live demo, as a one-time data-prep script.
2. Logic: load NetCDF files for the Indian Ocean region (2015–2024 subset), extract `float_id`, `time`, `lat`, `lon`, `depth`, `temperature`, `salinity`, and write to Parquet/CSV.
3. Result: a preprocessed dataset the Data Layer can query directly without touching NetCDF at request time.

**Inputs:** Raw ARGO NetCDF files (INCOIS FTP/WWW).

**Outputs:** Preprocessed Parquet/CSV files consumed by `get_profile()`, `get_regional_average()`, `get_time_series()`.

**Edge cases & error handling:**
- Edge case: ingestion not query-ready by Day 1, hour 4 → behavior: switch to a small pre-vetted fallback subset (1–2 regions, 2 years), clearly labeled internally as "fallback subset," decided at the hour-4 checkpoint.

**Dependencies:** None (first step in the pipeline).

---

## 2. Anomaly Baseline Precomputation
**Category:** Data Pipeline
**Phase:** Phase 1
**Priority:** Must-have

**What it does:**
Computes and stores mean/standard-deviation climatology baselines by region and month, split into two distinct baseline sets: a validation baseline (2015–2018) and a production baseline (full available history).

**User story:**
As a researcher, I want anomaly flags to be based on a solid historical baseline, so that "unusual" actually means something statistically.

**How it works:**
1. Trigger: run offline immediately after Feature 1 completes.
2. Logic: group profiles by region and month; compute mean, std, and profile count separately for the 2015–2018 validation window and the full-history production window; persist as a baseline table.
3. Result: two clearly separated baseline sets ready for anomaly scoring — never conflated with each other.

**Inputs:** Preprocessed ARGO dataset (Feature 1).

**Outputs:** Climatology baseline table (region × month × baseline_type → mean, std, n).

**Edge cases & error handling:**
- Edge case: fewer than 5 profiles in a region/month → behavior: baseline for that cell is marked insufficient and anomaly scoring for it returns low confidence / suppressed badge (see Feature 15).

**Dependencies:** Feature 1 (ARGO Data Ingestion & Preprocessing).

---

## 3. Heatwave Validation Check
**Category:** Validation
**Phase:** Phase 1
**Priority:** Must-have

**What it does:**
Tests whether the anomaly model correctly flags the documented 2019 Indian Ocean marine heatwave, using `validate_heatwave.py`, and records the real result for use in the pitch.

**User story:**
As a judge, I want to see that the anomaly model has been tested against a real, known event, so that I can trust the "unusual" flag isn't arbitrary.

**How it works:**
1. Trigger: run manually by Member 3 once baselines (Feature 2) are ready, Day 1 by hour 5.
2. Logic: for each defined region, compute the max |Z-score| in 2019 against the validation baseline (2015–2018); flag as anomalous if max |Z| ≥ 1.5.
3. Result: a printed, recorded outcome per region — either a real flagged Z-score to cite in the pitch, or an honest "not flagged" result requiring a fallback plan (region widening, different event, or honest negative reporting).

**Inputs:** Preprocessed ARGO dataset, validation baseline (2015–2018).

**Outputs:** Recorded validation result (region, max|z|, month, flagged True/False) — never a placeholder number.

**Edge cases & error handling:**
- Edge case: model does not flag the 2019 event as anomalous → behavior: report honestly, widen the region, or pick a different real, checkable event — time-boxed to a maximum of 1 hour on Day 2 morning.
- Error case: insufficient baseline data for a region → behavior: that region is marked "cannot validate" and excluded from pitch claims.

**Dependencies:** Feature 2 (Anomaly Baseline Precomputation).

---

## 4. Chat UI Shell
**Category:** Frontend
**Phase:** Phase 2
**Priority:** Must-have

**What it does:**
Provides the single chat panel — input box and response area — that is the entire user interface for FloatChat-Lite.

**User story:**
As any user, I want a simple chat box to type my question into, so that I don't need to learn a new interface.

**How it works:**
1. Trigger: page load.
2. Logic: renders an empty input box and a response area that stays empty until a query is submitted.
3. Result: user can type a query and submit it (Enter key or a submit button).

**Inputs:** User keystrokes / submit action.

**Outputs:** A submitted query string sent to `POST /chat` (once Feature 6/7 are wired in Phase 3).

**Edge cases & error handling:**
- Edge case: empty submission → behavior: input is not submitted; no request sent.

**Dependencies:** None (can be built against mock data initially, per Phase 2 scope).

---

## 5. Suggested Query Chips
**Category:** Frontend
**Phase:** Phase 2
**Priority:** Should-have

**What it does:**
Shows four example queries below the chat input that a user can click to quickly try the system.

**User story:**
As a first-time user, I want example questions I can just click, so that I don't face a blank box with no idea what to ask.

**How it works:**
1. Trigger: page load (always visible in the empty state).
2. Logic: each chip contains one of the four pinned example queries; clicking a chip populates (and may auto-submit) the input box.
3. Result: the query is submitted through the same flow as a manually typed one.

**Inputs:** User click.

**Outputs:** Populated/submitted query in the Chat UI Shell (Feature 4).

**Edge cases & error handling:**
- None beyond the standard query flow — chips submit exactly like typed queries.

**Dependencies:** Feature 4 (Chat UI Shell).

---

## 6. Natural Language Query Parsing (LLM)
**Category:** Query Parsing
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Converts a free-text question into structured parameters (`query_type`, `lat`, `lon`, `parameter`, `date_from`, `date_to`, `include_anomaly`) using a direct LLM API call.

**User story:**
As a forecaster, I want to ask "Show temperature profile near Mumbai in July 2024" in plain English, so that I don't need to know coordinates or query syntax.

**How it works:**
1. Trigger: backend receives a query via `POST /chat`.
2. Logic: sends the query text to the LLM API with a fixed extraction prompt; expects a JSON object back with the structured fields.
3. Result: structured parameters passed to the Data Layer; response tagged `parser_used: "llm"`.

**Inputs:** Raw query string.

**Outputs:** Structured query object (`query_type`, `lat`, `lon`, `parameter`, `date_from`, `date_to`, `include_anomaly`).

**Edge cases & error handling:**
- Error case: LLM call fails or times out → behavior: control passes to Feature 7 (Rule-Based Fallback Parser).
- Edge case: LLM returns malformed JSON → behavior: treated as a parse failure, falls back to Feature 7.

**Dependencies:** External LLM API (GPT-4o-mini / Claude 3.5 / Ollama Llama 3.1).

---

## 7. Rule-Based Fallback Parser
**Category:** Query Parsing
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Deterministically parses a query using a small city gazetteer, coordinate regex, and keyword matching, when the LLM parser is unavailable.

**User story:**
As any user, I want my query to still get an answer even if the AI parser is down, so that a single point of failure doesn't break the whole demo.

**How it works:**
1. Trigger: Feature 6 fails or times out.
2. Logic: matches lat/lon patterns, checks the query against a fixed city gazetteer (Mumbai, Chennai, Kolkata, Kochi, Visakhapatnam, Goa), extracts year/year-range via regex, and matches keywords for query type, parameter, and anomaly interest.
3. Result: structured parameters passed to the Data Layer; response tagged `parser_used: "rule_based"`, which triggers Feature 16 (Degraded-Mode Disclosure) on the frontend.

**Inputs:** Raw query string.

**Outputs:** Structured query object, same shape as Feature 6's output.

**Edge cases & error handling:**
- Edge case: no city or coordinates found in the query → behavior: `lat`/`lon` remain null, which downstream leads to a `parse_error` response.

**Dependencies:** None external (pure Python, no network calls, by design).

---

## 8. Profile Query (Depth Profile)
**Category:** Data Retrieval
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Returns a depth-vs-value profile (temperature or salinity) for a single location and time window.

**User story:**
As a forecaster, I want to see a temperature profile by depth near a location, so that I get a first read on ocean conditions.

**How it works:**
1. Trigger: `query_type == "profile"` from Feature 6 or 7.
2. Logic: filters the preprocessed dataset (Feature 1) to profiles within a fixed coverage radius of `lat`/`lon` and within the date range; returns depth vs. value pairs.
3. Result: chart-ready `data` object plus `data_sufficiency` (Feature 12) returned in the response.

**Inputs:** `lat`, `lon`, `parameter`, `date_from`, `date_to`.

**Outputs:** `data.depth` / `data.value` arrays; `data_sufficiency` object.

**Edge cases & error handling:**
- Edge case: zero matching profiles → behavior: `no_data` error response (Feature 14).

**Dependencies:** Feature 1 (ARGO Data Ingestion & Preprocessing); Feature 6/7 (parsers).

---

## 9. Regional Average Query
**Category:** Data Retrieval
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Returns an averaged value (e.g., average salinity) across a region and time window.

**User story:**
As a student, I want to ask for the average salinity in the Bay of Bengal in 2023, so that I get a defensible regional figure without manual aggregation.

**How it works:**
1. Trigger: `query_type == "regional_average"` from Feature 6 or 7.
2. Logic: filters the dataset to the specified region and date range; computes the mean of the requested parameter across all matching profiles.
3. Result: a single aggregated value plus `data_sufficiency` (Feature 12) returned in the response.

**Inputs:** Region bounds (or `lat`/`lon` + radius), `parameter`, `date_from`, `date_to`.

**Outputs:** Aggregated value; `data_sufficiency` object.

**Edge cases & error handling:**
- Edge case: zero matching profiles → behavior: `no_data` error response (Feature 14).

**Dependencies:** Feature 1; Feature 6/7 (parsers).

---

## 10. Time-Series Query
**Category:** Data Retrieval
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Returns a time-ordered series of averaged values (e.g., monthly SST) for a location or region across a date range.

**User story:**
As a researcher, I want to plot an SST time series at a coordinate from 2015–2024, so that I can see how it has changed over time.

**How it works:**
1. Trigger: `query_type == "time_series"` from Feature 6 or 7.
2. Logic: filters the dataset to the location/region and date range, groups by month, computes the mean value per month.
3. Result: `data.time` / `data.value` arrays plus `data_sufficiency` (Feature 12) returned in the response; if `include_anomaly` is true, also triggers Feature 11.

**Inputs:** `lat`, `lon`, `parameter`, `date_from`, `date_to`, `include_anomaly`.

**Outputs:** Time-series `data` object; `data_sufficiency` object.

**Edge cases & error handling:**
- Edge case: zero matching profiles → behavior: `no_data` error response (Feature 14).

**Dependencies:** Feature 1; Feature 6/7 (parsers).

---

## 11. Anomaly Detection (Z-score Scoring)
**Category:** Anomaly Detection
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Scores the current queried value against the precomputed production climatology baseline and classifies it as normal, mild, or strong (positive/negative) anomaly.

**User story:**
As a researcher, I want the system to tell me if a value is unusual, so that I can quickly spot anomalous periods worth investigating.

**How it works:**
1. Trigger: `include_anomaly == true`, typically alongside a time-series query (Feature 10).
2. Logic: computes `z_score = (current_value - baseline_mean) / baseline_std` using the production baseline (Feature 2); classifies as `normal` (|z| < 1.5), `mild_positive`/`mild_negative` (1.5 ≤ |z| < 2.5), or `strong_positive`/`strong_negative` (|z| ≥ 2.5).
3. Result: `anomaly` object (score, label, baseline period/mean/std, explanation) added to the response.

**Inputs:** Current aggregated value, region, month.

**Outputs:** `anomaly` object in the response JSON.

**Edge cases & error handling:**
- Edge case: production baseline for that region/month has insufficient data (< 5 profiles) → behavior: anomaly scoring is skipped or returned with low confidence, which suppresses the colored badge on the frontend (Feature 15).

**Dependencies:** Feature 2 (Anomaly Baseline Precomputation); Feature 10 (Time-Series Query) as the typical trigger.

---

## 12. Data Sufficiency Indicator
**Category:** Explainability
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Reports how many ARGO profiles back a given answer and assigns a confidence level (low/medium/high), so users know whether to treat a result as precise or merely indicative.

**User story:**
As a policy analyst, I want to know how much data backs an answer, so that I know whether to treat it as precise or merely indicative.

**How it works:**
1. Trigger: every successful data-backed response (Features 8, 9, 10).
2. Logic: counts matching profiles within the coverage radius; assigns `low` (1–5 profiles), `medium` (6–20), or `high` (21+) confidence.
3. Result: `data_sufficiency` object (`profile_count`, `coverage_radius_km`, `confidence`) included in every data response, and rendered as a line under the chart on the frontend.

**Inputs:** Matching profile count from the data retrieval step.

**Outputs:** `data_sufficiency` object in the response JSON.

**Edge cases & error handling:**
- Edge case: `confidence == "low"` and an anomaly was also computed → behavior: the frontend suppresses the colored anomaly badge (Feature 15) regardless of the anomaly label.

**Dependencies:** Features 8, 9, or 10 (whichever query type ran).

---

## 13. Answer Explainability Text
**Category:** Explainability
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Generates a plain-language description of the data source, aggregation method, and any proxy assumptions behind an answer (e.g., the SST-from-shallowest-measurement proxy).

**User story:**
As a policy analyst, I want every answer to explain its baseline and method in plain language, so that I can trust and cite the result without needing a statistics background.

**How it works:**
1. Trigger: every successful data-backed response.
2. Logic: assembles a fixed-template explanation string referencing the data source (INCOIS ARGO), the aggregation method used (e.g., "monthly mean of all profiles within 50km"), and any proxy caveats (e.g., the ≤10m SST depth cutoff).
3. Result: `answer_explanation` string included in the response and rendered in the explanation footer.

**Inputs:** Query parameters, aggregation method used, any proxy flags triggered.

**Outputs:** `answer_explanation` string in the response JSON.

**Edge cases & error handling:**
- None beyond standard template assembly — this feature does not fail independently of the underlying data retrieval.

**Dependencies:** Features 8, 9, or 10 (whichever query type ran); Feature 11 if an anomaly was also computed (adds the anomaly-specific "why" text).

---

## 14. Friendly Error Handling
**Category:** Reliability
**Phase:** Phase 3
**Priority:** Must-have

**What it does:**
Converts every backend failure mode into one of three friendly, specific messages (`no_data`, `parse_error`, `general_error`) instead of a raw error.

**User story:**
As any user, I want a friendly message instead of a raw error when my query can't be parsed or no data exists, so that I'm not stuck guessing what went wrong.

**How it works:**
1. Trigger: any failure point in the pipeline (both parsers fail, zero matching data, or an unexpected exception).
2. Logic: catches the failure type and maps it to the appropriate message: `parse_error` (neither parser could understand the query), `no_data` (parsed fine but no matching ARGO data), `general_error` (unexpected backend failure).
3. Result: a friendly, specific message rendered in the response area in place of the chart.

**Inputs:** Failure signal from any upstream component (parsers, Data Layer, Anomaly Model).

**Outputs:** One of three typed error responses, rendered conversationally on the frontend.

**Edge cases & error handling:**
- Edge case: an unexpected exception type not anticipated by the mapping → behavior: defaults to `general_error`, never exposes a stack trace.

**Dependencies:** Features 6/7 (parsers), Features 8/9/10 (data retrieval).

---

## 15. Confidence-Aware Anomaly Badge
**Category:** Frontend / Explainability
**Phase:** Phase 4
**Priority:** Must-have

**What it does:**
Renders the anomaly severity as a colored badge, but suppresses the color and shows a neutral "not enough data to assess" state whenever `data_sufficiency.confidence` is low.

**User story:**
As a researcher, I want anomaly flags to be honest about how much data backs them, so that I don't over-trust a flag based on very little data.

**How it works:**
1. Trigger: response includes both an `anomaly` object and a `data_sufficiency` object.
2. Logic: if `confidence == "low"`, render a neutral gray badge with "Not enough data to assess (N profiles within Xkm)," overriding the anomaly label entirely; if `"medium"`, render the colored badge with a "(provisional — moderate confidence)" qualifier; if `"high"`, render the colored badge at full weight.
3. Result: a badge component next to the chart that never overstates confidence on thin data.

**Inputs:** `anomaly.label`, `data_sufficiency.confidence`.

**Outputs:** Rendered badge UI element (color, icon, text).

**Edge cases & error handling:**
- Edge case: no `anomaly` object present in the response (query didn't request anomaly assessment) → behavior: badge component renders nothing.

**Dependencies:** Feature 11 (Anomaly Detection); Feature 12 (Data Sufficiency Indicator).

---

## 16. Degraded-Mode Disclosure
**Category:** Frontend
**Phase:** Phase 4
**Priority:** Should-have

**What it does:**
Shows a subtle line under the response when the query was parsed by the rule-based fallback instead of the LLM, so the "explainable/trustworthy" framing stays honest even in a degraded mode.

**User story:**
As any user, I want to know if my query was parsed in a simplified fallback mode, so that I understand why the result might be less precise and can rephrase if needed.

**How it works:**
1. Trigger: response has `parser_used == "rule_based"`.
2. Logic: renders a non-alarming line under the response: "Parsed using simplified matching — try rephrasing for best results."
3. Result: user is informed of the degraded mode without an alarming warning banner.

**Inputs:** `parser_used` field from the response.

**Outputs:** Rendered disclosure line under the response.

**Edge cases & error handling:**
- Edge case: `parser_used == "llm"` → behavior: no disclosure line rendered.

**Dependencies:** Feature 7 (Rule-Based Fallback Parser).

---

## 17. LLM Parser Eval Set
**Category:** QA
**Phase:** Phase 5
**Priority:** Should-have

**What it does:**
Runs a hand-written set of 20–25 test queries through the LLM parser (Feature 6) to measure and record its real accuracy before it's cited in the pitch.

**User story:**
As a judge, I want to know the parser's real accuracy rather than an unverified claim, so that I can trust the number presented in the pitch.

**How it works:**
1. Trigger: run manually before the final pitch, Phase 5.
2. Logic: runs each test query (covering pinned phrasings, city names, missing dates, ambiguous parameters, malformed input) through Feature 6, compares parsed output to expected output, computes `accuracy = correct_parses / total_test_queries`.
3. Result: a real, recorded accuracy number used in the pitch deck — never an assumed "90–95%" figure.

**Inputs:** 20–25 hand-written test queries with expected parsed outputs.

**Outputs:** Recorded accuracy percentage.

**Edge cases & error handling:**
- Edge case: accuracy is lower than expected → behavior: reported honestly; used as input for Day 2 morning triage, not hidden from the pitch.

**Dependencies:** Feature 6 (Natural Language Query Parsing).

---

## 18. Cached Demo Fallback
**Category:** Reliability
**Phase:** Phase 5
**Priority:** Must-have

**What it does:**
Prepares precomputed JSON responses or screenshots for the three pinned demo queries, so the presentation can continue smoothly if live infrastructure has issues.

**User story:**
As the presenting team, I want a fallback for the live demo, so that a network or API hiccup doesn't derail the pitch.

**How it works:**
1. Trigger: prepared during Phase 5, before the final presentation.
2. Logic: runs the three pinned demo queries against the live system, captures the full response JSON and/or screenshots of the rendered UI.
3. Result: a ready-to-show static fallback that can be substituted if the live `POST /chat` call fails during judging.

**Inputs:** Live responses for the three pinned demo queries.

**Outputs:** Saved JSON/screenshots for offline use during the demo.

**Edge cases & error handling:**
- Edge case: live system is fully broken at demo time → behavior: presenter switches to the cached fallback without breaking the presentation flow.

**Dependencies:** Features 8, 9, 10 (the three pinned query types), fully working end-to-end (Phase 3/4 complete).

---

## Deferred / Future Features
- **Multilingual support** (Hindi, Marathi, Tamil, etc.) — deferred to post-hackathon Phase 1 of the future roadmap; not needed to prove the core PS1/PS2/PS3 concept.
- **Fishing zone & wave height integration** (INCOIS PFZ, wave height API) — deferred; adds scope beyond core ARGO temperature/salinity data.
- **Cyclone & safety data integration** (IMD cyclone tracks, ocean state forecast) — deferred; a distinct data domain from ARGO profiles.
- **Multi-turn conversational memory** — deferred; stateless queries were a deliberate scope decision to reduce build risk.
- **Production deployment / INCOIS-VEDAS integration / mobile & WhatsApp bot** — deferred to post-hackathon Phase 4 of the future roadmap.
- **Fine-tuned LLM parser** — deferred; a prompted pre-trained model plus an eval set (Feature 17) was judged sufficient for the fixed query schema.
