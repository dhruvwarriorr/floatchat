# FloatChat-Lite Working Agreement

## Mission and source precedence

Build a narrow, explainable hackathon demonstration that answers supported Indian Ocean ARGO questions and distinguishes measurement quality from genuine oceanographic anomalies. Every result must expose source, method, QC treatment, data sufficiency, evidence grade, and computation provenance.

When instructions differ, follow this order:

1. The current user request.
2. This `AGENTS.md`.
3. `docs/prd.md` and `docs/ARCHITECTURE.md` for target requirements and architecture.
4. Current source, configuration, tests, data manifests, and evidence artifacts for implementation status.
5. `docs/HACKATHON_EXECUTION.md`, the synchronized roadmap, and other Markdown guidance.
6. Root DOCX files as retained reference artifacts only.

Do not commit or push automatically. Preserve unrelated local changes. Never present a target architecture or structural placeholder as implemented behaviour.

## Hard boundaries

- The existing application under `frontend/` is an accepted illustrative UI. Do not redesign it, rewrite its copy, change interactions, replace Recharts/static map assets, or connect it to a new contract unless the current user explicitly requests implementation work beyond structural synchronization.
- Keep the core stack small: React/TypeScript/Vite, FastAPI/Pydantic, pandas/xarray preprocessing, Parquet, NumPy z-scores, one optional LLM parser, and a deterministic Python parser.
- Do not add authentication, a database server, chat history, LangChain, vector search, fine-tuning, multiple model providers, microservices, Kubernetes, or new product domains during the core build.
- Never place provider keys in the frontend, tracked files, screenshots, cached JSON, logs, notebooks, results, or presentation material.
- Do not call a sparse ARGO profile Z-score result a “marine heatwave.” Use “upper-ocean temperature anomaly” or “salinity anomaly” unless a separate formal marine-heatwave method is implemented and validated.
- Describe the evidence panel as computation transparency and provenance reporting, not SHAP/LIME-style explainable AI.

## Architecture rules

- The browser talks only to `POST /chat`; it never reads NetCDF/Parquet or calls a model/data provider directly.
- FastAPI validates all inputs and responses. Treat query text as untrusted data, never as code or a filesystem path.
- Parsing, data selection, QC filtering, anomaly calculation, evidence grading, provenance composition, and HTTP mapping stay separate.
- The mandatory runtime order for anomaly requests is: retrieve matching records → apply ARGO QC/data-mode policy → aggregate QC-passed observations → score against the production baseline → compute evidence grade → compose the evidence panel.
- The anomaly service must never see raw or QC-rejected observations. Excluded counts and the applied QC rule remain auditable.
- Prefer adjusted/delayed-mode values for historical analysis only after the exact ARGO field precedence and acceptable QC flags are frozen against a reviewed dataset.
- The deterministic parser must survive model-disabled, timeout, malformed output, quota failure, and missing-configuration cases and must disclose `parser_used=rule_based`.
- Scientific preprocessing is offline. Request handling reads versioned, query-ready artifacts and must not rebuild baselines during a demo.
- Production and validation baselines are separate artifacts. Never use validation baselines for live answers or production baselines as independent validation evidence.
- `evidence_grade` replaces profile-count-only confidence in the target contract:
  - `Insufficient`: fewer than five valid current profiles or insufficient baseline observations.
  - `Indicative`: scoring is possible but spatial/float coverage is limited.
  - `Supported`: valid-profile count, baseline `n`, distinct-float coverage, and QC pass rate all satisfy frozen thresholds.
- Do not invent unresolved thresholds for baseline `n`, distinct-float count, coverage, or QC pass rate. Store them in one documented policy when the dataset is reviewed.
- Suppress colored anomaly severity for `Insufficient`; qualify `Indicative` as provisional; use full weight only for `Supported`.
- Skip z-score output when baseline standard deviation is zero or evidence is insufficient.

## Evidence and honesty

