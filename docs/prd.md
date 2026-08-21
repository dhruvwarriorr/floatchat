# FloatChat-Lite product requirements

> Status: active product baseline; implementation incomplete
> Last synchronized: 21 August 2026

## 1. Product overview

FloatChat-Lite aims to make a narrow set of Indian Ocean ARGO temperature and salinity questions accessible through natural language, while showing source, method, data sufficiency, and confidence. The repository currently demonstrates the intended experience with illustrative values and provides a backend safety scaffold; it does not yet answer real-data questions end-to-end.

## 2. Problem statement

ARGO observations are distributed in scientific formats and require data-selection, QC, and analysis knowledge. The product goal is a transparent answer-oriented workflow for non-specialists, not a replacement for operational forecasting or expert oceanographic analysis.

Claims about gaps in previous teams, model performance, validation, user impact, or operational usefulness require direct evidence. They are not treated as established project results here.

## 3. Goals

- Answer supported profile and time-series/anomaly questions from a reviewed Indian Ocean ARGO subset.
- Include source/version, method, dates, spatial selection, profile count, confidence, parser, and proxy caveats in every successful real-data answer.
- Use an explainable z-score policy with separate production and validation baselines.
- Remain useful when an optional LLM parser fails by using a deterministic fallback.
- Deliver a truthful live/local demo plus a sanitized cached fallback.

Regional average is a secondary goal and should ship only after profile and time-series flows are stable.

## 4. Non-goals for the core build

- Authentication, accounts, persistent chat history, or multi-turn memory.
- A database server, live NetCDF parsing, microservices, queues, Kubernetes, or background-job infrastructure.
- LangChain, agent frameworks, vector search, fine-tuning, or multiple LLM providers.
- Advanced anomaly ML or predictive/forecasting claims.
- Multilingual, fishing-zone, cyclone, wave-height, mobile, or WhatsApp integrations.
- Redesigning the accepted frontend.

## 5. Users and scenarios

| User | Need | Pinned scenario |
| --- | --- | --- |
| Forecaster/researcher | Quick exploratory vertical context | Temperature profile near Mumbai in July 2024 |
| Researcher/student | Long-window context and transparent anomaly method | Shallow-water SST proxy at 19N, 72.8E for 2015–2024 |
| Student | Regional summary, if data is stable | Average salinity in the Bay of Bengal in 2023 |
| Any user | Honest trust cues and safe failure | Source, method, profile count, confidence, and clear retry guidance |

These personas and needs are product assumptions; user research is ⚪ needs verification.

## 6. Requirements and current status

| ID | Requirement | Status | Current state / remaining work |
| --- | --- | --- | --- |
| FR-01 | Accept one non-blank query up to 500 characters | ✅ | Backend model and frontend form both enforce non-empty input; max length is backend-only. |
| FR-02 | Deterministically parse the pinned grammar | ✅ narrow | Four patterns, full month names, and years are supported; general coordinates/cities are not. |
| FR-03 | Optional LLM parse with strict validation, timeout, and deterministic fallback | 🟠 | Model enum and environment example exist; adapter/settings/failure tests do not. |
| FR-04 | Retrieve reviewed profile and time-series data from prepared artifacts | 🔴 | Blocked by absent artifacts and unimplemented repository queries. |
| FR-05 | Provide regional average only if stable | 🔴 | Parser pattern exists; real retrieval is absent. |
| FR-06 | Score anomalies from production baselines; skip zero/insufficient std | 🟡 | Policy function and boundary tests exist; baselines and runtime integration do not. |
| FR-07 | Report low (1–5), medium (6–20), high (21+) confidence | 🟡 | Implemented independently in frontend and backend; not yet driven by real query results. |
| FR-08 | Suppress severity for low confidence and qualify medium | 🟡 | Implemented in UI/backend policy; not integrated end-to-end. |
| FR-09 | Explain source, aggregation, selection, dates, and proxy caveats | 🟡 | Illustrative preparation text exists; real explanation service/contract response does not. |
| FR-10 | Return friendly `parse_error`, `no_data`, `general_error` | 🟡 | Backend emits parse/general errors; no-data path and distinct frontend states are missing. |
| FR-11 | Render result chart and geographic context | ✅ illustrative | Recharts and static Bhuvan image; no real API data. |
| FR-12 | Disclose `parser_used=rule_based` | 🟠 | Backend tags parsed params; frontend type/UI does not expose it. |
| FR-13 | Keep production and validation baselines separate | 🟡 boundary | Directories/schema/architecture exist; no artifacts or builder exists. |
| FR-14 | Provide health and one-container runtime | 🟡 | Endpoints and recipe exist; data readiness and deployment acceptance are absent. |

