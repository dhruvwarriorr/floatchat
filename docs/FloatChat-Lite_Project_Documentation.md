# FloatChat-Lite project handbook

> Detailed product and engineering baseline
> Status: illustrative frontend and backend foundation implemented; scientific pipeline and integration incomplete
> Last synchronized: 21 August 2026

For the concise entry point, use [Project documentation](PROJECT_DOCUMENTATION.md). This handbook captures the stable scope, terminology, policies, and definition of done without presenting planned work as implemented.

## 1. Project purpose

FloatChat-Lite is a narrow, explainable demonstration for supported Indian Ocean ARGO temperature and salinity questions. Its intended real-data response joins:

- a natural-language query;
- validated structured parameters;
- a reviewed, versioned ARGO subset;
- a chart and geographic context;
- optional anomaly context from a production baseline;
- data sufficiency and confidence; and
- source, method, selection, parser, and proxy caveats.

The current repository demonstrates the experience with bundled illustrative values and safely refuses real API answers because scientific artifacts and repository queries are absent.

## 2. Official vocabulary

| Term | Meaning |
| --- | --- |
| **Illustrative frontend** | The accepted UI backed by bundled `OceanResponse` values; not live or validated ocean data. |
| **Deterministic parser** | The narrow Python rule parser for the four pinned phrase families. Use this term instead of “fallback parser” when no LLM is involved. |
| **LLM parser adapter** | Optional planned provider integration. It must fall back to the deterministic parser. |
| **Scientific repository** | Runtime service that will read reviewed prepared artifacts and perform supported filters/aggregations. |
| **Prepared profile artifact** | Versioned query-ready Parquet produced offline from reviewed ARGO inputs. |
| **Production baseline** | Baseline used by live answers. |
| **Validation baseline** | Separate artifact used only for known-event/scientific evaluation. |
| **Shallow-water SST proxy** | Shallowest acceptable ARGO measurement within a documented cutoff; not satellite SST. |
| **Data sufficiency** | Matching profile count, documented coverage, and confidence tier. |
| **Cached fallback** | Sanitized response/screenshot captured from a recorded build, labelled with origin and version. |

## 3. Current status

| Area | Status | Repository reality |
| --- | --- | --- |
| Product/UI experience | ✅ illustrative | Four local response flows, charts, static map, confidence, explanation, error/loading/reset. |
| Query/API foundation | 🟡 partial | Deterministic parser, Pydantic models, health, safe errors; no success response. |
| Anomaly policy | 🟡 partial | Threshold/confidence code and tests; no real baseline or runtime connection. |
| Scientific data | 🔴 blocked | No manifest, Parquet, or baseline artifact. |
| Scientific scripts/repository | 🔴 blocked | Required entrypoints and query implementation absent. |
| Frontend/API integration | 🔴 blocked | No client; frontend/backend types diverge. |
| Optional LLM | 🟠 planned | Environment placeholders/model enum only. |
| Deployment | 🟡 recipe only | Docker/Compose exist; no accepted run or hosting target. |
| Evidence/demo | 🟠 planned | Evidence log and cache directories are empty apart from structure. |

## 4. Scope

### Core release

- Profile and time-series/anomaly questions from a reviewed subset.
- Regional average only if stable after the core flows.
- Temperature, salinity, and explicitly disclosed shallow-water SST proxy.
- One accepted web interface and one FastAPI application.
- Offline preprocessing, Parquet serving artifacts, and separate baseline artifacts.
- Deterministic parser; at most one optional LLM adapter.
- Typed safe failures, confidence-aware anomaly policy, and complete method/provenance context.
- One-container live/local path plus sanitized cached fallback.

### Explicit non-goals

Authentication, accounts, chat history, multi-turn memory, database servers, live NetCDF processing, vector search, LangChain, agents, fine-tuning, multiple providers, microservices, queues, advanced ML anomaly detection, native mobile, WhatsApp, multilingual, fishing-zone, wave, cyclone, and forecast integrations.

## 5. Current frontend

The accepted frontend uses React 19, TypeScript, Vite, Recharts, Lucide React, and locally bundled Manrope/Space Grotesk fonts. It has one page and no authentication or navigation hierarchy.

Four phrase families resolve locally to illustrative views:

1. Mumbai temperature depth profile.
2. Shallow-water SST proxy time series/anomaly at 19N, 72.8E.
3. Bay of Bengal monthly salinity regional average.
4. Arabian Sea warming/trend direction.

Suggested query chips are **not** rendered. Geographic context uses a static local Bhuvan image, not Leaflet. Charts use Recharts, not Plotly. See [Interface design](design.md).

## 6. Current backend

FastAPI exposes:

- `GET /health/live` — process liveness;
- `GET /health/ready` — current manifest/file-existence readiness; and
- `POST /chat` — validated input, deterministic parsing, and safe refusal when data is unavailable.

`POST /chat` cannot return `ChatResponse`. The repository performs no scientific query and always raises. `no_data` is modelled but unreachable. See [API contract](API_CONTRACT.md).

## 7. Scientific policy

### Prepared data

The final schema and QC choices are unresolved. At minimum, preserve float identifier, time, coordinates, consistent depth, adjusted temperature/salinity where acceptable, and enough QC/provenance information to audit filtering.

### Baseline separation

Production and validation baselines must be separately versioned and stored. A validation baseline cannot support live answers; a production baseline cannot be used as independent validation evidence.

### Anomaly and confidence

Current project policy:

- `|z| < 1.5`: normal;
- `1.5 ≤ |z| < 2.5`: mild positive/negative;
- `|z| ≥ 2.5`: strong positive/negative;
- 1–5 profiles: low; suppress severity;
- 6–20: medium; provisional;
- 21+: high; full severity may be shown.

