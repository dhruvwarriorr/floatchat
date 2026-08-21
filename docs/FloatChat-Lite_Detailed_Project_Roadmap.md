**EXECUTION ROADMAP**

# How to Complete FloatChat-Lite

> A four-week student-team plan with a 48-hour hackathon cut-down

**Focused, explainable, and buildable by a small student team**

For a six-member team

Prepared 14 August 2026

Simple stack, evidence-first delivery, protected rehearsal time

## 1. Roadmap outcome

> **Finish line:** A stable browser demo answers three pinned ARGO questions, explains its method and confidence, survives an LLM outage, and is supported by a nine-slide identity-safe pitch with traceable evidence.

The four-week plan is the recommended route when the team has preparation time. The 48-hour plan later in this document is the emergency/hackathon cut-down. Both use the same scope and acceptance gates, so work is reusable rather than duplicated.

## 2. Freeze the simple stack on day zero

| **Area** | **Freeze this** | **Do not add during core build** |
| --- | --- | --- |
| Frontend | React + TypeScript + Vite; Plotly.js; Leaflet | Next.js, design system migration, native mobile |
| Backend | FastAPI + Pydantic | Microservices, GraphQL, background job system |
| Data | pandas/xarray preprocessing -> Parquet | MongoDB, Postgres, live NetCDF queries |
| Analytics | NumPy z-score against precomputed baselines | Isolation Forest, deep learning, model training |
| Parser | One LLM API + deterministic fallback | LangChain, multi-agent orchestration, multiple providers |
| Deployment | One container / one hosted app | Kubernetes, separate frontend/backend deployments unless required |

## 3. Team operating model

| **Member** | **Primary responsibility** | **Backup responsibility** | **Main evidence** |
| --- | --- | --- | --- |
| Member 1 | Tech lead and end-to-end integration | Deployment and code review | Architecture decision log; working integrated build |
| Member 2 | Frontend chat/result experience | Deck and documentation | UI state checklist; projector screenshots |
| Member 3 | Data preprocessing and anomaly model | Validation evidence | Dataset report; baseline tables; validation output |
| Member 4 | FastAPI, repository, and parser fallback | Integration tests | API contract tests; failure-path report |
| Member 5 | Charts, map, accessibility, UI QA | Frontend support | Visual QA checklist; keyboard/contrast checks |
| Member 6 | Test coordinator, evidence log, demo runbook | Documentation support | Rehearsal log; cached fallback; submission checklist |

> **If the team is smaller:** Combine Member 1+4, Member 2+5, and Member 3+6. Do not split the architecture into more services; reduce scope before increasing coordination cost.

## 4. Repository and work breakdown

| **Area** | **Suggested path** | **Owner** |
| --- | --- | --- |
| Frontend | frontend/src/features/chat, frontend/src/components, frontend/src/api | Members 2 and 5 |
| API | backend/app/main.py, backend/app/api/chat.py, backend/app/models.py | Members 1 and 4 |
| Services | backend/app/services/parser.py, data.py, anomaly.py, explain.py | Members 1, 3, 4 |
| Data | data/raw, data/processed, data/baselines, data/manifest.json | Member 3 |
| Scripts | scripts/preprocess_argo.py, build_baselines.py, validate_heatwave.py, evaluate_parser.py | Members 3 and 4 |
| Tests | backend/tests, frontend tests, demo/checklist | Member 6 coordinates |
| Docs | README, evidence log, runbook, presentation | Members 2 and 6 |

## 5. Four-week implementation plan

### Week 1 - prove the data path

> **Goal:** A deterministic script can answer one real profile query and produce separate baseline tables before any LLM or polished UI is added.

