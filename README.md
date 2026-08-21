# FloatChat-Lite

FloatChat-Lite is the hackathon implementation workspace for explainable conversational access to Indian Ocean ARGO observations.

The repository now separates the already-built interface from the API, scientific data, deployment, evaluation, and demo evidence. The existing frontend was moved intact into `frontend/`; its source, assets, tests, and behaviour were not changed during this restructure.

## Current implementation status

- `frontend/` is the existing Vite demonstration and still uses bundled illustrative responses.
- `backend/` is a runnable FastAPI foundation with health checks, the typed `/chat` boundary, a deterministic parser for the pinned query grammar, safe errors, tests, and explicit planned boundaries for QC filtering, evidence grading, and provenance composition.
- A real, quality-controlled ARGO subset and its production/validation baselines are **not yet present**. The API reports that state honestly instead of returning invented scientific results.
- `data/`, `scripts/`, `evaluation/`, `docs/`, and `demo/` establish the scientific, quantitative-evaluation, evidence, and release boundaries.

## Repository map

```text
frontend/                 Existing React + TypeScript + Vite app
backend/                  FastAPI contract, services, and tests
  app/services/qc.py      Planned ARGO data-quality path before anomaly scoring
  app/services/evidence.py Planned multi-signal evidence grading
  app/services/explain.py Planned computation-transparency/provenance panel
data/
  raw/                    Local NetCDF inputs; ignored by Git
  processed/              Versioned query-ready Parquet outputs
  baselines/production/   Baselines used by live query responses
  baselines/validation/   Separate known-event validation baselines
scripts/                  Planned deterministic scientific/evaluation entrypoints
evaluation/               Structure for frozen fixtures, notebooks, and generated reports
docs/                     Architecture, contract, execution, and runbook guidance
demo/                     Cached offline fallback and presentation captures
deploy/                   Single-container deployment
AGENTS.md                 Durable instructions for future contributors and agents
```

## Local setup

Requirements: Node.js 22.13+, Python 3.11+, and `make`.

```bash
make setup
```

Run the two development processes in separate terminals:

```bash
make dev-web
make dev-api
```

- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health/live`
- Data readiness: `http://localhost:8000/health/ready`

The frontend is intentionally not wired to the API yet; contract integration begins only after a query-ready ARGO subset and frozen response fixtures exist.

## Verification

```bash
make check
```

This runs the existing frontend tests plus backend lint and tests. It does not prove scientific validity, live-provider reliability, projector acceptance, deployment health, or demo rehearsal success; those require recorded evidence in `docs/evidence/`.

## Hackathon path

Read these before implementation:

1. [Architecture](docs/ARCHITECTURE.md)
2. [API contract](docs/API_CONTRACT.md)
3. [48-hour execution plan](docs/HACKATHON_EXECUTION.md)
4. [Demo runbook](docs/DEMO_RUNBOOK.md)
5. The supplied `FloatChat-Lite_Project_Documentation.docx` and `FloatChat-Lite_Detailed_Project_Roadmap.docx`

The immediate critical path is real ARGO subset preparation -> explicit QC filtering -> separate baselines -> one deterministic profile query -> evidence-grade/provenance contract -> frontend integration -> quantitative evaluation. Do not add new product scope before that path works.
