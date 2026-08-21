# FloatChat-Lite documentation index

> All `docs/**/*.md` files were synchronized against the repository on 21 August 2026.

## Start here

1. [Project documentation](PROJECT_DOCUMENTATION.md) — concise current-state entry point.
2. [Project handbook](FloatChat-Lite_Project_Documentation.md) — detailed scope, policies, status, structure, workflow, issues, and definition of done.
3. [Synchronized roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md) — completed, next, planned, blocked, and long-term work.

## Product and design

- [Product requirements](prd.md) — goals, non-goals, requirements, acceptance evidence, risks, and decisions.
- [Feature status](feature.md) — each major feature’s purpose, flow, implementation, dependencies, status, and remaining work.
- [Interface design](design.md) — accepted current UI and target integration behaviour.

## Engineering

- [Architecture](ARCHITECTURE.md) — current and target runtime, component boundaries, data, security, and deployment.
- [API contract](API_CONTRACT.md) — exact reachable endpoints/errors and planned success contract.
- [ADR 0001: single service and file-based data](adr/0001-single-service-file-data.md).

## Delivery and operations

- [Delivery phases](phases.md) — dependency-ordered milestone model.
- [Executable todo](todo.md) — checkable priority list.
- [Critical-path hackathon plan](HACKATHON_EXECUTION.md) — compressed execution from the current state.
- [Demo runbook](DEMO_RUNBOOK.md) — release gate, deployment/judging checks, and recovery.
- [Evidence and claim gate](evidence/README.md) — rules for recorded results.

## References

- [Supplied reference artifacts](reference/README.md) — relationship between root DOCX files and synchronized Markdown.

## Source-of-truth order

When documents and implementation disagree, use:

1. Current source, configuration, tests, and actual artifacts.
2. This index and [Project documentation](PROJECT_DOCUMENTATION.md).
3. Detailed architecture/API/feature documents.
4. Roadmap and planning documents for future work.
5. Root DOCX files as retained references only.

`evidence/evidence-log.csv` is authoritative for observed results and pitch/release claims. A build or test statement outside that log is not scientific, deployment, provider, projector, or rehearsal evidence.

## Status vocabulary

- ✅ Implemented
- 🟡 Partially implemented
- 🔵 In development (only when active work is evidenced)
- 🟠 Planned
- 🔴 Blocked
- ⚪ Needs verification

Use “illustrative frontend,” “deterministic parser,” “LLM parser adapter,” “scientific repository,” “prepared profile artifact,” “production baseline,” “validation baseline,” “shallow-water SST proxy,” “data sufficiency,” and “cached fallback” consistently.
