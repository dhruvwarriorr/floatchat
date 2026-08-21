# Architecture

## Outcome

FloatChat-Lite has one browser application and one FastAPI process. Scientific data preparation happens offline; live requests only validate, parse, filter prepared artifacts, compute bounded statistics, and compose an explanation.

```text
Browser (frontend/)
  -> POST /chat
FastAPI route
  -> validated parser result (LLM or deterministic fallback)
  -> data repository (versioned Parquet)
  -> anomaly policy (versioned production baseline)
  -> explanation templates
  -> validated response
Browser renders summary, chart, map, confidence, method, and disclosure
```

## Component boundaries

- `frontend/` owns input state, loading/error/success presentation, charts, map context, and accessibility. It does not parse queries or calculate scientific results.
- `backend/app/api/` owns HTTP validation, orchestration, status codes, and safe typed errors. It does not preprocess data.
- `backend/app/services/parser.py` owns the deterministic supported grammar. A future LLM adapter must produce the same validated `QueryParams` and fall back here.
- `backend/app/services/data.py` owns manifest readiness and prepared-data access. It must not invent fallback values.
- `backend/app/services/anomaly.py` owns z-score policy and confidence suppression. It does not choose visual colors.
- `scripts/` owns offline NetCDF preprocessing, baseline creation, validation, and parser evaluation.
- `data/` owns versioned artifacts and provenance. Production and validation baselines never mix.

## Deployment

`deploy/Dockerfile` builds the existing frontend, installs the API with scientific dependencies, and serves both from one Python container. The runtime receives data as files and secrets through environment settings. There is no database, queue, or separate frontend deployment in the core build.

## Current gap

The structure and API safety foundation exist, but the scientific repository intentionally refuses success until the team implements and validates the ARGO preprocessing/repository path. This is a visible checkpoint, not a hidden mock.
