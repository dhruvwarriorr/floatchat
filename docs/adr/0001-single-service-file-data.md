# ADR 0001: Single service with file-based scientific data

- Status: accepted for the hackathon build
- Date: 2026-08-20

## Decision

Use one React/Vite frontend, one FastAPI application, offline Python preprocessing, versioned Parquet/CSV artifacts, precomputed production/validation baselines, and one container. Do not add a database server, queue, microservice split, or orchestration framework.

## Why

The team must prove an end-to-end, explainable scientific path under tight time constraints. A single runtime artifact reduces deployment, networking, schema, and ownership failure modes while retaining clear internal component boundaries.

## Consequences

- Data refresh is an explicit offline build, not a live request feature.
- Runtime readiness depends on a reviewed manifest and local artifacts.
- Larger-scale concurrency, account storage, and asynchronous processing remain outside the hackathon scope.
- If the data path falls behind, scope is reduced before architecture is expanded.
