# FloatChat-Lite — Phases

> **Status:** Draft | **Last updated:** 13 August 2026

## Roadmap Summary

| Phase | Name | Goal | Target duration |
|---|---|---|---|
| Phase 1 | Foundation & Data Pipeline | Repo, scope, and a queryable ARGO dataset with precomputed baselines exist | Day 1, hours 0–5 |
| Phase 2 | Basic Chat UI Shell | A working chat interface exists against dummy backend responses | Day 1, hours 5–8 |
| Phase 3 | Full Pipeline Integration | Real data, LLM parsing + fallback, anomaly scoring, and explanations all connected end-to-end | Day 2, hours 0–3 |
| Phase 4 | UX Polish & Explainability Surfacing | Charts, maps, anomaly badges, and explanation UI are demo-quality | Day 2, hours 3–5 |
| Phase 5 | Hardening, Testing & Demo Rehearsal | System is reliable, validated, and rehearsed for judges | Day 2, hours 5–7 |
| Future | Post-Hackathon Roadmap | Multilingual, PFZ/cyclone integration, production deployment | Not scheduled |

---

## Phase 1: Foundation & Data Pipeline
**Goal:** Establish the shared PRD/scope and produce a preprocessed, query-able ARGO dataset with precomputed anomaly baselines.

**Scope:**
- Agree on unified PRD, finalize scope, set up the repo and team roles.
- Ingest ARGO NetCDF data from INCOIS and preprocess it into CSV/Parquet.
- Precompute production baselines (mean/std by region/month, full available history).
- Run `validate_heatwave.py` against the preprocessed dataset and record the real result (flagged or honestly not-flagged) — owned by Member 3.
- Go/no-go checkpoint at hour 4: if ingestion isn't query-ready, switch to a pre-vetted fallback subset (1–2 regions, 2 years).

**Out of scope for this phase:**
- Any frontend work.
- LLM query parsing integration.
- Live anomaly scoring against real user queries (baselines only, not yet wired to a query flow).

**Deliverables:**
- Repo initialized with agreed structure and team-role assignments.
- Preprocessed ARGO Parquet/CSV dataset (or fallback subset, clearly labeled if used).
- Precomputed production and validation baseline tables.
- Recorded `validate_heatwave.py` output (region, max|z|, month, flagged True/False) — no placeholder numbers.

**Dependencies:** Access to INCOIS ARGO NetCDF data; Python data-processing stack (pandas, numpy, xarray) set up.

**Exit criteria:** The dataset can answer `get_profile()`, `get_regional_average()`, and `get_time_series()` queries directly from a script; baselines exist for anomaly scoring; the heatwave validation checklist (PRD Section 10.2 equivalent) is checked off with a real, recorded result.

---

## Phase 2: Basic Chat UI Shell
**Goal:** Stand up a working chat interface that a user can type into and see a response render, even with placeholder data.

**Scope:**
- Build the React + TypeScript chat panel: input box, suggested query chips, response area layout.
- Wire the UI to a dummy/stubbed backend that returns representative fake responses matching the eventual API contract.
- Establish the basic visual style (colors, fonts, spacing) per the design doc.

**Out of scope for this phase:**
- Real ARGO data, real LLM parsing, real anomaly scoring — everything here is stubbed.
- Anomaly badge confidence logic (can render with hardcoded states for now).
- Polished map/chart rendering — basic versions are acceptable.

**Deliverables:**
- A running frontend that accepts a query and displays a mock chart, map, and explanation footer.
- Suggested query chips wired to populate the input box.

**Dependencies:** Phase 1's API contract shape (even if the real data isn't ready yet, the response JSON structure must be agreed).

**Exit criteria:** A teammate can open the app, type or click a query, and see a full mock response render without errors.

---

## Phase 3: Full Pipeline Integration
**Goal:** Connect every real component end-to-end so a live query produces a real, data-backed response.

