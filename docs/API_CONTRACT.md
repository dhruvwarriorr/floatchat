# API contract

## `POST /chat`

Request:

```json
{
  "query": "Plot SST time series at 19N, 72.8E from 2015-2024 and tell me if it is unusual"
}
```

Successful responses must validate against `ChatResponse` in `backend/app/models.py` and include:

- `summary`
- `query_type`: `profile`, `regional_average`, or `time_series`
- validated `params`
- chart-ready `data`
- conditional `anomaly` with baseline metadata
- `answer_explanation`
- `data_sufficiency` with profile count, coverage, and confidence
- `parser_used`: `llm` or `rule_based`
- `source`

The frontend contract fixture must be frozen from a real, reviewed response before integration. Do not reshape the API around the current illustrative frontend object without reconciling names deliberately.

## Errors

All expected failures return the same body shape:

```json
{
  "error": {
    "type": "parse_error",
    "message": "Safe user-facing explanation",
    "suggestion": "A concrete next step"
  }
}
```

- `422 parse_error`: neither parser can produce a supported query.
- `404 no_data`: the query is valid but no acceptable observation matches.
- `503 general_error`: required dataset/provider is unavailable.
- `500 general_error`: an unexpected failure, without internal detail.

Pydantic request validation may return FastAPI's standard `422` body for structurally invalid requests such as blank or oversized query strings. Before contract freeze, decide whether to normalize those errors into the project error body and record the decision.

## Health

- `GET /health/live`: process is running; independent of data/provider state.
- `GET /health/ready`: manifest and declared query artifacts are present.

Readiness does not prove scientific validity; it only proves that declared runtime files exist.
