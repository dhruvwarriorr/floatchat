# FloatChat-Lite scientific and evaluation policy

**Policy version:** 0.1  
**Decision date:** 21 August 2026  
**Status:** Frozen except for dataset-derived Evidence Grade thresholds  
**Applies to:** preprocessing, QC, retrieval, baselines, anomaly scoring,
evidence grading, evaluation, API contracts, and integrated UI results

This document is the Phase 0, Week 1 decision record. Later code and fixtures
must cite the policy version. A policy change requires a dated entry in the
change log; measured thresholds must not be adjusted merely to improve a demo
result.

## 1. Product scope and source

The MVP supports exactly these pinned real-data questions:

1. temperature profile near 19.0 N, 72.8 E during July 2024;
2. shallow-water temperature time series near 19.0 N, 72.8 E for 2015–2024,
   with anomaly context for 2024;
3. upper-ocean salinity average in the Bay of Bengal during 2023.

The accepted Arabian Sea warming flow remains illustrative. It is not part of
the first real-data contract and must not be presented as a verified result.

### Frozen source

- **Provider/provenance:** INCOIS Indian ARGO CSV exports supplied by the team
  under `data/raw/`. No external source is fetched at request time.
- **Collection:** core temperature/salinity profile rows only; no BGC,
  trajectory, technical, gridded, satellite, model, or value-added product.
- **Format contract:** each source file has a field-name first row and units
  second row. Preprocessing skips the units row, reads identifiers and QC values
  as strings, rejects a duplicate header within the data, and records each file
  name and SHA-256 in `data/manifest.json`.
- **Required CSV columns:** `platform_number`, `cycle_number`, `time`,
  `latitude`, `longitude`, `pres`, `temp`, `temp_qc`, `temp_adjusted`,
  `temp_adjusted_qc`, `psal`, `psal_qc`, `psal_adjusted`,
  `psal_adjusted_qc`, `data_mode`, and `position_qc`.
- **Licence/access:** the manifest records the INCOIS export URL/access date and
  the licence text supplied with the export. The product includes the required
  Argo acknowledgement when it uses Argo data.

If the reviewed CSV exports do not cover all pinned selections, preprocessing
must fail with a coverage report. Replacing INCOIS or silently adding a second
source requires a policy revision.

### Frozen spatial and temporal subset

| Selection ID | Geometry | Time | Intended query |
|---|---|---|---|
| `mumbai-50km` | great-circle distance no more than 50.0 km from 19.0 N, 72.8 E | 2015-01-01T00:00:00Z through 2024-12-31T23:59:59Z | profile and shallow time series |
| `bay-of-bengal` | 5.0–22.0 N and 80.0–100.0 E, inclusive | 2015-01-01T00:00:00Z through 2024-12-31T23:59:59Z | 2023 salinity and historical grouping |

Coordinates are evaluated from the profile position, not deployment position.
Longitude is normalized to -180…180 before selection. Boundary points are
included. Distance uses the haversine formula with Earth radius 6,371.0088 km.

## 2. Required audit schema

Every prepared observation retains these source or derived fields:

- source file path, source file SHA-256, dataset version, and policy version;
- `platform_number`, `cycle_number`, and a derived stable
  `profile_id = platform_number:cycle_number`;
- profile time, latitude, longitude, and `position_qc`;
- pressure (`pres`), used only as a depth proxy because the export does not
  include a separate pressure-QC or adjusted-pressure field;
- raw and adjusted `temp` and `psal` plus their corresponding QC flags;
- `data_mode`;
- selected value, selected QC flag, selected value kind (`raw` or `adjusted`),
  selection reason, exclusion reason, and all spatial/grouping keys;
- source row/profile index so an output can be traced back without relying on
  row order.

Missing required identity, time, position-QC, pressure, parameter-QC, or
data-mode columns make a file invalid. Missing adjusted values are allowed only
where the rule below explicitly permits raw real-time display. The absence of a
separate pressure/time QC field is recorded in provenance; it is not fabricated.

## 3. QC and value precedence

Data quality and ocean anomaly are separate decisions. QC rejection is never
an anomaly label and rejected observations never reach anomaly scoring.

### Accepted flags

- `position_qc` and the selected parameter QC must both equal Argo flag `1`
  (good data). The CSV exports do not include a separate time or pressure QC.
- Flags `0`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, blank, missing, or unknown
  are excluded from the scientific aggregate and retained in audit counts.
- A future decision to accept `2` (probably good) requires a policy revision
  and a repeated method comparison; it is not an automatic fallback.

### Historical value precedence

1. For `DATA_MODE=D`, use only the adjusted value and its adjusted QC flag.
2. For `DATA_MODE=A`, use only the adjusted value and its adjusted QC flag.
3. For `DATA_MODE=R`, raw QC=1 values may be shown in a non-anomaly profile
   response, explicitly marked real-time. They are excluded from production
   baselines, validation baselines, regional averages, trends, and anomaly
   scoring.
