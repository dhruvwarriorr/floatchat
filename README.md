# FloatChat-Lite

FloatChat-Lite is a stateless React/FastAPI workspace for explainable exploration of local Indian Ocean ARGO temperature and salinity observations. Its mandatory trust order is retrieval → ARGO QC/data-mode filtering → QC-passed aggregation → production-baseline lookup → evidence grade → computation-transparency panel.

## Implemented

- React 19, TypeScript, Vite, Recharts, an interactive Leaflet/CARTO map, Temperature/Salinity/All chart toggles, typed API errors, suggested queries, QC warnings, evidence-grade presentation, parser disclosure, and expandable result provenance.
- FastAPI/Pydantic `POST /chat`, a schema-constrained Gemini-first parser, deterministic parsing for 50+ Indian Ocean aliases and coordinates, failure-safe fallback, CORS, liveness, and data-aware readiness.
- Chunked CSV preprocessing into a 165 MB Parquet artifact with source hashes, retained QC/data-mode fields, stable profile IDs, deduplication, and a versioned manifest.
- Separate production and validation baseline artifacts with runtime protection against validation-baseline use.
- Parquet retrieval, vectorized haversine/region filters, mandatory adjusted A/D QC filtering, independent multi-parameter profile/time-series/regional pipelines, Z-score policy, multi-signal grading, and point-to-source-row traceability.
- 24-prompt parser reliability fixture, three-method evaluation command, and sanitized cache generation from actual API responses.

## Current scientific acceptance

The installed 11 CSV exports contain 14,595,054 data rows before preprocessing and cover 7 November 2001 through 21 August 2026, 5.0–26.168°N, and 45.003–77.987°E. Preprocessing produced 14,413,526 observations, 77,172 profiles, and 531 floats.

The installed source files are an **Arabian Sea subset**, not a complete Indian Ocean archive. They do not include the frozen Mumbai-within-50-km, Chennai, or Bay-of-Bengal selections; those questions return an honest typed `no_data`. Artifact readiness is independent of geographic completeness: the generated manifest is `ready` and `/health/ready` returns `200` when the declared Parquet and production baseline are present.

The evidence thresholds supplied in the build specification are implemented centrally: 5 valid profiles, baseline `n` 10, 2 distinct floats, and a 30% QC pass rate. They make the software behaviour reproducible but remain explicitly marked as not externally scientifically validated. Generated parser/evaluation reports are not pitch evidence until reviewed and copied unchanged into `docs/evidence/evidence-log.csv`.

## Setup and build

Requirements: Node.js 22.13+, Python 3.11+, and `make`.

```bash
make setup
.venv/bin/python scripts/preprocess_argo.py
.venv/bin/python scripts/build_baselines.py
make check
```

For optional LLM parsing, copy `.env.example` to `.env` and set the single server-side `FLOATCHAT_LLM_API_KEY`. Keep `LLM_PROVIDER=gemini` and a Gemini model such as `gemini-2.5-flash`, or select one of the documented compatible providers with the same key variable. The key is loaded only by FastAPI and must never use a `VITE_` prefix. If the provider is missing, times out, reaches quota, or returns invalid output, the response safely discloses `parser_used=rule_based`.

Run the API and web app in separate terminals:

```bash
make dev-api
make dev-web
```

- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health/live`
- Artifact/release readiness: `http://localhost:8000/health/ready`

The Vite development server proxies `/chat` and `/health` to the local API. A production build uses the page's own origin by default, avoiding a browser-side `localhost:8000` dependency; set `VITE_API_URL` only for an intentional split-origin deployment.

Suggested successful local queries:

```text
Show temperature profile at 10N 70E within 150 km in July 2024
Plot SST time series at 10N 70E within 150 km from 2015-2024 and tell me if it is unusual
Show average salinity in the Arabian Sea in 2023
```

The first two use an explicit 150 km radius because the installed exports have no July 2024 profile within the frozen 50/100 km Mumbai selection.

## Evaluation and cache commands

```bash
.venv/bin/python scripts/test_parser_reliability.py
.venv/bin/python scripts/evaluate_methods.py
.venv/bin/python scripts/build_demo_cache.py
```

`evaluate_methods.py` intentionally fails until scientifically reviewed anomaly labels and references are added to `evaluation/fixtures/anomaly_cases.csv`. Cache files distinguish recorded output from a live response; cache generation preserves honest typed `no_data` for uncovered prescribed locations.

## Repository map

```text
frontend/                 Accepted UI plus typed /chat integration
backend/                  FastAPI contract, scientific stages, and tests
data/raw/                 Local source CSV exports; ignored by Git
data/processed/           Query-ready Parquet; ignored by Git
data/baselines/           Separate production/validation artifacts; ignored by Git
evaluation/fixtures/      Frozen parser prompts and anomaly-label schema
evaluation/results/       Generated, unreviewed reports; ignored by Git
demo/cached_responses/    Sanitized recorded API responses; ignored by Git
docs/evidence/            Human-reviewed claim gate
```

Do not commit or push automatically. Do not expose provider keys, call a sparse-profile Z-score a marine heatwave, or describe the provenance panel as SHAP/LIME-style explainable AI.
