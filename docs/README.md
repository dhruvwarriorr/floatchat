# FloatChat-Lite documentation index

> Rev. B synchronization: 21 August 2026

## Target authority

1. [Product requirements Rev. B](prd.md)
2. [Architecture Rev. B](ARCHITECTURE.md)
3. [ADR 0002: QC before anomaly and evidence grading](adr/0002-qc-before-anomaly-and-evidence-grading.md)

These describe the target. Current implementation status comes from source/tests/artifacts and is summarized below; target requirements are never assumed complete.

## Current-state entry points

- [Project documentation](PROJECT_DOCUMENTATION.md)
- [Detailed project handbook](FloatChat-Lite_Project_Documentation.md)
- [Feature status](feature.md)
- [API contract and migration](API_CONTRACT.md)
- [Interface design and current/target differences](design.md)

## Delivery and evidence

- [Synchronized roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md)
- [Delivery phases](phases.md)
- [Executable todo](todo.md)
- [Critical-path plan](HACKATHON_EXECUTION.md)
- [Demo runbook](DEMO_RUNBOOK.md)
- [Evidence and claim gate](evidence/README.md)

## Decisions and references

- [ADR 0001: single service/file data](adr/0001-single-service-file-data.md)
- [Supplied references](reference/README.md)

## Standard vocabulary

Use: QC Filter/data-quality path, Anomaly Model/ocean-event path, Evidence Grade (`Insufficient`/`Indicative`/`Supported`), computation-transparency/provenance panel, valid/excluded observations, distinct floats, QC pass rate, production baseline, validation baseline, shallow-water SST proxy, deterministic parser, and cached fallback.

Do not use profile-count confidence as the target trust judgment, call a Z-score result a marine heatwave, or describe provenance reporting as model-attribution XAI.