Skip scoring for non-positive baseline standard deviation or no supporting profiles. These thresholds are project policy, not a universal scientific standard, and still require data-specific validation.

## 8. Required real success content

Every successful real-data response must include:

- source and dataset version;
- query type and validated parameters;
- chart-ready data;
- aggregation method;
- exact date window;
- radius or named region definition;
- profile count, coverage, and confidence;
- parser used;
- optional anomaly with production baseline period/mean/std and explanation; and
- shallow-water proxy caveat where relevant.

No illustrative value may be copied into a real response fixture merely to unblock integration.

## 9. Repository structure

```text
FloatChat/
├── frontend/                  accepted illustrative React app
├── backend/
│   ├── app/api/               HTTP routes and safe error mapping
│   ├── app/services/          parser, data boundary, anomaly policy
│   └── tests/                 backend unit/API tests
├── data/
│   ├── raw/                   local source inputs; ignored by default
│   ├── processed/             planned query-ready artifacts
│   ├── baselines/production/  planned serving baselines
│   ├── baselines/validation/  planned evaluation baselines
│   └── manifest.schema.json
├── scripts/                   frontend boundary check; scientific scripts planned
├── deploy/                    Dockerfile
├── demo/                      planned cached/screenshot artifacts
├── docs/                      synchronized documentation and evidence log
├── compose.yaml
└── Makefile
```

## 10. Development workflow

Prerequisites: Node.js ≥22.13, Python ≥3.11, and `make`. The container runtime uses Python 3.12.

```bash
make setup
make dev-web
make dev-api
make check
make container
```

Run web and API development processes in separate terminals. The web interface is at `http://localhost:3000`; API docs are at `http://localhost:8000/docs`.

Configuration is server-side. `.env.example` lists environment, data/static paths, and planned LLM settings. Current backend settings load only environment, data directory, and static directory; the LLM fields have no effect.

## 11. Testing and evidence

The repository has frontend static/render checks, backend parser/anomaly/API/health tests, linting, and GitHub Actions. These checks verify code boundaries, not scientific correctness, live provider behaviour, container deployment, projector usability, or rehearsals.

The evidence CSV currently has no result rows. Therefore no parser accuracy, heatwave validation, deployment, cache, or rehearsal result is claimable. See [Evidence and claim gate](evidence/README.md).

## 12. Deployment status

The multi-stage Dockerfile builds the frontend and runs FastAPI; Compose mounts `data/` read-only. This is a recipe, not a verified deployment. Hugging Face Spaces or any other host is only an option until selected and tested.

## 13. Known issues and technical debt

### Critical

- No reviewed ARGO data, manifest, production baseline, or validation baseline.
- No preprocessing/baseline/validation scripts or scientific repository query implementation.
- `/chat` has no success path.

### High

- Frontend and backend response models diverge and are not integrated.
- No `no_data` runtime path or distinct frontend API errors.
- Readiness does not validate manifest schema/hashes/provenance/scientific validity.
- No evidence/cached fallback/release acceptance exists.

### Medium

- Optional LLM configuration is listed but not loaded or implemented.
- Query matching is duplicated between frontend and backend.
- Backend response duplicates query type/parser fields.
- Suggested-query behaviour remains a product decision because the accepted UI omits chips.

### Low

- Formal accessibility, responsive-browser, and projector acceptance are unrecorded.
- Root DOCX references may be stale relative to synchronized Markdown.

## 14. Important decisions

- Use one frontend, one API, file-based prepared data, offline scientific work, and one container. See [ADR 0001](adr/0001-single-service-file-data.md).
- Preserve the accepted frontend and integrate contract-first.
- Make the deterministic parser sufficient for core pinned flows; the LLM is optional.
- Keep production and validation baselines independent.
- Prefer scope cuts over infrastructure expansion.
- Treat safe failures and negative evidence as valid outcomes.

## 15. Definition of done

- Reviewed data source/licence/provenance/QC and versioned subset are recorded.
- Production and validation baselines are separate, reproducible, and hashed.
- Profile and time-series/anomaly work end-to-end; regional average is either stable or explicitly cut.
- All real successes include full method, selection, data-sufficiency, parser, and caveat context.
- All typed failures are friendly and trace-free.
- Scientific validation and any parser evaluation store exact positive/negative results.
- Accepted UI passes browser, accessibility-focused, narrow-screen, and projector checks.
- One-container and sanitized cached fallback paths are verified.
- Rehearsal results and pitch claims trace to the evidence log.

## 16. Roadmap and future direction

The immediate dependency chain is:

```text
data decisions
  → preprocessing + manifest
  → separate baselines
  → repository queries
  → real API fixtures
  → accepted UI integration
  → validation + container + cache + rehearsal
```

See the [synchronized roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md). Long-term features are intentionally unscheduled until the real-data core has release evidence.

## 17. References

External scientific/source references retained from the supplied project material:

1. [Argo data sources](https://argo.ucsd.edu/data/).
2. [How to use Argo profile files](https://argo.ucsd.edu/data/how-to-use-argo-files/).
3. [INCOIS Indian ARGO Floats ERDDAP dataset](https://erddap.incois.gov.in/erddap/tabledap/Indian_ARGO_Floats.html).
4. Kelley, D. E. et al. (2021), “argoFloats: An R Package for Analyzing Argo Data,” *Frontiers in Marine Science* 8:635922.
5. Holbrook, N. J. et al. (2019), “A global assessment of marine heatwaves and their drivers,” *Nature Communications* 10, 2624.

These references support background/scientific planning, not claims that the current implementation has ingested or validated a dataset.