| **Day** | **Work** | **Owner** | **Exit check** |
| --- | --- | --- | --- |
| 1 | Confirm scope, pinned queries, region boxes, data source, licenses, and response schema. | All / M1 leads | Signed scope sheet and frozen JSON contract |
| 2 | Download a small real ARGO subset; inspect NetCDF variables, adjusted values, and QC flags. | M3 | Data manifest and five manually checked profiles |
| 3 | Build NetCDF-to-Parquet preprocessing with schema/range validation. | M3 + M4 | Repeatable command and clean validation report |
| 4 | Implement get_profile and distance/time/depth filters against Parquet. | M4 | Pinned profile query returns chart-ready values |
| 5 | Build separate production and validation baselines; implement z-score unit tests. | M3 | Versioned baseline files and passing boundary tests |
| 6 | Run the heatwave validation script and record the exact result without editing. | M3 + M6 | Evidence log entry or documented negative result |
| 7 | Checkpoint: real data path review; prepare fallback subset if needed. | All | Go/no-go decision recorded |

### Week 2 - build the contract and UI shell

| **Day** | **Work** | **Owner** | **Exit check** |
| --- | --- | --- | --- |
| 8 | Create FastAPI project, models, health endpoint, and POST /chat stub. | M1 + M4 | OpenAPI schema matches frozen contract |
| 9 | Implement regional average and time-series repository functions. | M4 + M3 | Deterministic fixture tests pass |
| 10 | Implement anomaly and explanation services with insufficient-data outcomes. | M3 + M1 | Contract examples for all confidence tiers |
| 11 | Scaffold React/Vite app; build input, suggested queries, and result shell. | M2 | Mock response renders end-to-end |
| 12 | Add profile/time-series Plotly charts and location map. | M5 + M2 | Readable laptop and projector screenshots |
| 13 | Implement empty/loading/error/fallback states and anomaly badge logic. | M2 + M5 | Component tests cover every UI state |
| 14 | Contract checkpoint: frontend mock fixtures and backend models are identical. | M1 + M6 | No field-name or enum mismatch |

### Week 3 - connect natural language and real data

| **Day** | **Work** | **Owner** | **Exit check** |
| --- | --- | --- | --- |
| 15 | Integrate one structured-output LLM parser with strict validation and timeout. | M1 | Pinned parses succeed and malformed output is rejected |
| 16 | Implement city/coordinate/date/parameter rule parser and forced-fallback test. | M4 | Fallback handles all pinned queries or returns parse_error |
| 17 | Wire POST /chat orchestration and typed error mapping. | M1 + M4 | Real profile query works through HTTP |
| 18 | Connect frontend to real API and render all three real query types. | M1 + M2 | Three pinned queries work locally |
| 19 | Verify explanation, proxy caveat, sample count, confidence, and parser disclosure. | M3 + M5 | Trust checklist passes for every response |
| 20 | Write 20-25 labeled parser queries and run the evaluation. | M6 + M4 | Measured result stored with test set |
| 21 | Integration checkpoint and scope cut if any pinned flow is unstable. | All | Feature freeze decision |

### Week 4 - harden, prove, and present

| **Day** | **Work** | **Owner** | **Exit check** |
| --- | --- | --- | --- |
| 22 | Deploy one container; verify data files, secrets, CORS, and health check. | M1 | Hosted app serves all pinned queries |
| 23 | Run endpoint, failure-path, and browser QA; fix only release blockers. | M5 + M6 | Release checklist has no critical failures |
| 24 | Capture fallback JSON/screenshots and test offline switch procedure. | M6 | Fallback opens in under 20 seconds |
| 25 | Finalize exactly nine slides; include only validated numbers and citations. | M2 + M6 | Identity/citation/slide-count audit passes |
| 26 | Record 5-7 minute video or run a timed practice with the same structure. | All | One complete take within time |
| 27 | Run 10 rehearsals; log failures and resolve high-frequency issues. | All | Failure modes have assigned mitigations |
| 28 | Run final 10 rehearsals; freeze build, deck, and fallback artifacts. | All | 20+ run log and release package complete |

## 6. 48-hour hackathon cut-down

> **Rule:** The data path is the critical path. Keep two hours protected for final verification and rehearsal even if features remain unfinished.

