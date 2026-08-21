# FloatChat-Lite Rev. B critical-path plan

> Starts from the current repository; structural placeholders are not implementation.

## H0–H4: freeze trust policy and data

- Freeze source/licence/subset, QC/data-mode/adjusted-value policy, regions/radii, grade thresholds, proxy cutoff, labels, and denominators.
- Implement auditable preprocessing and manually review profiles.
- Build separate baselines and manifest/hash checks.

Gate: one reproducible reviewed profile artifact retains QC/data-mode evidence.

## H4–H9: implement mandatory QC path

- Implement retrieval and QC Filter outputs: raw/valid/excluded counts, reasons, pass rate, distinct floats, warning.
- Prove rejected records cannot reach anomaly scoring.
- Implement profile query first and baseline boundary checks.

Gate: one real profile works and QC behavior is auditable.

## H9–H15: anomaly, grade, provenance, contract

- Refactor anomaly scoring over QC-passed aggregates only.
- Implement centralized Evidence Grade/reasons without inventing thresholds.
- Compose actual evidence panel and target response; add no-data/sparse/zero-std/trace tests.
- Freeze real response variants.

Gate: deterministic profile and time-series/anomaly work through HTTP with quality and grade explanations.

## H15–H19: UI and quantitative evaluation

- Integrate accepted UI after resolving library decision.
- Run three-method anomaly comparison and parser/API reliability suite.
- Record exact metrics/limitations; remove unsupported claims.

Gate: every metric has frozen inputs, denominator, report, and evidence row.

## H19–H24: release

- Verify container/local, cache complete contract responses, test projector/offline/provider recovery, rehearse, and freeze.

Scope cuts: narrow coverage → keep static map → cut regional average → cut optional LLM. Never cut QC, provenance, evidence grading, quantitative integrity, or rehearsal.
