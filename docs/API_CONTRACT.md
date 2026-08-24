# FloatChat-Lite API contract

> Status: Rev. C runtime contract implemented; scientific/release acceptance remains gated
> Synchronized with `backend/app/` and measured local artifacts on 24 August 2026

## Current reachable API

| Method | Path | Status | Current behaviour |
| --- | --- | --- | --- |
| `GET` | `/health/live` | ✅ | Returns `200 {"status":"ok"}`. |
| `GET` | `/health/ready` | ✅ | Validates manifest status, artifacts, profile schema, and production baseline. The current generated artifact set returns `200`. |
| `POST` | `/chat` | ✅ / 🟡 | Runs parse → retrieval → recurring month/season filter → QC → aggregation → baseline → grade → optional anomaly → provenance. In-coverage development selections return the full contract; uncovered locations return a diagnostic `404 no_data`. Release acceptance is not implied. |

The browser calls only this API through `frontend/src/api/chatApi.ts`; `frontend/src/api/adapter.ts` preserves the accepted component shape. Legacy illustrative responses remain stored but are not used by submission. `ChatResponse` is validated before every success is serialized.

## Request

`ChatRequest` accepts one non-blank string of 1–500 characters:

```json
{"query":"Plot SST time series at 19N, 72.8E from 2015-2024 and tell me if it is unusual"}
```

Structurally invalid requests use FastAPI/Pydantic's standard `422` body. Project-envelope normalization remains a contract decision.

The returned `params.location` is also validated. Every selection carries a complete latitude/longitude display centre so the map never invents a fallback coordinate. A point also carries its radius and `coordinate_precision` (0–4, used only for honest display formatting). A named region carries its canonical backend `bounds`; point locations cannot carry region bounds, and named regions cannot omit them. Explicit radii outside 1–2000 km are rejected rather than silently clamped.

`QueryParams` also preserves compound time meaning. A one-off month uses `month`;
a recurring month across a year range uses `calendar_month`; and named periods use
`season` (`monsoon`, `post-monsoon`, `pre-monsoon`, `summer`, or `winter`).
`calendar_month` and `season` are mutually exclusive. This lets “June of the last
five years” retrieve the full year range first and then retain June observations only.
The words “today”, “current”, “latest”, and “now” resolve to the versioned
artifact's latest represented observation date (currently 2026-08-21), not to a
claim about live ocean conditions.

## Target processing order

```text
validated query
  → parser (LLM optional, deterministic fallback mandatory)
  → retrieve matching raw records
  → apply the parsed recurring calendar-month or season filter
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
| `interpreted_title` | Compact query-specific heading derived from validated parameters; it describes the accepted question rather than reusing the result summary. |
| `summary` | Plain-language restatement of the answer. |
| `query_type` / `params` | Validated query vocabulary and selection. |
| `data` | Chart-ready result; variants must be frozen from reviewed real fixtures. |
| `anomaly` | Optional z-score label plus production baseline mean/std/period/`n`; attempted for every successful parameter result but omitted when evidence/baseline policy disallows scoring. Never call sparse-profile output a marine heatwave. |
| `evidence_grade` | `Insufficient`, `Indicative`, or `Supported`. Replaces `data_sufficiency.confidence`. |
| `evidence_grade_reasons` | Machine-readable or stable textual reasons for the grade. |
| `evidence_panel` | QC rule and exclusion reasons; raw/valid/excluded profile and observation counts; distinct floats and positions; QC pass rate; actual aggregation method, bins, and per-bin counts; current aggregate; selected baseline grid/region, month, mean/std/`n`, and distinct floats; threshold-by-threshold evidence checks; source/version and record provenance. |
| `data_quality_warning` | True when QC leaves too little trustworthy evidence or exposes a material quality limitation. |
| `data_sufficiency` | Raw factual counts/coverage only; no trust label. |
| `answer_explanation` | Source, aggregation, dates, region/radius, proxy caveats, and plain-language interpretation. |
| `parser_used` | `llm` or `rule_based`; fallback must be disclosed. |
| `source` / dataset version | Reviewed artifact identity. |
| `results_by_parameter` | Independent temperature/salinity data, grade, anomaly, QC, and evidence payloads when the query asks for both. |
| `secondary_views` | Best-effort alternate aggregations over the same parameter's QC-passed observations. |
| `supplementary_data` | Best-effort T-S, density, OHC, Hovmöller, seasonal, year-over-year, and anomaly-trend payloads. Joint temperature-salinity products use only observations that pass both parameter QC policies. |

Every chart bin/month includes a bounded `trace` object with contributing profile IDs, float IDs, and source-file row references. The evidence panel also identifies the Parquet artifact and SHA-256.

The map's query anchor represents the requested centre or region centre. It is not an
observation location. `evidence_panel.float_positions` contains up to 50 actual,
contributing ARGO float positions, each with its contributing profile count.

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
    "type": "no_data",
    "message": "Safe user-facing explanation",
    "suggestion": "A concrete next step",
    "understanding": "The query resolved to Mumbai (19.08°N, 72.88°E, 100 km radius).",
    "understood": {
      "location_label": "Mumbai",
      "latitude": 19.076,
      "longitude": 72.8777,
      "radius_km": 100,
      "date_from": "2024-07-01",
      "date_to": "2024-07-31",
      "parameters": ["temperature"],
      "query_type": "profile"
    },
    "searched": "Mumbai (19.08°N, 72.88°E, 100 km radius), from 2024-07-01 through 2024-07-31.",
    "records_found": 0,
    "nearest_available_km": 214.6,
    "suggested_query": "temperature near Mumbai within 500 km from 2024 to 2024"
  }
}
```

The example values above illustrate the response shape; they are not measured dataset
claims. Parse failures use `understanding` to state honestly that no safe structured
selection could be formed. Errors after parsing also return the structured
`understood` selection and `searched` summary.

| Status | Type | Current state |
| --- | --- | --- |
| `422` | `parse_error` | Implemented for unsupported deterministic input. |
| `404` | `no_data` | Implemented for zero spatial/temporal matches. Returns the understood selection, searched area/time, zero count, a safe wider-search diagnostic when one is available, and a ready-to-run alternative query. |
| `503` | `general_error` | Implemented for missing/unreadable data artifacts. |
| `500` | `general_error` | Sanitized unexpected-failure fallback; paths and traces are not returned. |

## Remaining scientific/release gate

1. Install exports covering the frozen Mumbai-50-km and Bay-of-Bengal selections, or approve a documented scope change.
2. Review `data/coverage_report.json`, freeze all grade/spatial thresholds, and record the named reviewer.
3. Create scientifically reviewed anomaly labels/references and run the three-method comparison.
4. Run provider-enabled reliability, browser/projector, recovery, container, and rehearsal acceptance.
5. Log only reviewed quantitative/release claims in `docs/evidence/evidence-log.csv`.
