# FloatChat-Lite API contract

> Status: 🟡 Partially implemented
> Verified against `backend/app/` on 21 August 2026

This document describes the contract that exists today and labels fields or behaviours that are not reachable yet. The browser is not connected to this API; see [Architecture](ARCHITECTURE.md) and [Features](feature.md).

## Status legend

- ✅ Implemented in source
- 🟡 Implemented boundary, incomplete runtime path
- 🟠 Planned
- ⚪ Needs verification

## Endpoints

| Method | Path | Status | Current behaviour |
| --- | --- | --- | --- |
| `GET` | `/health/live` | ✅ | Returns `200 {"status":"ok"}` when the process is running. |
| `GET` | `/health/ready` | 🟡 | Returns `200` only when a ready manifest and every declared file exist; currently returns `503` because `data/manifest.json` is absent. It does not validate hashes, schema, provenance, or scientific correctness. |
| `POST` | `/chat` | 🟡 | Validates input and runs the deterministic parser. Supported input currently reaches `503 general_error` because scientific repository queries are not implemented. No success response is reachable. |

There is no authentication. Queries are stateless and are not persisted.

## `POST /chat`

### Request

`ChatRequest` in `backend/app/models.py` accepts one non-blank string of 1–500 characters:

```json
{
  "query": "Plot SST time series at 19N, 72.8E from 2015-2024 and tell me if it is unusual"
}
```

Structurally invalid JSON, a missing field, blank text, or text over 500 characters uses FastAPI/Pydantic's standard `422` validation response. Normalising that response into the project error envelope is 🟠 planned.

### Deterministic parsing

The current parser supports four narrow patterns:

| Pattern | Parsed query type | Parameter |
| --- | --- | --- |
| Mumbai + temperature | `profile` | `temperature` |
| `19N`, `72.8E`, or SST wording | `time_series` | `shallow_sst_proxy` |
| Bay of Bengal + salinity | `regional_average` | `salinity` |
| Arabian Sea + warming | `time_series` | `temperature` |

It extracts years and full English month names. It is not a general coordinate parser or city gazetteer. Every current parse is tagged `rule_based`; no LLM adapter exists.

### Success model: defined but not reachable

`ChatResponse` is defined and validated by Pydantic:

| Field | Type / values | Notes |
| --- | --- | --- |
| `summary` | string | Plain-language result summary. |
| `query_type` | `profile`, `regional_average`, `time_series` | Duplicates `params.query_type` by current model design. |
| `params` | `QueryParams` | Validated location, parameter, year range, month, anomaly intent, and parser. |
| `data` | array of objects | Shape is intentionally not frozen yet. |
| `anomaly` | object or null | Z-score, label, baseline values/period, and provisional flag. |
| `answer_explanation` | string | Must state method, source, selection, and proxy caveats. |
| `data_sufficiency` | object | `profile_count`, textual `coverage`, and `low`/`medium`/`high`. |
| `parser_used` | `llm` or `rule_based` | `llm` is modelled but not implemented. |
| `source` | string | Must identify the reviewed dataset/version when real responses exist. |

The frontend currently consumes `OceanResponse` from `frontend/src/types/ocean.ts`, not `ChatResponse`. Those shapes differ and must be reconciled contract-first before integration. Do not reshape the API around illustrative values without a reviewed real response fixture.

### Project error envelope

```json
{
  "error": {
    "type": "parse_error",
    "message": "Safe user-facing explanation",
    "suggestion": "A concrete next step"
  }
}
```

| HTTP status | Error type | Status | Trigger |
| --- | --- | --- | --- |
| `422` | `parse_error` | ✅ | Deterministic parser cannot map the text to a supported query. |
| `404` | `no_data` | 🟠 | Defined in the enum and intended for a valid query with no acceptable observations; no current code path emits it. |
| `503` | `general_error` | ✅ | Data manifest/artifacts are absent or the repository query is unimplemented. |
| `500` | `general_error` | 🟡 | Safe fallback exists after repository execution, but the repository currently always raises first. |

Internal traces and filesystem paths must never be returned.

## Contract freeze gate

Before connecting the frontend:

1. Implement one reviewed real profile query against a versioned dataset.
2. Freeze a real `ChatResponse` fixture and the chart-data variants.
3. Reconcile frontend and backend field names/enums together.
4. Add success, `no_data`, validation, and trace-safety contract tests.
5. Record the dataset/build and observed integration result in `evidence/evidence-log.csv`.
