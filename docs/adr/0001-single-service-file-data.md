# ADR 0001: Single service with file-based scientific data

- Status: Accepted
- Date: 20 August 2026
- Last verified: 21 August 2026

## Decision

Use one React/Vite frontend, one FastAPI/Pydantic application, offline Python scientific processing, versioned Parquet artifacts, separate production/validation baselines, and one container. Do not add a database server, queue, microservice split, authentication, or persistent chat state to the core build.

## Rev. B refinement

File-based storage does not remove the need for explicit internal stages. Runtime scientific work remains separated into retrieval, QC/data-mode filtering, anomaly scoring, evidence grading, and provenance composition. Reproducible quantitative evaluation is stored under `evaluation/`, while observed claim evidence remains gated by `docs/evidence/evidence-log.csv`.

## Current alignment

- Frontend/backend/container and data directory boundaries exist.
- QC, evidence, and explain service files now mark target ownership but contain no scientific implementation.
- Scientific artifacts, preprocessing, repository queries, evaluation notebooks/results, and deployment acceptance remain absent.

## Consequences

- Data refresh and baseline construction are offline operations.
- Runtime readiness requires reviewed local artifacts but does not itself prove scientific validity.
- Larger-scale concurrency/storage is deferred until measured need exists.
- Reduce coverage/features before expanding infrastructure.
