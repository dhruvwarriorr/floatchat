# ADR 0001: Single service with file-based scientific data

- Status: Accepted for the hackathon build
- Date: 20 August 2026
- Last verified: 21 August 2026

## Context

FloatChat-Lite must demonstrate an explainable scientific request path with a small team and limited delivery time. The application is read-heavy, stateless, and has no account or chat-history requirement. Scientific preprocessing must be reproducible and must not run during a live request.

## Decision

Use:

- one React/TypeScript/Vite frontend;
- one FastAPI/Pydantic application;
- offline Python preprocessing;
- versioned Parquet artifacts;
- separate precomputed production and validation baselines; and
- one container that serves the built frontend and API.

Do not add a database server, queue, microservice split, orchestration framework, authentication, or persistent chat state to the core build.

## Current implementation alignment

- ✅ `frontend/`, `backend/`, `deploy/Dockerfile`, and `compose.yaml` follow the single-application direction.
- ✅ `data/` separates processed data and production/validation baselines.
- 🟡 The container recipe exists but has no recorded runtime/deployment acceptance.
- 🔴 Scientific preprocessing, artifacts, manifest, and repository queries are not implemented.

## Consequences

- Data refresh is an explicit offline build, not a live feature.
- Runtime readiness depends on a reviewed manifest and local artifacts.
- File existence alone is insufficient; provenance, hashes, QC, and scientific checks remain release gates.
- Larger-scale concurrency, account storage, and asynchronous processing are outside the hackathon scope.
- If the data path falls behind, reduce feature/coverage scope before expanding architecture.

## Revisit when

Reconsider file-based storage only after measured workload, artifact size, update frequency, or multi-user requirements demonstrate that it is inadequate. Do not schedule a database migration merely as roadmap polish.
