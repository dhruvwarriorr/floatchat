# FloatChat-Lite API contract

> Status: Rev. B runtime contract implemented; scientific/release acceptance remains gated
> Synchronized with `backend/app/` and measured local artifacts on 22 August 2026

## Current reachable API

| Method | Path | Status | Current behaviour |
| --- | --- | --- | --- |
| `GET` | `/health/live` | ✅ | Returns `200 {"status":"ok"}`. |
| `GET` | `/health/ready` | ✅ | Validates manifest status, artifacts, profile schema, and production baseline. The current generated artifact set returns `200`. |
| `POST` | `/chat` | ✅ / 🟡 | Runs parse → retrieval → QC → aggregation → baseline → grade → optional anomaly → provenance. In-coverage development selections return the full contract; uncovered locations return `404 no_data`. Release acceptance is not implied. |

The browser calls only this API through `frontend/src/api/chatApi.ts`; `frontend/src/api/adapter.ts` preserves the accepted component shape. Legacy illustrative responses remain stored but are not used by submission. `ChatResponse` is validated before every success is serialized.

## Request

`ChatRequest` accepts one non-blank string of 1–500 characters:

```json
{"query":"Plot SST time series at 19N, 72.8E from 2015-2024 and tell me if it is unusual"}
```

Structurally invalid requests use FastAPI/Pydantic's standard `422` body. Project-envelope normalization remains a contract decision.

## Target processing order

```text
validated query
  → parser (LLM optional, deterministic fallback mandatory)
  → retrieve matching raw records
  → mandatory QC/data-mode filter
  → aggregate QC-passed observations
  → production-baseline anomaly score
  → multi-signal evidence grade
  → computation-transparency/provenance panel
  → validated ChatResponse
```

The anomaly service must never receive QC-rejected records.

## Target success fields

| Field | Purpose |
| --- | --- |
| `summary` | Plain-language restatement of the answer. |
| `query_type` / `params` | Validated query vocabulary and selection. |
| `data` | Chart-ready result; variants must be frozen from reviewed real fixtures. |
| `anomaly` | Optional z-score label plus production baseline mean/std/period/`n`; never call sparse-profile output a marine heatwave. |
| `evidence_grade` | `Insufficient`, `Indicative`, or `Supported`. Replaces `data_sufficiency.confidence`. |
| `evidence_grade_reasons` | Machine-readable or stable textual reasons for the grade. |
| `evidence_panel` | QC rule, raw/valid/excluded counts, distinct floats, QC pass rate, current aggregate, baseline mean/std/`n`, score, source/version, and selection provenance. |
| `data_quality_warning` | True when QC leaves too little trustworthy evidence or exposes a material quality limitation. |
| `data_sufficiency` | Raw factual counts/coverage only; no trust label. |
| `answer_explanation` | Source, aggregation, dates, region/radius, proxy caveats, and plain-language interpretation. |
| `parser_used` | `llm` or `rule_based`; fallback must be disclosed. |
| `source` / dataset version | Reviewed artifact identity. |
| `results_by_parameter` | Independent temperature/salinity data, grade, anomaly, QC, and evidence payloads when the query asks for both. |

Every chart bin/month includes a bounded `trace` object with contributing profile IDs, float IDs, and source-file row references. The evidence panel also identifies the Parquet artifact and SHA-256.

No numeric example in architecture or documentation is a measured response fixture.

## Evidence-grade policy

- `Insufficient`: fewer than five valid current profiles or baseline sample size below the frozen minimum.
- `Indicative`: scoring is possible, but distinct-float/spatial coverage is limited.
- `Supported`: valid count, baseline `n`, distinct-float coverage, and QC pass rate all meet frozen thresholds.

The values supplied by the build specification are active: 5 valid profiles, baseline `n` 10, 2 distinct floats, and QC pass rate 0.30. The manifest records that these are implementation thresholds, not externally validated scientific cut-offs. `Insufficient` still suppresses the Z-score.

## Errors

```json
{
  "error": {
    "type": "parse_error",
    "message": "Safe user-facing explanation",
    "suggestion": "A concrete next step"
  }
}
```

| Status | Type | Current state |
| --- | --- | --- |
| `422` | `parse_error` | Implemented for unsupported deterministic input. |
| `404` | `no_data` | Implemented for zero spatial/temporal matches; verified for Bay of Bengal with the installed exports. |
| `503` | `general_error` | Implemented for missing/unreadable data artifacts. |
| `500` | `general_error` | Sanitized unexpected-failure fallback; paths and traces are not returned. |

## Remaining scientific/release gate

1. Install exports covering the frozen Mumbai-50-km and Bay-of-Bengal selections, or approve a documented scope change.
2. Review `data/coverage_report.json`, freeze all grade/spatial thresholds, and record the named reviewer.
3. Create scientifically reviewed anomaly labels/references and run the three-method comparison.
4. Run provider-enabled reliability, browser/projector, recovery, container, and rehearsal acceptance.
5. Log only reviewed quantitative/release claims in `docs/evidence/evidence-log.csv`.
