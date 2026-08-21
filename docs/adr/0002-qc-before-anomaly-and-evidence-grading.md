# ADR 0002: QC filtering before anomaly scoring and multi-signal evidence grading

- Status: Accepted in target architecture
- Date: 21 August 2026
- Implementation status: Structural boundaries only

## Context

An unusual raw ARGO value may be a sensor/profile quality problem or a genuine oceanographic event. Profile count alone also cannot justify trust when baseline depth, distinct-float coverage, spatial spread, or QC pass rate is weak.

## Decision

1. Retrieve matching records without making a trust judgment.
2. Apply an explicit ARGO QC/data-mode policy and preserve retained/excluded audit counts.
3. Allow only QC-passed observations into aggregation and anomaly scoring.
4. Grade the result as `Insufficient`, `Indicative`, or `Supported` using valid-profile count, baseline `n`, distinct-float/spatial coverage, and QC pass rate.
5. Surface actual intermediate values in a computation-transparency/provenance panel.

The only fixed grade threshold currently approved is fewer than five valid current profiles → `Insufficient`. Other thresholds require reviewed-data analysis and one centrally documented policy.

## Consequences

- A data-quality warning and an ocean-event anomaly are separate outputs.
- Legacy `low`/`medium`/`high` confidence is retired from the target API.
- Sparse-profile Z-scores are not labelled marine heatwaves.
- Quantitative evaluation must compare the full pipeline against simpler/unfiltered alternatives on the same labels and data.
- Current `anomaly.py`, frontend confidence UI, and models require contract-first migration; this ADR does not claim that migration is complete.
