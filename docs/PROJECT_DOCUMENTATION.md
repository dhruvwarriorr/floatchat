# FloatChat-Lite project documentation

> Central entry point
> Last synchronized: 21 August 2026

## Project overview

FloatChat-Lite is an explainable Indian Ocean ARGO question-answering demonstration. Today, the repository contains an accepted **illustrative** React interface and a **partial** FastAPI safety foundation. It does not contain query-ready ARGO data, scientific preprocessing scripts, baseline artifacts, real repository queries, frontend/API integration, or release evidence.

## Goals

- Deliver reviewed real-data profile and time-series/anomaly flows.
- Show source, method, selection, data sufficiency, confidence, parser, and caveats.
- Preserve deterministic operation when an optional LLM is unavailable.
- Keep the stack small, stateless, file-based, and evidence-first.

## Current status

| Area | Status | Summary |
| --- | --- | --- |
| Illustrative frontend | ✅ | React/Vite/Recharts, four local flows, static map, confidence/explanation states. |
| Backend foundation | 🟡 | Models, health, narrow rule parser, anomaly policy, safe errors, tests. |
| Scientific data and repository | 🔴 | Missing; `/chat` cannot return success. |
| UI/API integration | 🔴 | Missing; contracts differ. |
| Deployment/evidence | 🟡 / 🟠 | Recipe exists; no verified runtime, data, cache, or rehearsal. |

## Major features

- Implemented illustrative UI: depth profile, shallow-water SST/anomaly context, salinity regional view, warming direction.
- Implemented narrow deterministic parser for the four pinned phrase families.
- Partially implemented typed API, health, safe failures, and anomaly/confidence policy.
- Planned/blocked real preprocessing, Parquet repository, baselines, explanations, API success, integration, evaluation, and cached demo.

See [Feature status](feature.md) for purpose, flow, implementation, dependencies, status, and remaining work.

## Technology stack

- Frontend: React 19, TypeScript 5.9, Vite 8, Recharts, Lucide React, local variable fonts.
- Backend: Python ≥3.11, FastAPI, Pydantic, Uvicorn.
- Planned scientific path: xarray/pandas/NumPy/PyArrow and Parquet.
- Runtime: one container; no database, auth, queue, or microservices.

## Architecture

Current frontend and backend are separate: the UI reads bundled illustrative objects, while the API safely refuses scientific success. The target connects the same accepted UI to one FastAPI boundary backed by offline-prepared artifacts and production baselines. See [Architecture](ARCHITECTURE.md) and [ADR 0001](adr/0001-single-service-file-data.md).

## Repository structure

```text
frontend/   accepted illustrative UI
backend/    API models/routes/services/tests
data/       planned scientific artifacts and manifest schema
scripts/    scientific entrypoints planned
deploy/     one-container recipe
demo/       cached fallback placeholders
docs/       synchronized documentation and evidence
```

## Development workflow

Requirements: Node.js ≥22.13, Python ≥3.11, and `make`.

```bash
make setup
make dev-web   # terminal 1
make dev-api   # terminal 2
make check
make container
```

The frontend intentionally does not call the API yet. See the [project handbook](FloatChat-Lite_Project_Documentation.md) for configuration and command caveats.

## Implementation status

Core engineering scaffolding is present; scientific/product completion is not. The next milestone is one reviewed ARGO profile artifact and repository query—not LLM expansion or UI redesign.

## Known issues and technical debt

- Critical: no data/manifest/baselines/scripts/repository success.
- High: incompatible frontend/backend contracts; no end-to-end path or release evidence.
- Medium: existence-only readiness, duplicated phrase matching, inactive LLM environment placeholders.
- Needs verification: container runtime, hosting, accessibility, projector, scientific validation, parser accuracy, and rehearsals.

Detailed severity and context are in the [project handbook](FloatChat-Lite_Project_Documentation.md#13-known-issues-and-technical-debt).

## Testing status

Frontend and backend automated checks and CI are present. They do not prove scientific validity, live integration, deployment, browser/projector acceptance, or demo readiness. The evidence log contains no result rows.

## Deployment status

A Dockerfile and Compose recipe exist. No hosting target or successful release run is verified. Without ready data, readiness correctly fails.

## Roadmap

1. P0: freeze data/QC/spatial decisions and preprocess a reviewed subset.
2. P0: build separate production/validation baselines.
3. P0: implement profile/time-series repository and API success/no-data.
4. P1: integrate the accepted frontend through frozen real fixtures.
5. P1: validate science/failures, container, cached fallback, projector, and rehearsal.
6. P2: optionally add one LLM adapter and regional average if the core is stable.

See the [detailed synchronized roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md).

## Important decisions

- Preserve the accepted UI.
- Use deterministic parsing for the core; LLM parsing is optional.
- Keep scientific preprocessing offline and file-based.
- Keep production and validation baselines separate.
- Prefer honest scope cuts and negative evidence over unsupported completion claims.

## Future direction

Multilingual, other ocean domains, memory/accounts, databases, mobile/WhatsApp, and scaling are unscheduled. Revisit only after the core has verified release evidence and a demonstrated need.

## Documentation index

Use [docs/README.md](README.md) for the full document map and authority rules.
