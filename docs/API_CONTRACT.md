# FloatChat-Lite API contract

> Status: target Rev. B contract planned; legacy backend boundary partially implemented
> Synchronized with `docs/ARCHITECTURE.md`, `docs/prd.md`, and `backend/app/` on 21 August 2026

## Current reachable API

| Method | Path | Status | Current behaviour |
| --- | --- | --- | --- |
| `GET` | `/health/live` | ✅ | Returns `200 {"status":"ok"}`. |
| `GET` | `/health/ready` | 🟡 | Checks ready manifest status and declared file existence only; currently `503` because `data/manifest.json` is absent. |
| `POST` | `/chat` | 🟡 | Validates input and runs the narrow deterministic parser, then returns `503 general_error`; no scientific success path exists. |

The browser does not call this API. `ChatResponse` now structurally defines Rev. B evidence-grade, panel, warning, baseline-`n`, and factual sufficiency fields, but no runtime path constructs it. Legacy profile-count `Confidence` remains internal to the current anomaly scaffold.

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

No numeric example in architecture or documentation is a measured response fixture.

## Evidence-grade policy

- `Insufficient`: fewer than five valid current profiles or baseline sample size below the frozen minimum.
- `Indicative`: scoring is possible, but distinct-float/spatial coverage is limited.
- `Supported`: valid count, baseline `n`, distinct-float coverage, and QC pass rate all meet frozen thresholds.

Only the fewer-than-five rule is currently specified quantitatively. Other thresholds must be frozen from the reviewed dataset and stored in one policy; do not invent them in API code or UI copy.

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
| `404` | `no_data` | Modelled, but unreachable. Distinct from “records found but rejected/too thin after QC.” |
| `503` | `general_error` | Implemented for absent/unimplemented scientific data path. |
| `500` | `general_error` | Safe fallback exists but is not meaningfully exercised after successful repository work. |

## Contract migration gate

1. Freeze ARGO QC flags, adjusted/raw precedence, `data_mode`, grade thresholds, and warning semantics.
2. Review/freeze the structural target models without treating legacy frontend confidence as evidence grade.
3. Implement and test QC → anomaly → grade → evidence-panel order.
4. Freeze one reviewed real fixture per supported data variant.
5. Reconcile `OceanResponse` and target `ChatResponse` contract-first.
6. Add success, no-data, QC-warning, each grade, zero-std, validation, and trace-safety tests.
7. Log quantitative/reliability acceptance in `evidence/evidence-log.csv`.
