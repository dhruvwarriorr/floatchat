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

- **Provider/provenance:** Core Argo profile NetCDF files handled by the INCOIS
  Data Assembly Centre and distributed through an official Argo GDAC.
- **Collection:** `dac/incois`, profile files only; no BGC, trajectory,
  technical, gridded, satellite, model, or value-added product.
- **Version:** a dated GDAC snapshot or a file list plus per-file SHA-256 hashes
  recorded in `data/manifest.json` at preprocessing time.
- **Licence/access:** Argo data are freely available without restriction. The
  product must include the Argo acknowledgement and snapshot DOI when one is
  used. Source files also retain their provider metadata and disclaimers.
- **Discovery only:** INCOIS ERDDAP dataset `Indian_ARGO_Floats` may be used to
  find candidate records. Its flattened export is not the production input
  because it does not expose `DATA_MODE` or position QC and can omit adjusted
  values needed by this policy.

If INCOIS-DAC profiles do not cover all pinned selections, preprocessing must
fail with a coverage report. Expanding to other DACs requires a policy revision;
the application must not silently change its source.

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
- `PLATFORM_NUMBER`, `CYCLE_NUMBER`, `DIRECTION`, and a derived stable
  `profile_id = PLATFORM_NUMBER:CYCLE_NUMBER:DIRECTION`;
- profile time, `JULD_QC`, latitude, longitude, and `POSITION_QC`;
- pressure plus `PRES_QC`, `PRES_ADJUSTED`, `PRES_ADJUSTED_QC`, and adjusted
  pressure error when supplied;
- raw and adjusted `TEMP` and `PSAL`, their corresponding QC flags, and
  adjusted errors when supplied;
- `DATA_MODE` and parameter-specific data mode when the source format supplies
  it;
- selected value, selected QC flag, selected value kind (`raw` or `adjusted`),
  selection reason, exclusion reason, and all spatial/grouping keys;
- source row/profile index so an output can be traced back without relying on
  row order.

Missing required identity, time, position-QC, pressure, parameter-QC, or
data-mode fields make a file invalid. Missing adjusted values are allowed only
where the rule below explicitly permits raw real-time display.

## 3. QC and value precedence

Data quality and ocean anomaly are separate decisions. QC rejection is never
an anomaly label and rejected observations never reach anomaly scoring.

### Accepted flags

- `JULD_QC`, `POSITION_QC`, pressure QC, and the selected parameter QC must all
  equal Argo flag `1` (good data).
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
5. Pressure and the requested parameter must independently pass the rule.

The source mode, selected field, selected QC flag, retained/excluded counts,
and exclusion reason remain visible to provenance composition.

## 4. Selection and aggregation

### Profile identity and duplicates

`PLATFORM_NUMBER + CYCLE_NUMBER + DIRECTION` identifies a profile. Only
ascending profiles (`DIRECTION=A`) enter aggregates. Descending profiles remain
auditable but are excluded. Exact duplicate observation rows are collapsed.
Conflicting duplicates are resolved by `D` over `A` over `R`, then newest
`DATE_UPDATE`; a remaining conflicting tie is a preprocessing error rather than
an arbitrary selection.

### Mumbai depth profile

- Select July 2024 ascending profiles inside `mumbai-50km`.
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

- Select ascending profiles in the frozen box during 2023.
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

`data/raw/Indian_ARGO_Floats_2f13_9046_0763_U1787326430188.nc` was inspected on
21 August 2026 and rejected as the production subset.

- SHA-256: `0bc4974eb7628fc67d66cf02dc9c2c0d509cacabc7d65ca92e10e1524748f5f4`
- 364 observation rows, four profiles, and four floats;
- time coverage: 16–23 April 2025 only;
- latitude: 15.884805 S to 1.732282 S;
- longitude: 62.891297 E to 85.176593 E;
- all raw pressure, temperature, and salinity flags are `1`;
- adjusted pressure, temperature, and salinity values are entirely missing;
- `DATA_MODE` and `POSITION_QC` are absent.

It covers none of the frozen date/location requirements and cannot support
historical adjusted-value precedence or grade-threshold review. It remains a
useful negative ingestion fixture but must not be marked ready.

## 11. Phase 0 acceptance status

- [x] Source, licence, subset, regions, radii, and date range are recorded.
- [x] Accepted QC flags and value/data-mode precedence are explicit.
- [x] Aggregation and proxy rules are testable rather than implied.
- [x] Production and validation baseline policies cannot overlap operationally.
- [ ] Every Evidence Grade condition has a dataset-reviewed threshold and reason.
- [x] Evaluation labels and denominators are reproducible.
- [x] Frontend library direction is recorded without redesigning the accepted UI.

**Blocking input:** install the correct 2015–2024 INCOIS-DAC profile subset,
including `DATA_MODE`, position/time QC, raw and adjusted values/QC fields. Then
generate and review the coverage distributions and amend Section 6.

## 12. Change log

- **0.1 — 2026-08-21:** froze source, scope, schema, QC/value precedence,
  spatial and aggregation rules, baseline separation, anomaly bands, reason
  codes, evaluation denominators, frontend direction, and ownership roles;
  rejected the installed one-week ERDDAP export; left dataset-derived grade
  thresholds fail-closed pending a correct subset.
