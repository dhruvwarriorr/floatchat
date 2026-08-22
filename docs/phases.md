# FloatChat-Lite delivery phases

> Rev. B synchronization: 22 August 2026

| Phase | Goal | Status | Exit gate |
| --- | --- | --- | --- |
| 0. Foundation | Current UI/API plus Rev. B structural ownership | ✅ | Engineering foundation and checks implemented. |
| 1. Policy and data | Freeze QC/grade/labels and build reviewed artifacts | 🟡 artifacts built/review blocked | Correct pinned coverage plus named threshold/label review. |
| 2. QC-gated backend | Retrieval → QC → anomaly → grade → provenance | ✅ implemented/scientifically gated | Automated contract passes; grades remain fail-closed. |
| 3. UI integration | Accepted UI renders target response | ✅ implemented/browser pending | Automated build/tests pass; projector/browser evidence remains. |
| 4. Evaluation | Three-method comparison and parser/API reliability | 🟡 tools built | Reviewed anomaly labels, provider run, and evidence rows remain. |
| 5. Release | Container/cache/projector/recovery/rehearsal | 🟡 cache built/acceptance pending | Frozen live/local and cached paths. |

## Phase 0: foundation

Current source includes the accepted UI, typed API adapter, deterministic and
optional-provider parsers, safe errors/health, QC-gated scientific stages,
tests, container recipe, and evaluation/cache commands. Automated Rev. B
behavior is implemented; scientific and release acceptance gates remain.

## Phase 1: policy and data

Freeze source/licence, schema, QC flags, adjusted/raw/data-mode precedence, spatial rules, baseline and grade thresholds, proxy cutoff, labeling methodology, and metric denominators. Build reviewed Parquet, production/validation baselines, manifest, and small frozen evaluation fixtures.

## Phase 2: QC-gated backend

Implement retrieval without judgment; mandatory auditable QC; QC-passed aggregation/anomaly; evidence grade/reasons; provenance panel; success/no-data/QC-warning/error mapping. Verify rejected records never enter anomaly scoring.

## Phase 3: UI integration

Freeze real fixtures, migrate contracts, resolve frontend-library divergence, preserve accepted interactions, and render typed errors, quality warning, grade-governed anomaly, parser disclosure, and expandable evidence panel.

## Phase 4: quantitative evaluation

Run the same frozen labels/subset through the three anomaly methods. The
24-query reliability suite and five API scenarios now cover the disabled,
simulated-failure, sparse/no-data, malformed-date, and latency paths. Reviewed
anomaly labels and provider-enabled evidence are still required before metrics
can be logged or quoted.

## Phase 5: release

The local runtime and sanitized full-contract cache are verified. Verify the
container once a Docker daemon is available, then complete
browser/projector/accessibility-focused behaviour, network/provider/data
recovery, and recorded rehearsals. Freeze only after claims trace to evidence.
