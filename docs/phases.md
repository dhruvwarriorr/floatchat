# FloatChat-Lite delivery phases

> Rev. B synchronization: 21 August 2026

| Phase | Goal | Status | Exit gate |
| --- | --- | --- | --- |
| 0. Foundation | Current UI/API plus Rev. B structural ownership | 🟡 | Structure/checks exist; no real scientific success. |
| 1. Policy and data | Freeze QC/grade/labels and build reviewed artifacts | 🔴 blocked | Reproducible profiles, baselines, manifest, labels. |
| 2. QC-gated backend | Retrieval → QC → anomaly → grade → provenance | 🔴 blocked by 1 | Target API fixtures and full stage-order tests. |
| 3. UI integration | Accepted UI renders target response | 🔴 blocked by 2 | QC warning, grades, panel, typed failures in browser. |
| 4. Evaluation | Three-method comparison and parser/API reliability | 🔴 blocked by 2/3 | Reproducible reports and reviewed evidence rows. |
| 5. Release | Container/cache/projector/recovery/rehearsal | 🟠 planned | Frozen live/local and cached paths. |

## Phase 0: foundation

Current source includes illustrative UI, deterministic parser, safe errors/health, legacy anomaly tests, CI, container recipe, and structural QC/evidence/explain/evaluation boundaries. It does not meet Rev. B behaviour.

## Phase 1: policy and data

Freeze source/licence, schema, QC flags, adjusted/raw/data-mode precedence, spatial rules, baseline and grade thresholds, proxy cutoff, labeling methodology, and metric denominators. Build reviewed Parquet, production/validation baselines, manifest, and small frozen evaluation fixtures.

## Phase 2: QC-gated backend

Implement retrieval without judgment; mandatory auditable QC; QC-passed aggregation/anomaly; evidence grade/reasons; provenance panel; success/no-data/QC-warning/error mapping. Verify rejected records never enter anomaly scoring.

## Phase 3: UI integration

Freeze real fixtures, migrate contracts, resolve frontend-library divergence, preserve accepted interactions, and render typed errors, quality warning, grade-governed anomaly, parser disclosure, and expandable evidence panel.

## Phase 4: quantitative evaluation

Run the same frozen labels/subset through the three anomaly methods. Run the 20–30-query reliability suite with LLM explicitly disabled plus simulated failures. Report required metrics and limitations; review/log exact results.

## Phase 5: release

Verify container/local runtime, sanitized full-contract cache, browser/projector/accessibility-focused behaviour, network/provider/data recovery, and recorded rehearsals. Freeze only after claims trace to evidence.