## 7. Non-functional requirements

- **Honesty:** illustrative, cached, planned, and verified real outputs must be distinguishable.
- **Safety:** input is validated and never treated as code or a filesystem path; external errors are sanitized.
- **Reproducibility:** data builds accept explicit inputs/outputs and record provenance, QC, version, hashes, and build command.
- **Resilience:** the optional provider must never be required for pinned deterministic flows.
- **Maintainability:** preserve one frontend, one API, offline scripts, and file-based serving artifacts.
- **Accessibility:** target usable keyboard, text-equivalent charts, reduced motion, and sufficient contrast; formal acceptance is not yet recorded.

## 8. Success evidence

Targets are not results. Completion requires recorded evidence for:

| Outcome | Acceptance evidence |
| --- | --- |
| Profile and time-series work end-to-end | Reviewed dataset/build plus HTTP/browser results |
| Regional average included | Stable real-data response or explicit scope cut |
| Parser reliability | Frozen labelled set and observed result |
| Scientific anomaly behaviour | Unit boundaries plus recorded validation output, including negative results |
| Provider resilience | Forced timeout/malformed/missing-configuration run with `rule_based` disclosure |
| Demo readiness | Container/local and cached runs on the presentation setup |

The evidence log currently contains no result rows, so none of these outcomes is verified.

## 9. Constraints and dependencies

- Current prerequisites are Node.js ≥22.13, Python ≥3.11, and `make`; the container uses Python 3.12.
- A reviewed ARGO source/subset, redistribution decision, region definitions, QC policy, and shallow-water cutoff are unresolved P0 inputs.
- The LLM provider and hosting platform are ⚪ needs verification, not confirmed dependencies.
- The frontend contract cannot be frozen from illustrative objects; it needs reviewed real responses.

## 10. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Data/QC/provenance decisions remain unresolved | Blocks all real results | Freeze a small reviewed subset and manifest before broader coverage. |
| Frontend/backend contracts diverge | Integration rework or misleading UI | Freeze real fixtures and reconcile types together. |
| Readiness accepts files without integrity/science checks | False operational signal | Add schema/hash/provenance checks and keep scientific acceptance separate. |
| LLM scope distracts from deterministic data path | Core flow remains incomplete | Add provider only after deterministic HTTP success. |
| Illustrative values are mistaken for observations | Trust failure | Keep explicit disclosures; never copy them into scientific artifacts. |
| Evidence and fallback remain empty | Unsupported pitch/release claims | Record exact outputs and prepare sanitized cached artifacts before release. |

## 11. Open decisions

- [ ] Exact data source URL/access method, licence/redistribution terms, subset coverage, and dataset version.
- [ ] Region definitions and spatial/radius rules shared by preprocessing, repository, and baselines.
- [ ] QC policy, adjusted/raw value precedence, pressure-to-depth rule, and shallow-water cutoff.
- [ ] Final success data variants and frontend adapter.
- [ ] Whether suggested queries should remain absent from the accepted UI.
- [ ] LLM provider and timeout only after the deterministic pipeline works.
- [ ] Hosting target after the one-container build passes locally.

## 12. Related documents

- [Master project documentation](PROJECT_DOCUMENTATION.md)
- [Architecture](ARCHITECTURE.md)
- [API contract](API_CONTRACT.md)
- [Feature status](feature.md)
- [Roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md)
- [Evidence rules](evidence/README.md)
