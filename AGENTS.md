# FloatChat-Lite Working Agreement

## Mission and source precedence

Build a narrow, explainable hackathon demonstration that answers supported Indian Ocean ARGO questions and shows source, method, data sufficiency, and confidence.

When instructions differ, follow this order:

1. The current user request.
2. This `AGENTS.md`.
3. `docs/HACKATHON_EXECUTION.md` and `docs/ARCHITECTURE.md`.
4. `FloatChat-Lite_Detailed_Project_Roadmap.docx`.
5. `FloatChat-Lite_Project_Documentation.docx`.
6. Current source and tests for implementation details.

Do not commit or push automatically. Preserve unrelated local changes.

## Hard boundaries

- The existing application under `frontend/` is an accepted UI. Do not redesign it, rewrite its copy, change interactions, replace its libraries, or connect it to a new contract unless the user explicitly asks.
- Keep the core stack small: React/TypeScript/Vite, FastAPI/Pydantic, pandas/xarray preprocessing, Parquet, NumPy z-scores, one optional LLM parser, and a deterministic Python fallback.
- Do not add authentication, a database server, chat history, LangChain, vector search, fine-tuning, multiple model providers, microservices, Kubernetes, or new product domains during the core build.
- Never place provider keys in the frontend, tracked files, screenshots, cached JSON, logs, or presentation material.

## Architecture rules

- The browser talks only to `POST /chat`; it never reads NetCDF/Parquet or calls a model/data provider directly.
- FastAPI validates all inputs and responses. Treat query text as untrusted data, never as code or a filesystem path.
- Parsing, data selection, anomaly calculation, explanation, and HTTP mapping stay separate.
- The deterministic rule parser must survive model timeout, malformed output, quota failure, or missing configuration and must disclose `parser_used=rule_based`.
- Scientific preprocessing is offline. Request handling reads versioned, query-ready artifacts and must not rebuild baselines during a demo.
- Production and validation baselines are separate artifacts. Never use validation baselines for live answers or production baselines as validation evidence.
- Low confidence (1-5 profiles) suppresses colored anomaly severity; medium (6-20) is provisional; high (21+) may use full severity.
- Skip z-score output when the baseline standard deviation is zero or evidence is insufficient.

## Evidence and honesty

- The current frontend values are illustrative. Do not relabel them as real, live, validated, operational, or production-ready.
- Do not claim parser accuracy, heatwave validation, model quality, impact, uptime, or rehearsal success until an exact run is recorded in `docs/evidence/evidence-log.csv`.
- Record command/method, dataset or build version, observed result, owner, and date. Negative results are valid evidence; edited or placeholder results are not.
- Every successful real-data response must include source, aggregation, dates, radius/region, profile count, confidence, parser used, and shallow-water proxy caveat where relevant.
- Safe failures are part of the product: `parse_error`, `no_data`, and `general_error` must not expose internal traces.

## Repository ownership

- `frontend/`: accepted interface; frontend owners.
- `backend/app/api/`: HTTP orchestration and typed error mapping only.
- `backend/app/models.py`: shared API vocabulary; change contract-first and update tests/fixtures together.
- `backend/app/services/`: parsing, repository, anomaly, and explanation logic.
- `data/`: local scientific artifacts and a versioned manifest; large raw/processed files are ignored by default.
- `scripts/`: repeatable preprocessing, baseline, validation, and parser-evaluation commands.
- `docs/evidence/`: observed evidence only.
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

Build/lint/test success is not full acceptance. Real-data work also needs manifest/provenance checks and scientific validation; UI integration needs browser/projector checks; provider work needs forced-failure evidence; a release needs live and cached demo rehearsal.

## Definition of done for the hackathon build

- A versioned, licensed/provenanced ARGO subset supports the pinned questions.
- Production and validation baselines are separately versioned.
- Profile and time-series/anomaly work end-to-end; regional average is included only if stable.
- Every success includes explanation and data-sufficiency context.
- Forced parser failure and all typed error paths are friendly and trace-free.
- Parser evaluation and anomaly validation results are stored without altered numbers.
- The presentation setup passes projector checks, cached fallback is sanitized, and rehearsals are logged.