4. Never substitute raw data when mode `A` or `D` has a missing or rejected
   adjusted value. Exclude it and record the reason.
5. The requested parameter must pass the rule; pressure is a depth proxy whose
   separate QC is unavailable in this CSV format.

The source mode, selected field, selected QC flag, retained/excluded counts,
and exclusion reason remain visible to provenance composition.

## 4. Selection and aggregation

### Profile identity and duplicates

`platform_number + cycle_number` identifies a profile in the CSV export. Exact
duplicate observation rows are collapsed. Conflicting duplicates are resolved by
`D` over `A` over `R`, then source-file modification time recorded in the
manifest; a remaining conflicting tie is a preprocessing error rather than an
arbitrary selection. The CSV export has no direction field, so direction-based
selection is not applied and this source limitation is reported in provenance.

### Mumbai depth profile

- Select July 2024 profiles inside `mumbai-50km`.
- Apply QC and value precedence before aggregation.
- Use pressure in decibar as the displayed depth proxy and label it as such.
- Bin selected values into `[0,10)`, `[10,25)`, `[25,50)`, `[50,100)`,
  `[100,200)`, `[200,300)`, and `[300,500]` dbar.
- Within each profile/bin, take the median so densely sampled profiles do not
  dominate. Across profile medians, take the median. Return each bin's profile
  count and distinct-float count. Do not interpolate missing bins.

### Shallow-water temperature time series

- From each retained profile, select the shallowest valid adjusted temperature
  observation with pressure from 0 through 10 dbar, inclusive.
- Do not interpolate to the surface. A profile without a valid observation in
  that range contributes no shallow value.
- Aggregate first to one value per profile, then to a calendar-month arithmetic
  mean. Annual display values are means of available monthly means and include
  the number of represented months.
- Label this quantity **shallow-water temperature proxy (0–10 dbar)**. It is
  neither skin temperature nor satellite SST.

### Bay of Bengal salinity

- Select profiles in the frozen box during 2023.
- For each profile, take the median of valid adjusted salinity observations
  from 0 through 100 dbar, inclusive.
- Compute monthly arithmetic means across profile medians. The annual answer is
  the mean of available monthly means so a heavily sampled month does not
  silently dominate.
- Report represented months, raw/valid profiles, distinct floats, and spatial
  coverage. If reviewed coverage is unstable, this query is cut from the MVP.

All statistics ignore only values excluded by an explicit rule. Rounding is for
presentation only: retain full precision in artifacts; display temperature to
0.1 °C, salinity to 0.1 PSU, pressure to 1 dbar, and z-score to two decimals.

## 5. Baselines and anomaly policy

### Production baseline

- Stored only under `data/baselines/production/` and tagged
  `baseline_type=production`.
- Built from retained adjusted `A`/`D` data from 2015–2023.
- Grouped by selection, parameter, and calendar month using the same per-profile
  aggregation as the current value.
- Stores mean, sample standard deviation, `n`, distinct floats, covered years,
  input artifact hash, and policy version.
- Runtime may read only this artifact. It is never independent validation
  evidence.

### Validation baseline

- Stored only under `data/baselines/validation/` and tagged
  `baseline_type=validation`.
- Built from retained adjusted `A`/`D` data from 2015–2018.
- Used only to score frozen evaluation cases from 2019–2024.
- Evaluation code must reject a production artifact; runtime code must reject a
  validation artifact. Separate paths, type tags, hashes, and tests enforce the
  boundary.

No z-score is emitted when baseline standard deviation is zero, baseline data
are missing, or the Evidence Grade is `Insufficient`.

### Anomaly labels

For a permitted z-score `z = (current - mean) / std`:

- `normal`: `abs(z) < 1.5`;
- `mild_positive`: `1.5 <= z < 2.5`;
- `mild_negative`: `-2.5 < z <= -1.5`;
- `strong_positive`: `z >= 2.5`;
- `strong_negative`: `z <= -2.5`.

These are transparent MVP alert bands, not a claim that the thresholds define
a climatological event. Output wording is **upper-ocean temperature anomaly**
or **salinity anomaly**. Sparse Argo profile z-scores must never be called a
marine heatwave.

## 6. Evidence Grade

The grade is based on current valid profiles, baseline `n`, distinct floats,
QC pass rate, and spatial coverage. It is separate from anomaly magnitude.

The existing rule is frozen:

- fewer than five valid current profiles => `Insufficient` with reason
  `valid_profiles_below_5`.

Other reason codes are frozen so contracts and tests can proceed:

- `baseline_n_below_minimum`;
- `distinct_floats_below_minimum`;
- `qc_pass_rate_below_minimum`;
- `spatial_coverage_below_minimum`;
- `baseline_std_zero`;
- `all_grade_conditions_met`.

Numeric minima for baseline `n`, distinct floats, QC pass rate, and spatial
coverage are deliberately **not frozen yet**. They must be set from a coverage
report over the correct 2015–2024 source subset, with distributions by query
family and month. Until then every real-data response is `Insufficient`, no
colored severity is shown, and no z-score is returned. This fail-closed rule
prevents an unresolved threshold from becoming an implicit confidence claim.