| **Clock** | **Parallel work** | **Owner** | **Hard gate** |
| --- | --- | --- | --- |
| H0-H1 | Freeze scope, pinned queries, contract, roles, evidence log. | All | No new features after H1 without a cut. |
| H1-H4 | Data subset + preprocessing + baselines; UI shell in parallel. | M3/M4; M2/M5 | At H4, switch to prepared fallback subset if real ingestion is not query-ready. |
| H4-H6 | Validate anomaly script; implement repository functions and API stub. | M3/M4/M1 | One real profile query works from a script and HTTP. |
| H6-H9 | Build response UI, charts, map, and mock confidence states. | M2/M5 | Mock contract renders every state. |
| H9-H12 | LLM parser + deterministic fallback + typed errors. | M1/M4 | Forced LLM failure still produces a valid pinned response. |
| H12-H15 | Connect real data, anomaly, explanation, and frontend. | All | Profile and time-series+anomaly work end-to-end. |
| H15-H17 | Add regional average only if core flows are stable; polish copy and projector layout. | M2/M3/M5 | Feature freeze at H17. |
| H17-H19 | Run parser eval and complete evidence/claim audit. | M4/M6 | Deck contains only recorded numbers. |
| H19-H21 | Deploy and capture cached fallback. | M1/M6 | Hosted and offline paths both work. |
| H21-H24 | Final testing, 20 short demo repetitions, deck/video rehearsal. | All | No feature work; release only blocker fixes. |

## 7. Dependency and checkpoint map

| **Checkpoint** | **Cannot start until** | **Pass condition** | **If it fails** |
| --- | --- | --- | --- |
| C1 Data ready | Subset acquired | Profile query and schema report work | Use pre-vetted smaller subset |
| C2 Baseline ready | C1 | Separate production/validation files with mean/std/n | Limit anomaly to supported regions or return insufficient |
| C3 Contract frozen | Pinned queries known | Backend model and frontend fixture match | Stop UI feature work and reconcile names |
| C4 Core integrated | C1-C3 | Profile and time-series+anomaly work through HTTP | Cut regional average and map interaction |
| C5 Evidence ready | C4 | Parser eval and validation outputs are stored | Remove unverified claims |
| C6 Release ready | C4-C5 | Live and cached demos pass on presentation machine | Present workflow proof; do not fake completion |

## 8. Acceptance gates by workstream

| **Workstream** | **Definition of done** |
| --- | --- |
| Data | Versioned subset, provenance, schema/range checks, QC policy, deterministic preprocessing command. |
| Baselines | Region/month/parameter mean, std, n; exact periods; production and validation separated. |
| Backend | Validated /chat contract, short parser timeout, fallback path, typed errors, no internal trace leakage. |
| Frontend | Every state is readable, confidence changes badge behavior, and charts/maps work at projector scale. |
| Explainability | Every result states source, aggregation, radius, dates, proxy caveat, profile count, and confidence. |
| Evaluation | Labeled parser set and anomaly validation output are stored with date, dataset version, command, and owner. |
| Deployment | One documented start/deploy path; secrets server-side; health and pinned-query smoke tests pass. |
| Presentation | Exactly nine slides; references trace in-slide citations; no personal/institutional identity; no placeholder results. |

## 9. Risk triggers and cut order

| **Trigger** | **Immediate action** | **Scope cut order** |
| --- | --- | --- |
| Data not query-ready by checkpoint | Activate fallback subset immediately; do not keep waiting. | Keep profile + time series; drop wide regional coverage. |
| LLM unreliable or quota-limited | Default pinned queries to the rule parser and preserve disclosure. | Drop free-form breadth; keep supported grammar. |
| Frontend integration late | Render one chart type well and use a static location marker if necessary. | Drop map interaction, then regional-average KPI. |
| Anomaly validation inconclusive | Remove validation claim and present the test plan and recorded result honestly. | Do not change threshold merely to manufacture a pass. |
| Deployment unstable | Use local presentation machine or cached JSON/screenshots. | Drop live remote dependency, not evidence or rehearsal. |
| Time under two hours | Freeze all features; run release checks and rehearsals only. | No exceptions. |

## 10. Testing matrix

