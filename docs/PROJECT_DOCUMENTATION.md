# FloatChat-Lite project documentation

> Current-state entry point, synchronized 22 August 2026

## Overview

FloatChat-Lite is a stateless React/FastAPI MVP for natural-language exploration of temperature and salinity in an installed Arabian Sea ARGO subset. It accepts wider Indian Ocean questions but returns typed `no_data` when the local artifacts do not cover the requested selection.

```text
query → Gemini schema parser or deterministic fallback
      → Parquet retrieval → adjusted A/D QC filter
      → per-profile aggregation → production baseline
      → evidence grade → response and point-level provenance
```

## Implemented runtime

| Area | Current implementation |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, Recharts, Leaflet/CARTO, suggested queries, typed failures, multi-parameter toggles, evidence and source traces. |
| API | FastAPI/Pydantic `POST /chat`, CORS, sanitized 404/422/500/503 responses, liveness, and artifact-aware readiness. |
| Parsing | Gemini structured JSON with server-only credentials; 50+ deterministic aliases/regions and coordinate/date grammar on any provider failure. |
| Data | 14,413,526 query-ready observations, 77,172 profiles, 531 floats, versioned manifest, artifact hashes, and column-pruned Parquet scans. |
| Science | Mandatory adjusted A/D QC, profile/time-series/regional aggregation, production-only Z-score, evidence-grade suppression, and shallow-proxy caveat. |
| Traceability | Dataset/source, artifact SHA-256, selection, QC counts/reasons, profile/float IDs, and source-row samples for every displayed chart point. |
| Evaluation | Frozen 24-query parser fixture, API safety scenarios, live-provider cap, three-method comparison command, and reproducible notebook. |

## Data boundary

The 11 local CSV exports cover 7 November 2001 through 21 August 2026, 5.0–26.168°N and 45.003–77.987°E. They are an Arabian Sea subset. Mumbai-within-50-km, Chennai, and Bay-of-Bengal examples are parsed correctly but return `404 no_data`; this is expected, not a system error.

The manifest becomes `ready` when declared query-ready artifacts exist and validate. Geographic completeness is disclosed independently and does not turn a valid Arabian Sea artifact into a readiness failure.

## Scientific boundary

The anomaly service receives only QC-retained observations. `Insufficient` suppresses Z-scores and colored severity. Build-spec evidence thresholds are versioned but explicitly not described as externally validated scientific cut-offs. Sparse ARGO screening is never called a marine heatwave.

See [scientific policy](SCIENTIFIC_POLICY.md), [API contract](API_CONTRACT.md), [features](feature.md), and [evidence rules](evidence/README.md).

## Development

```bash
make setup
.venv/bin/python scripts/preprocess_argo.py
.venv/bin/python scripts/build_baselines.py
make check
make dev-api
make dev-web
```

Configure Gemini in root `.env` using `GEMINI_API_KEY` or `FLOATCHAT_LLM_API_KEY`, `LLM_PROVIDER=gemini`, and a Gemini model. The browser never receives the key.

## Remaining acceptance gates

- Replace the currently rejected local Gemini credential and rerun the provider-enabled fixture within the agreed request cap.
- Supply independently reviewed anomaly labels/references before running or quoting method-comparison metrics.
- Complete browser/projector and container acceptance in an environment where those runtimes are available.
- Review evidence-log rows before allowing any quantitative claim in a pitch.