**Scope:**
- Integrate the LLM query parser (with the rule-based fallback and `parser_used` tagging).
- Connect the Data Layer to the real (or fallback) preprocessed dataset.
- Wire the Anomaly Model to precomputed production baselines.
- Wire the Explainability Layer to generate `answer_explanation` and anomaly "why" text.
- Replace the frontend's dummy backend calls with real `POST /chat` requests.

**Out of scope for this phase:**
- Visual polish, map styling, chart aesthetics (Phase 4).
- Full error-message copywriting pass (basic error handling only; refined in Phase 4/5).

**Deliverables:**
- A working `POST /chat` endpoint returning real data, real anomaly scores, and real explanations.
- Frontend successfully rendering live (not mocked) responses for at least one query per type (profile, regional_average, time_series).

**Dependencies:** Phase 1 (dataset + baselines) and Phase 2 (UI shell) both complete.

**Exit criteria:** All three pinned demo queries return a real, correct response end-to-end, even if the UI isn't fully polished yet.

---

## Phase 4: UX Polish & Explainability Surfacing
**Goal:** Bring the chat UI to demo quality, with every explainability and data-sufficiency signal clearly visible.

**Scope:**
- Polish chart and map rendering (Plotly.js, Leaflet) for clarity on a projector/screen.
- Implement the full `AnomalyBadge` component behavior, including confidence-based suppression (Appendix F logic).
- Implement the data-sufficiency line and explanation footer styling.
- Implement the degraded-mode disclosure line for `parser_used == "rule_based"`.
- Build out remaining static/supporting pages if any (e.g., an "about" panel).

**Out of scope for this phase:**
- New backend functionality — this phase is UI-facing only.
- Final end-to-end testing and rehearsal (Phase 5).

**Deliverables:**
- Fully styled chat UI matching the design doc's component library.
- Anomaly badge correctly suppresses/qualifies based on `data_sufficiency.confidence` in all three confidence tiers.
- Explanation footer and disclosure line rendering correctly in both LLM-parsed and fallback-parsed responses.

**Dependencies:** Phase 3's live `POST /chat` integration.

**Exit criteria:** The three pinned demo queries, run live, produce a fully polished, correctly badged, fully explained response with no visual placeholders remaining.

---

## Phase 5: Hardening, Testing & Demo Rehearsal
**Goal:** Make the system reliable and the team confident, with every claim in the pitch backed by real, recorded evidence.

**Scope:**
- End-to-end testing of all three pinned demo queries and common failure paths (`no_data`, `parse_error`, `general_error`).
- Run the LLM parser eval set (Appendix D equivalent) and record the real accuracy number.
- Prepare cached fallback (screenshots or precomputed JSON) for the three pinned queries in case of live infra issues.
- Finalize pitch slides, referencing only validated numbers (heatwave result, parser accuracy) — no placeholders.
- Rehearse the full demo 20+ times.

**Out of scope for this phase:**
- New features of any kind — this is explicitly protected time, never pulled for late feature work.

**Deliverables:**
- Recorded LLM parser accuracy number.
- Cached fallback responses for the three pinned demo queries.
- Finalized, rehearsed pitch deck citing only real, verified results.

**Dependencies:** Phases 1–4 complete.

**Exit criteria:** All three pinned demo queries work reliably on repeated live runs; the team has rehearsed the full demo 20+ times; every number in the pitch traces back to a recorded, real result.

---

## Future / Not Yet Scheduled
- Multilingual support (Hindi, Marathi, Tamil, etc. via Bhashini AI / fine-tuned Llama, MACHLI app partnership).
- Wave height + fishing zone data integration (INCOIS Potential Fishing Zone advisories, wave height API).
- Cyclone + safety data integration (IMD cyclone tracks, INCOIS ocean state forecast).
- Production deployment, INCOIS/VEDAS integration, mobile/WhatsApp bot, deeper explainability (feature contributions, counterfactuals).
- Multi-turn conversational memory / follow-up questions.
- Migration off CSV/Parquet to a real database, if usage scale requires it.