| **Test** | **Case** | **Expected result** | **Owner** |
| --- | --- | --- | --- |
| Parser | Pinned query / city / explicit coordinates | Valid supported schema | M4 |
| Parser fallback | Forced timeout and malformed LLM JSON | rule_based or typed parse_error | M4 |
| Data | No matches / few matches / many matches | no_data / low / medium-high confidence | M3 |
| Anomaly | z=0, +/-1.5, +/-2.5, std=0 | Correct boundary labels or skipped scoring | M3 |
| API | Unexpected internal exception | general_error without stack trace | M1 |
| UI | All labels and confidence tiers | Color + icon + text, low confidence neutral | M5 |
| Responsive | 1366x768 and presentation laptop/projector | No clipping; chart/map readable | M5 |
| Demo | Network loss / LLM outage / hosting cold start | Fallback path within 20 seconds | M6 |

## 11. Daily team rhythm

1. Ten-minute stand-up: each member states the next testable output, current blocker, and help needed.
1. Work in small vertical slices. Merge only when the relevant unit/contract check passes.
1. At every checkpoint, demonstrate the actual output rather than reporting percent complete.
1. Member 6 updates the evidence log with command, dataset version, output, owner, and date.
1. End each day with one full pinned-query run and one forced-failure run.
1. After feature freeze, accept only release blockers: crashes, wrong data, unreadable slides/UI, identity leakage, or unsupported claims.

## 12. Presentation and video completion plan

| **Asset** | **Content** | **Completion gate** |
| --- | --- | --- |
| Slide 1 | Problem title, domain, category, Team ID, Team Name | No personal or institutional identity |
| Slides 2-3 | Problem/users and literature/current-solution comparison | Every major claim cites an authoritative or peer-reviewed source |
| Slides 4-6 | Solution, simple stack, differentiation | Technology maps directly to the identified gap; no novelty exaggeration |
| Slide 7 | Feasibility, measurable targets, risks, roadmap | Targets are labeled; validation gates are not presented as results |
| Slide 8 | Complete references | All in-slide numbers resolve to a traceable entry |
| Slide 9 | Member 1-6 roles | Meaningful contributions only; no names/institution |
| 5-7 minute video | Problem -> evidence -> gap -> solution -> differentiation -> feasibility -> close | Readable slides, clear audio, no credentials or private information |

## 13. Final release checklist

- Repository starts from a clean documented command on the presentation machine.
- Processed data and baselines have a version/manifest and are not rebuilt during the demo.
- Three pinned queries return expected result types; low-data behavior is honest.
- LLM failure and no-data paths are demonstrated once after the final deployment.
- Parser accuracy and anomaly validation values exactly match stored outputs or are absent from the pitch.
- Cached JSON/screenshots open offline and contain no keys, identities, or confidential data.
- Deck has exactly nine slides, readable font sizes, citations, and no identity leakage.
- Video is 5-7 minutes and complements rather than reads the slides.
- The team has a primary presenter, demo operator, timekeeper, and Q&A owner.
- The build, deck, and fallback package are frozen after final rehearsal.

## 14. Evidence log template

| **Date** | **Owner** | **Claim/test** | **Command or method** | **Dataset/build** | **Result** | **Allowed in pitch?** |
| --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Member N | Example: parser eval | evaluate_parser.py | dataset-v1 / build hash | Observed value | Yes / No |
| YYYY-MM-DD | Member N | Example: heatwave validation | validate_heatwave.py | baseline-validation-v1 | Exact script output | Yes / No |
| YYYY-MM-DD | Member N | Example: 20 demo runs | run checklist | release candidate | Pass/failure count | Yes / No |

## 15. Source basis

1. Project source pack supplied by the team: prd.md, architecture.md, design.md, feature.md, phases.md, todo.md, and FloatChat-Lite_Master_v3.md.
1. Submission rules supplied by the team: First_Round_Shortlisting_Rubric_PPT_Video_Guidelines.pdf and SIH Internal Template.pptx.
1. External evidence references are listed in FloatChat-Lite Project Documentation and in the nine-slide deck.