After review, one policy amendment must record the chosen values, distribution
table, reviewer, rationale, and rejected alternatives. Thresholds cannot be
selected to maximize attractive anomaly labels.

## 7. Evaluation labels and denominators

The unit of anomaly evaluation is one frozen `selection + parameter + calendar
month` case from 2019–2024. Every row stores source/build version, profile IDs,
reviewer, references, label, rationale, exclusions, and ambiguity state.

Ground-truth classes are:

- `normal_ocean_state`;
- `upper_ocean_anomaly`;
- `measurement_quality_problem`;
- `ambiguous_excluded`.

Labels must be created before method outputs are inspected. A label requires a
documented scientific reference or an independent manual review of the source
profiles and neighboring time/space context. QC flags alone may label a
measurement-quality problem but cannot prove a genuine ocean event. Ambiguous
cases remain in the fixture with their reason and are excluded from binary
precision/recall denominators. If credible event labels cannot be made, results
are `NEEDS VERIFICATION` and no accuracy claim is permitted.

For each of the regional-average, unfiltered-z, and full-pipeline methods:

- `eligible_cases`: all non-ambiguous frozen cases whose required inputs exist;
- `covered_cases`: eligible cases for which the method returns a decision;
- query coverage = `covered_cases / eligible_cases`;
- TP, FP, TN, and FN are counted only among covered binary cases, with
  `upper_ocean_anomaly` positive and `normal_ocean_state` negative;
- precision = `TP / (TP + FP)` and is undefined when the denominator is zero;
- recall = `TP / (TP + FN)` and is undefined when the denominator is zero;
- F1 is undefined when precision or recall is undefined, otherwise their
  harmonic mean;
- false-alert rate = `FP / (FP + TN)` and is undefined when the denominator is
  zero;
- measurement-quality cases are reported separately as rejected, falsely
  alerted, or uncovered and never silently merged into normal cases;
- every report includes raw counts and denominators, not percentages alone.

Parser coverage uses a separately frozen prompt fixture. Its denominator is all
fixture prompts; supported-query accuracy and unsupported-query rejection are
reported separately. Latency reports include run count, environment, mean, and
p95 without removing failed requests.

## 8. Frontend decision

The MVP keeps the accepted React/Vite/Recharts implementation and static local
geographic context. Plotly and Leaflet migration is deferred. This decision
does not claim the current illustrative UI is connected to real data or already
renders the target evidence contract. Contract integration requires reviewed
fixtures and explicit implementation work while preserving accepted behavior.

## 9. Ownership

Until named team members are recorded, the repository owner is accountable and
the following role owns each artifact:

| Area | Responsible role | Required review |
|---|---|---|
| Policy and scope | project lead | scientific/data lead |
| Source, preprocessing, manifest | scientific/data lead | evaluation lead |
| API, QC boundary, anomaly and grade services | backend lead | scientific/data lead |
| Accepted UI and later contract integration | frontend lead | project lead |
| Fixtures, labels, methods, metrics | evaluation lead | scientific/data lead |
| Evidence log, cached fallback, rehearsal | demo-evidence lead | project lead |

One person may hold several roles, but the evidence log must use the person's
name rather than only a role before a claim is approved for presentation.

## 10. Review of the currently downloaded file

The CSV exports present on 21 August 2026 use the required 16-column schema,
including `data_mode`, `position_qc`, raw/adjusted parameter values, and
parameter QC flags. They are valid source-format candidates but not yet the
production subset: they cover March 2024 and January–May 2025, not the frozen
2015–2024 period; their longitude coverage ends west of the Bay of Bengal
selection; and their coverage report has not yet been generated. They must not
be marked ready or used to choose Evidence Grade thresholds.

## 11. Phase 0 acceptance status

- [x] Source, licence, subset, regions, radii, and date range are recorded.
- [x] Accepted QC flags and value/data-mode precedence are explicit.
- [x] Aggregation and proxy rules are testable rather than implied.
- [x] Production and validation baseline policies cannot overlap operationally.
- [ ] Every Evidence Grade condition has a dataset-reviewed threshold and reason.
- [x] Evaluation labels and denominators are reproducible.
- [x] Frontend library direction is recorded without redesigning the accepted UI.

**Blocking input:** install the correct 2015–2024 INCOIS CSV subset, including
the required columns above. Then generate and review the coverage distributions
and amend Section 6.

## 12. Change log

- **0.1 — 2026-08-21:** froze source, scope, schema, QC/value precedence,
  spatial and aggregation rules, baseline separation, anomaly bands, reason
  codes, evaluation denominators, frontend direction, and ownership roles;
  left dataset-derived grade thresholds fail-closed pending a correct subset.
- **0.2 — 2026-08-21:** accepted INCOIS CSV exports as source input; documented
  their two-header-row format, required fields, and unavailable direction/time/
  pressure-QC fields; recorded that the currently installed monthly files do
  not yet meet the frozen coverage requirements.
