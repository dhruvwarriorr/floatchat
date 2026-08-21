# FloatChat-Lite — Todo

> **Last updated:** 13 August 2026. Check items off as they're completed; keep this file in sync with actual progress.

## Phase 1: Foundation & Data Pipeline
- [ ] Agree on unified PRD and finalize scope with the full team
- [ ] Set up the repo (structure, branches, team-role assignments per PRD Section 5 / prd.md)
- [ ] Source ARGO NetCDF data from INCOIS for the Indian Ocean region (2015–2024 subset)
- [ ] Write the NetCDF → CSV/Parquet preprocessing script (float_id, time, lat, lon, depth, temperature, salinity)
- [ ] Run preprocessing and validate output schema against a few known profiles
- [ ] Precompute production baselines (mean/std by region/month, full available history)
- [ ] Precompute validation baseline (2015–2018) as a separate, non-conflated baseline set
- [ ] **Checkpoint (hour 4):** go/no-go decision — if ingestion isn't query-ready, prepare and swap in the pre-vetted fallback subset (1–2 regions, 2 years)
- [ ] Implement `validate_heatwave.py` (region filtering, baseline comparison, Z-score computation, CLI output)
- [ ] Run `validate_heatwave.py` against the real preprocessed dataset
- [ ] Record the real validation result (region, max|z|, month, flagged True/False) — no placeholder numbers
- [ ] If not flagged: decide on fallback plan (honest reporting / widen region / different real event), time-boxed for Day 2 morning if needed

## Phase 2: Basic Chat UI Shell
- [ ] Scaffold the React + TypeScript frontend project
- [ ] Build the chat input box component
- [ ] Build the suggested query chips component with the four pinned example queries
- [ ] Build the response area layout (header, chart placeholder, map placeholder, explanation footer placeholder)
- [ ] Stub a mock backend (or mock fetch responses) matching the agreed API contract shape
- [ ] Wire the input box to submit a query and render the mocked response
- [ ] Apply basic visual style (colors, fonts, spacing) per design.md's component library

## Phase 3: Full Pipeline Integration
- [ ] Write the LLM query-parsing prompt and integrate the chosen LLM API (GPT-4o-mini / Claude 3.5 / Ollama Llama 3.1)
- [ ] Implement `parser_used: "llm"` tagging on successful LLM parses
- [ ] Implement the rule-based fallback parser (city gazetteer, coordinate regex, year-range regex, keyword matching)
- [ ] Implement `parser_used: "rule_based"` tagging and the LLM-failure/timeout fallback trigger
- [ ] Implement `get_profile()` in the Data Layer against the real (or fallback) dataset
- [ ] Implement `get_regional_average()` in the Data Layer
- [ ] Implement `get_time_series()` in the Data Layer
- [ ] Implement Z-score anomaly scoring against precomputed production baselines
- [ ] Implement anomaly label classification (normal / mild / strong, positive/negative)
- [ ] Implement the `data_sufficiency` calculation (profile_count, coverage_radius_km, confidence tiering: low 1–5, medium 6–20, high 21+)
- [ ] Implement the Explainability Layer's `answer_explanation` text generation (data source, aggregation method, proxy caveats like the ≤10m SST cutoff)
- [ ] Implement the anomaly "why" explanation text generation
- [ ] Implement `POST /chat` endpoint wiring all of the above together
- [ ] Implement `no_data`, `parse_error`, and `general_error` friendly error responses
- [ ] Replace the frontend's mocked backend calls with real `POST /chat` requests
- [ ] Test all three query types (profile, regional_average, time_series) end-to-end with real data

## Phase 4: UX Polish & Explainability Surfacing
- [ ] Polish Plotly.js chart rendering (depth profiles and time series) for readability on a projector
- [ ] Polish Leaflet map rendering (location pin styling, zoom defaults)
- [ ] Build the `AnomalyBadge` component with full confidence-aware logic (suppress on low, qualify on medium, full weight on high)
- [ ] Style the explanation footer and data-sufficiency line per design.md
- [ ] Implement the degraded-mode disclosure line for `parser_used == "rule_based"` responses
- [ ] Style all four error states (`no_data`, `parse_error`, `general_error`, empty state) as friendly, non-technical messages
- [ ] Run the three pinned demo queries live and verify polished output end-to-end (chart, map, badge, explanation, confidence)

## Phase 5: Hardening, Testing & Demo Rehearsal
- [ ] Write the 20–25 query LLM parser eval set (pinned phrasings, city names, missing dates, ambiguous parameters, malformed input)
- [ ] Run the eval set and record the real accuracy number
- [ ] End-to-end test all three pinned demo queries repeatedly for reliability
- [ ] End-to-end test all three error paths (`no_data`, `parse_error`, `general_error`)
- [ ] Capture cached fallback (screenshots and/or precomputed JSON) for the three pinned demo queries
- [ ] Finalize pitch slides using only validated numbers (heatwave result from Phase 1, parser accuracy from this phase)
- [ ] Rehearse the full demo end-to-end (target: 20+ full run-throughs)
- [ ] Final check: confirm no placeholder numbers or unverified claims remain anywhere in the pitch deck

## Backlog / Unscheduled
- [ ] Multilingual support (Hindi, Marathi, Tamil, etc.)
- [ ] INCOIS Potential Fishing Zone / wave height data integration
- [ ] IMD cyclone track / ocean state forecast integration
- [ ] Multi-turn conversational memory / follow-up questions
- [ ] Production deployment, INCOIS/VEDAS integration, mobile/WhatsApp bot
- [ ] Fine-tuned LLM parser (in place of prompted pre-trained model)
- [ ] Migration off CSV/Parquet to a real database, if usage scale requires it