- Current frontend values and profile-count confidence are illustrative/legacy. Do not relabel them as real, live, validated, operational, production-ready, or compliant with the Rev. B evidence-grade contract.
- Do not claim parser reliability, anomaly accuracy/precision/recall/F1, false-alert rate, query coverage, response latency, heatwave validation, model quality, impact, uptime, or rehearsal success until an exact run is recorded in `docs/evidence/evidence-log.csv`.
- Quantitative anomaly evaluation must compare: (a) regional-average baseline, (b) unfiltered Z-score, and (c) the full QC-filtered/evidence-graded pipeline on the same frozen labels and subset.
- Parser/API reliability must cover 20–30 frozen paraphrases, invalid-output rate, LLM explicitly disabled, deterministic fallback, average/p95 latency, no-data, sparse-data, malformed-date, and simulated-provider-failure conditions.
- Record command/method, dataset/build version, labeling method, denominators, observed result, owner, date, and evidence path. Negative results are valid; edited or placeholder results are not.
- Every successful real-data response must include source/version, aggregation, dates, radius/region, raw and valid counts, distinct-float count, QC rule/pass rate, evidence grade and reasons, parser used, baseline mean/std/n, score, and shallow-water proxy caveat where relevant.
- Safe failures are part of the product: `parse_error`, `no_data`, and `general_error` must not expose internal traces.

## Repository ownership

- `frontend/`: accepted illustrative interface; target contract migration requires reviewed fixtures and explicit authorization.
- `backend/app/api/`: HTTP orchestration and typed error mapping only.
- `backend/app/models.py`: shared API vocabulary; target `EvidenceGrade`/panel fields are structurally defined while legacy `Confidence` remains internal to the old anomaly scaffold. Complete migration contract-first and update tests/fixtures together.
- `backend/app/services/parser.py`: deterministic grammar and optional provider handoff only.
- `backend/app/services/data.py`: artifact readiness, retrieval, and supported filters/aggregations; no anomaly judgment.
- `backend/app/services/qc.py`: mandatory ARGO QC/data-mode filter boundary before anomaly scoring.
- `backend/app/services/anomaly.py`: Z-score policy over QC-passed aggregates only; never data-quality filtering.
- `backend/app/services/evidence.py`: multi-signal evidence-grade policy and reasons.
- `backend/app/services/explain.py`: evidence-panel/provenance composition from actual computed values.
- `data/`: local scientific artifacts and a versioned manifest; large raw/processed files are ignored by default.
- `scripts/`: repeatable preprocessing, baseline, scientific evaluation, method-comparison, and parser-reliability commands.
- `evaluation/`: frozen small fixtures, reproducible notebooks, and generated reports; generated metrics are not evidence until reviewed/logged.
- `docs/evidence/`: observed evidence and claim gate only.
- `demo/`: sanitized cached fallback and presentation captures only.

## Commands and acceptance

```bash
make setup
make dev-web
make dev-api
make check
make container
```

For focused work, run the narrow check first:

```bash
npm --prefix frontend run lint
npm --prefix frontend test
.venv/bin/ruff check backend scripts
.venv/bin/pytest backend/tests
```

Build/lint/test success is not full acceptance. Real-data work also needs manifest/provenance/QC checks and quantitative scientific validation; UI integration needs browser/projector checks; provider work needs model-disabled and forced-failure evidence; a release needs live and cached demo rehearsal.

## Definition of done for the hackathon build

- A versioned, licensed/provenanced ARGO subset supports the pinned questions and retains auditable QC/data-mode fields.
- Production and validation baselines are separately versioned.
- QC filtering demonstrably precedes anomaly scoring; rejected records cannot reach the anomaly service.
- Profile and time-series/anomaly work end-to-end; regional average is included only if stable.
- Every success includes the computation-transparency panel, raw/valid counts, distinct-float coverage, baseline `n`, evidence grade with reasons, and proxy caveats.
- Forced model-disabled/provider failure and all typed error paths are friendly and trace-free.
- The three-method anomaly comparison and parser/API reliability evaluation store exact, reproducible outputs without altered numbers.
- The presentation setup passes projector checks, cached fallback is sanitized, and rehearsals are logged.
