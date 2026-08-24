# FloatChat-Lite feature status

> Synchronized to Rev. C, current source, and measured local artifacts on 24 August 2026

## Status summary

| Feature | Status | Current state | Remaining work |
| --- | --- | --- | --- |
| Integrated UI | ✅ implemented | Recharts plus Leaflet/CARTO, multi-parameter toggles, and typed `/chat` adapter | Browser/projector acceptance remains. |
| Data preprocessing/manifest | ✅ query-ready | 14.4M-row Arabian-Sea Parquet, hashes, coverage report, separate baselines | Licence review still blocks public redistribution. |
| Deterministic parser | ✅ implemented | 114 aliases plus named regions, coordinates, compound month/season dates, casual language, type/anomaly intent, safety rejection, and disclosed fallback | Generated report requires review. |
| Gemini LLM parser | 🟡 implemented/unaccepted | Schema-constrained server-only Gemini parser plus deterministic failover | Provider-enabled evidence requires a valid authorized credential. |
| Scientific retrieval | ✅ implemented | Column-pruned Parquet spatial/date/recurring-period filters and diagnostic `no_data` with a wider-search probe | Release data coverage remains incomplete. |
| QC Filter | ✅ implemented | Auditable position/mode/adjusted-QC/value rules | Manual profile review remains. |
| Anomaly Model | ✅ implemented/gated | Production-only Z-score over QC aggregates | External scientific validation remains. |
| Evidence Grade | ✅ implemented | Build-spec thresholds, multi-signal logic, suppression, and reasons | Thresholds remain marked as not externally validated. |
| Evidence panel | ✅ implemented | Actual counts, QC exclusions, selection, aggregation/bin counts, baseline match, grade checks, contributing float positions, artifact hash, source rows, and point trace | Browser/projector acceptance remains. |
| API errors/health | ✅ implemented | Success, typed errors, warnings, schema-aware readiness | Arabian-Sea artifact readiness returns 200. |
| Frontend/API integration | ✅ implemented | Typed adapter preserves accepted layout and components | Release fixture/browser acceptance remains. |
| Quantitative evaluation | 🟡 tools/fixture | 59 parser queries, five API scenarios, and comparison command | Reviewed anomaly labels/references and evidence approval remain. |
| Deployment/demo | 🟡 | Container recipe and sanitized generated cache | Container/projector/recovery/rehearsal evidence remains. |

## QC Filter: data-quality path

**Purpose:** prevent bad/suspect ARGO observations from masquerading as ocean events.

**Flow:** retrieve matches → apply frozen QC/data-mode/adjusted-value policy → return retained and excluded records/counts, distinct floats, pass rate, reasons, and warning.

**Dependencies:** reviewed ARGO variables, accepted QC flags, data-mode policy, profile identity, provenance, and fixtures.

**Status:** implemented and tested. The adjusted A/D, QC=1 rule and build-spec grade thresholds are auditable; external scientific validation is still separate.

## Anomaly Model: ocean-event path

**Purpose:** classify whether a trustworthy aggregate is unusual relative to the matching production climatology.

**Flow:** QC-passed aggregate → `(x-mean)/std` → normal/mild/strong positive or negative. Skip zero standard deviation or insufficient evidence. Never label this a marine heatwave.

**Status:** implemented behind the QC aggregate boundary with production-baseline safety and zero-standard-deviation handling. Scoring is suppressed whenever evidence is Insufficient.

## Evidence Grade

**Purpose:** state how well the result is supported and why.

**Inputs:** valid profiles, baseline `n`, distinct floats/spatial spread, and QC pass rate. Raw profile count alone is insufficient.

**Presentation:** `Insufficient` suppresses severity; `Indicative` is provisional; `Supported` requires every frozen condition.

**Status:** build-spec thresholds and reasons are implemented centrally. Their source and external-validation caveat are recorded in the manifest.

## Computation-transparency panel

**Purpose:** expose the exact data/provenance behind the result.

**Required values:** selection/source/version, QC rule, raw/valid/excluded counts, distinct floats, pass rate, current aggregate, baseline period/mean/std/`n`, score/label, grade/reasons, parser, and proxy caveats.

**Status:** implemented with actual API counts, selection, QC, aggregate, baseline,
grade decision, parser, source version, and proxy caveats. Browser/projector
acceptance remains outstanding because no local browser runtime was available.

## Quantitative evaluation

**Anomaly comparison:** fixed labels/subset; compare regional-average, unfiltered Z-score, and full QC/evidence pipeline; report confusion counts, precision, recall, F1, false-alert rate, coverage, and response time.

**Reliability:** 59 frozen supported/error queries; provider disabled, malformed output, fallback, invalid rate, average/p95 latency, no/sparse data, malformed date, and simulated provider failure.

**Status:** the 59-query parser suite and five API scenarios generate an
unreviewed report covering disabled parsing, simulated provider failure,
no-data, sparse-data, malformed-date, and latency behavior. The three-method
command is implemented and deliberately exits until reviewed anomaly labels and
references exist. Provider-enabled behavior and all scientific metrics remain
unaccepted.

## Other feature details

- Preprocessing remains offline and must record manifest/hash/QC provenance.
- Production and validation baselines never mix.
- Target success/API/frontend migration follows [API contract](API_CONTRACT.md).
- Typed errors remain `parse_error`, `no_data`, and `general_error`; a data-quality warning is successful-result context, not an internal error.
- Regional average and one optional server-side LLM parser are implemented but
  remain scientifically/provider gated behind the deterministic core.
- Auth, persistence, multilingual, other ocean domains, mobile/WhatsApp, advanced ML, and scaling remain deferred.
