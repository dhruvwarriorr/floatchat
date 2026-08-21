# FloatChat-Lite feature status

> Synchronized to Rev. B and current source on 21 August 2026

## Status summary

| Feature | Status | Current state | Remaining work |
| --- | --- | --- | --- |
| Illustrative UI | ✅ illustrative | Four local Recharts/static-map flows with legacy confidence | Preserve; migrate only after reviewed target fixtures and frontend-library decision. |
| Data preprocessing/manifest | 🔴 | Structure/schema only | Retain auditable QC/data-mode fields; build reviewed artifacts. |
| Deterministic parser | ✅ narrow | Four phrase families | Expand only to frozen data coverage; reliability evaluation missing. |
| Optional LLM parser | 🟠 | Environment placeholders/enum | One validated adapter, model-disabled fallback, failure/latency evidence. |
| Scientific retrieval | 🔴 | Readiness/refusal boundary | Parquet schema/filter/aggregation and `no_data`. |
| QC Filter | 🟠 structure | `services/qc.py` boundary only | Freeze rules; implement audit output and tests before anomaly. |
| Anomaly Model | 🟡 legacy | Isolated Z-score/profile-count policy | Accept QC-passed aggregate only; baseline `n`; remove trust judgment. |
| Evidence Grade | 🟠 structure | `services/evidence.py` boundary only | Target models, centralized thresholds/reasons, tests. |
| Evidence panel | 🟠 structure | `services/explain.py`; illustrative preparation UI | Compose actual QC/count/baseline/score/provenance values; expandable UI. |
| API errors/health | 🟡 | Live/ready, parse/general | Success, no-data, QC-warning, integrity readiness. |
| Frontend/API integration | 🔴 | No client; contracts diverge | Freeze target real fixtures and preserve accepted behaviour. |
| Quantitative evaluation | 🟠 structure | Empty `evaluation/` workspace | Labels, notebooks, three-method metrics, parser/API reliability. |
| Deployment/demo | 🟡 / 🟠 | Recipe/placeholders | Verified run, cache, projector/recovery/rehearsal evidence. |

## QC Filter: data-quality path

**Purpose:** prevent bad/suspect ARGO observations from masquerading as ocean events.

**Flow:** retrieve matches → apply frozen QC/data-mode/adjusted-value policy → return retained and excluded records/counts, distinct floats, pass rate, reasons, and warning.

**Dependencies:** reviewed ARGO variables, accepted QC flags, data-mode policy, profile identity, provenance, and fixtures.

**Status:** structure only. No rule is implemented. Thresholds/flags must not be guessed.

## Anomaly Model: ocean-event path

**Purpose:** classify whether a trustworthy aggregate is unusual relative to the matching production climatology.

**Flow:** QC-passed aggregate → `(x-mean)/std` → normal/mild/strong positive or negative. Skip zero standard deviation or insufficient evidence. Never label this a marine heatwave.

**Status:** legacy isolated function exists but currently combines profile-count confidence with anomaly presentation and is not QC-gated.

## Evidence Grade

**Purpose:** state how well the result is supported and why.

**Inputs:** valid profiles, baseline `n`, distinct floats/spatial spread, and QC pass rate. Raw profile count alone is insufficient.

**Presentation:** `Insufficient` suppresses severity; `Indicative` is provisional; `Supported` requires every frozen condition.

**Status:** structure only; only the fewer-than-five insufficient rule is quantitatively frozen.

## Computation-transparency panel

**Purpose:** expose the exact data/provenance behind the result.

**Required values:** selection/source/version, QC rule, raw/valid/excluded counts, distinct floats, pass rate, current aggregate, baseline period/mean/std/`n`, score/label, grade/reasons, parser, and proxy caveats.

**Status:** frontend has illustrative preparation text, not a real evidence panel.

## Quantitative evaluation

**Anomaly comparison:** fixed labels/subset; compare regional-average, unfiltered Z-score, and full QC/evidence pipeline; report confusion counts, precision, recall, F1, false-alert rate, coverage, and response time.

**Reliability:** 20–30 paraphrases; model disabled, malformed output, fallback, invalid rate, average/p95 latency, no/sparse data, malformed date, simulated provider failure.

**Status:** directory structure only; no metrics exist.

## Other feature details

- Preprocessing remains offline and must record manifest/hash/QC provenance.
- Production and validation baselines never mix.
- Target success/API/frontend migration follows [API contract](API_CONTRACT.md).
- Typed errors remain `parse_error`, `no_data`, and `general_error`; a data-quality warning is successful-result context, not an internal error.
- Regional average and optional LLM remain lower priority than the QC-gated deterministic core.
- Auth, persistence, multilingual, other ocean domains, mobile/WhatsApp, advanced ML, and scaling remain deferred.
