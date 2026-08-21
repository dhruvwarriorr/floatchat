# FloatChat-Lite project documentation

> Central current-state entry point synchronized to Rev. B on 21 August 2026

## Overview

FloatChat-Lite targets explainable conversational exploration of Indian Ocean ARGO temperature and salinity. Rev. B separates measurement trust from ocean-event detection:

```text
retrieve → QC filter → aggregate → anomaly score → evidence grade → provenance panel
```

The current repository does not implement this scientific path. It contains an accepted illustrative frontend, a partial FastAPI safety scaffold, legacy profile-count confidence/anomaly policy, and new structural service/evaluation boundaries.

## Current status

| Area | Status | Reality |
| --- | --- | --- |
| Illustrative frontend | ✅ | React/Vite/Recharts, static Bhuvan map, four bundled flows, legacy confidence presentation. |
| API/parser/health | 🟡 | Pydantic boundary, narrow deterministic parser, safe missing-data errors; no success response. |
| QC Filter | 🟠 structure | `services/qc.py` ownership exists; rules/logic/tests absent. |
| Anomaly Model | 🟡 legacy | Isolated Z-score/profile-count policy exists; it is not QC-gated or integrated. |
| Evidence Grade | 🟠 structure | Target enum/panel fields and `services/evidence.py` exist; thresholds/logic/runtime absent. |
| Evidence panel | 🟠 structure | `services/explain.py` ownership exists; composition/UI absent. |
| Scientific artifacts/repository | 🔴 | No manifest, Parquet, baselines, or repository success path. |
| Quantitative evaluation | 🟠 structure | `evaluation/` workspace exists; fixtures/notebooks/results absent. |
| Integration/release evidence | 🔴 | Frontend does not call API; evidence log empty. |

## Target features

- Mandatory ARGO QC/data-mode filtering before anomaly scoring.
- Data-quality warning separate from anomaly classification.
- Z-score over QC-passed observations and production baselines only.
- Evidence grade from valid count, baseline `n`, distinct-float/spatial coverage, and QC pass rate.
- Expandable “Why this result?” panel with actual computed values and provenance.
- Reproducible three-method anomaly comparison and parser/API reliability evaluation.

See [features](feature.md), [API migration](API_CONTRACT.md), and [ADR 0002](adr/0002-qc-before-anomaly-and-evidence-grading.md).

## Stack and current/target differences

- Current frontend: React 19, TypeScript 5.9, Vite 8, Recharts, static local map image.
- Target authority names Plotly/Leaflet; migration is unresolved and not performed by structural synchronization.
- Backend: Python ≥3.11, FastAPI/Pydantic/Uvicorn; planned pandas/xarray/NumPy/PyArrow path.
- Storage: versioned Parquet and separate baseline artifacts; no database.
- Runtime: one container; hosting target remains unverified in current evidence despite the PRD target.

## Repository structure

```text
frontend/                         accepted illustrative UI
backend/app/api/                  HTTP orchestration
backend/app/services/
  parser.py                       current deterministic grammar
  data.py                         current readiness/refusal boundary
  qc.py                           planned mandatory QC stage
  anomaly.py                      current legacy anomaly policy
  evidence.py                     planned evidence-grade policy
  explain.py                      planned provenance-panel composer
backend/tests/fixtures/           future reviewed contract/QC fixtures
data/                             raw/processed/production/validation artifacts
scripts/                          deterministic scientific/evaluation commands
evaluation/
  fixtures/                       frozen labels/prompts/regions
  notebooks/                      reproducible comparisons/reliability
  results/                        generated reports; not evidence by default
docs/evidence/                    reviewed claim log
demo/                             sanitized cached responses/screenshots
deploy/                           one-container recipe
```

## Development

Requirements: Node.js ≥22.13, Python ≥3.11, and `make`.

```bash
make setup
make dev-web
make dev-api
make check
make container
```

The frontend is not integrated with the API. `make check` is an engineering gate, not scientific/reliability acceptance.

## Critical issues

- QC flags/data-mode/adjusted-value precedence and grade thresholds are not frozen.
- No reviewed dataset, manifest, baselines, repository queries, or API success exists.
- Target response models are structurally defined, but the anomaly scaffold and frontend still use legacy Low/Medium/High confidence and no runtime produces the target response.
- No quantitative labels, notebooks, results, provider reliability measurements, or response-latency measurements exist.
- Architecture/PRD target Plotly/Leaflet while accepted source uses Recharts/static map; an explicit decision is required.

## Roadmap

1. Freeze data/QC/grade/labeling policy.
2. Preprocess auditable ARGO fields and build independent baselines.
3. Implement/test QC Filter before anomaly scoring.
4. Implement evidence grade/reasons and provenance panel.
5. Return reviewed real API fixtures and integrate the accepted UI.
6. Run three-method scientific comparison and parser/API reliability evaluation.
7. Verify container, cache, projector, recovery, and rehearsal.

See the [synchronized roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md).

## Evidence status

No quantitative or release result is currently claimable because `docs/evidence/evidence-log.csv` has no result rows. See [evidence rules](evidence/README.md).
