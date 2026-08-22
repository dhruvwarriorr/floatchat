from __future__ import annotations

import json
import os
import re
from calendar import monthrange
from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from app.models import (
    GeographicBounds,
    Parameter,
    ParserUsed,
    QueryLocation,
    QueryParams,
    QueryType,
)
from app.services import parser_policy as policy
from app.services.parser_policy import (  # re-exported for stable imports
    GAZETTEER,
    MONTHS,
    QUERY_SCHEMA,
    REGION_BOXES,
    REGION_NAMES,
)

__all__ = [
    "GAZETTEER",
    "MONTHS",
    "QUERY_SCHEMA",
    "REGION_BOXES",
    "REGION_NAMES",
    "UnsupportedQuery",
    "parse_llm",
    "parse_query",
    "parse_rule_based",
]


class UnsupportedQuery(ValueError):
    """Raised when a query cannot be mapped to the supported ocean-data contract.

    Subclasses classify *why* a parse failed so evaluation output can record the
    category. The public API still returns the same safe typed error envelope and
    never exposes provider bodies or credentials.
    """

    category = "unsupported_query"


class ProviderNotConfigured(UnsupportedQuery):
    category = "provider_not_configured"


class ProviderError(UnsupportedQuery):
    """Provider authentication or HTTP failure."""

    category = "provider_error"


class ProviderTimeout(UnsupportedQuery):
    category = "provider_timeout"


class MalformedProviderOutput(UnsupportedQuery):
    category = "malformed_json"


class SchemaViolation(UnsupportedQuery):
    category = "schema_violation"


class SemanticValidationError(UnsupportedQuery):
    category = "semantic_validation"


LAT_LON_PATTERN = re.compile(
    r"(?P<lat>\d{1,2}(?:\.\d+)?)\s*[°º]?\s*(?P<lat_dir>[NS])"
    r"\s*[,;/]?\s*"
    r"(?P<lon>\d{1,3}(?:\.\d+)?)\s*[°º]?\s*(?P<lon_dir>[EW])",
    re.IGNORECASE,
)


def _normalize(raw_query: str) -> str:
    return re.sub(r"\s+", " ", raw_query.lower().replace("–", "-").replace("—", "-")).strip()


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    body = phrase.replace(" ", r"\s+")
    return re.compile(rf"\b{body}\b", re.IGNORECASE)


def _any(query: str, phrases: tuple[str, ...]) -> bool:
    """Token-aware phrase match so 'salt' never matches inside 'basalt'."""

    return any(_phrase_pattern(phrase).search(query) for phrase in phrases)


# --- Parameter, query-type, and anomaly intent -------------------------------


def extract_parameters(query: str) -> list[Parameter]:
    has_salinity = _any(query, policy.SALINITY_PHRASES)
    has_sst = _any(query, policy.SST_PHRASES)
    has_temperature = _any(query, policy.TEMPERATURE_PHRASES) or has_sst
    wants_both = _any(query, policy.BOTH_PARAMETER_PHRASES) or (has_temperature and has_salinity)
    if wants_both:
        temperature_parameter = Parameter.SHALLOW_SST_PROXY if has_sst else Parameter.TEMPERATURE
        return [temperature_parameter, Parameter.SALINITY]
    if has_salinity:
        return [Parameter.SALINITY]
    if has_sst:
        return [Parameter.SHALLOW_SST_PROXY]
    return [Parameter.TEMPERATURE]


def extract_query_type(
    query: str, parameters: list[Parameter], location: QueryLocation
) -> QueryType:
    if _any(query, policy.PROFILE_PHRASES) or policy.DEPTH_PATTERN.search(query):
        return QueryType.PROFILE
    if _any(query, policy.TIME_SERIES_PHRASES):
        return QueryType.TIME_SERIES
    # Comparison/anomaly intent is temporal and outranks whole-region intent,
    # unless the user explicitly asked for a regional average.
    if extract_anomaly_intent(query) and not _any(query, policy.REGIONAL_PHRASES):
        return QueryType.TIME_SERIES
    if _any(query, policy.REGIONAL_PHRASES):
        return QueryType.REGIONAL_AVERAGE
    if location.region_id:
        return QueryType.REGIONAL_AVERAGE
    if any(parameter is Parameter.SHALLOW_SST_PROXY for parameter in parameters):
        return QueryType.TIME_SERIES
    return QueryType.PROFILE


def extract_anomaly_intent(query: str) -> bool:
    return _any(query, policy.ANOMALY_PHRASES)


def extract_radius(query: str) -> float:
    match = policy.RADIUS_PATTERN.search(query)
    if match:
        value = match.group(1) or match.group(2)
        radius = float(value)
        return min(max(radius, policy.MIN_RADIUS_KM), policy.MAX_RADIUS_KM)
    return get_settings().default_radius_km


# --- Dates -------------------------------------------------------------------


def _subtract_months(anchor: date, months: int) -> date:
    total = anchor.year * 12 + (anchor.month - 1) - months
    year, month = divmod(total, 12)
    return date(year, month + 1, 1)


def _season_window(season: str, year: int) -> tuple[str, str]:
    start_month, start_day, end_month, end_day = policy.SEASONS[season]
    return f"{year}-{start_month:02d}-{start_day:02d}", f"{year}-{end_month:02d}-{end_day:02d}"


def _named_month(query: str) -> int | None:
    for name, number in sorted(MONTHS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", query):
            return number
    return None


def _detect_season(query: str) -> str | None:
    if re.search(r"\bpre[-\s]?monsoon\b", query):
        return "pre-monsoon"
    if re.search(r"\bpost[-\s]?monsoon\b", query):
        return "post-monsoon"
    if re.search(r"\bmonsoon\b", query):
        return "monsoon"
    if re.search(r"\bsummer\b", query):
        return "summer"
    return None


def extract_date_range(
    query: str, today: date | None = None
) -> tuple[str, str, int | None, int, int]:
    reference = policy.resolve_today(today)
    # Remove radius/depth spans so numbers like "2000 km" or "200 m" cannot be
    # misread as years.
    date_query = policy.DEPTH_PATTERN.sub(" ", policy.RADIUS_PATTERN.sub(" ", query))

    years = [int(year) for year in re.findall(r"\b(?:19|20|21)\d{2}\b", date_query)]
    if any(
        year < policy.DATASET_MIN_YEAR or year > policy.DATASET_MAX_YEAR for year in years
    ):
        raise UnsupportedQuery(
            f"The local ARGO collection supports dates from {policy.DATASET_MIN_YEAR} "
            f"through {policy.DATASET_MAX_YEAR}."
        )

    def _bounds(
        date_from: str, date_to: str, month: int | None
    ) -> tuple[str, str, int | None, int, int]:
        if date_from > date_to:
            raise UnsupportedQuery("The start date must not be later than the end date.")
        return date_from, date_to, month, int(date_from[:4]), int(date_to[:4])

    # Explicit year range.
    range_match = re.search(r"\b(20\d{2})\s*(?:-|to|through)\s*(20\d{2})\b", date_query)
    if range_match:
        year_start, year_end = map(int, range_match.groups())
        if year_start > year_end:
            raise UnsupportedQuery("The start year must not be later than the end year.")
        return _bounds(f"{year_start}-01-01", f"{year_end}-12-31", None)

    season = _detect_season(date_query)
    single_year_match = re.search(r"\b(20\d{2})\b", date_query)
    month = _named_month(date_query)

    if season is not None:
        year = int(single_year_match.group(1)) if single_year_match else reference.year
        date_from, date_to = _season_window(season, year)
        return _bounds(date_from, date_to, None)

    if single_year_match:
        year = int(single_year_match.group(1))
        if month:
            last_day = monthrange(year, month)[1]
            return _bounds(f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}", month)
        return _bounds(f"{year}-01-01", f"{year}-12-31", None)

    # Relative dates (no explicit year present).
    last_n = re.search(r"\b(?:last|past)\s+(\d{1,2})\s+(year|years|month|months)\b", date_query)
    if last_n:
        count = int(last_n.group(1))
        end = reference
        if last_n.group(2).startswith("year"):
            start = date(end.year - count + 1, 1, 1)
        else:
            start = _subtract_months(end, count - 1)
        return _bounds(start.isoformat(), end.isoformat(), None)

    if re.search(r"\brecently\b", date_query):
        end = reference
        start = _subtract_months(end, 5)
        return _bounds(start.isoformat(), end.isoformat(), None)

    if re.search(r"\bthis\s+year\b", date_query):
        return _bounds(f"{reference.year}-01-01", reference.isoformat(), None)

    if re.search(r"\blast\s+year\b", date_query):
        year = reference.year - 1
        return _bounds(f"{year}-01-01", f"{year}-12-31", None)

    if re.search(r"\b(today|current|latest|now)\b", date_query):
        return _bounds(reference.isoformat(), reference.isoformat(), reference.month)

    # No date at all -> full supported window.
    return _bounds(policy.DATASET_MIN_DATE, policy.DATASET_MAX_DATE, month)


# --- Location ----------------------------------------------------------------


def _validate_envelope(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise UnsupportedQuery("The supplied latitude or longitude is outside its valid range.")
    if not (policy.LAT_MIN <= latitude <= policy.LAT_MAX) or not (
        policy.LON_MIN <= longitude <= policy.LON_MAX
    ):
        raise UnsupportedQuery(
            "The coordinates fall outside the supported Indian Ocean envelope."
        )


def _region_location(region_id: str, label: str, radius_km: float) -> QueryLocation:
    lat_min, lat_max, lon_min, lon_max = REGION_BOXES[region_id]
    return QueryLocation(
        label=label,
        latitude=(lat_min + lat_max) / 2,
        longitude=(lon_min + lon_max) / 2,
        region_id=region_id,
        radius_km=radius_km,
        bounds=GeographicBounds(south=lat_min, west=lon_min, north=lat_max, east=lon_max),
    )


def extract_location(query: str, radius_km: float) -> QueryLocation | None:
    coordinate_match = LAT_LON_PATTERN.search(query)
    if coordinate_match:
        latitude = float(coordinate_match.group("lat"))
        longitude = float(coordinate_match.group("lon"))
        if coordinate_match.group("lat_dir").upper() == "S":
            latitude *= -1
        if coordinate_match.group("lon_dir").upper() == "W":
            longitude *= -1
        _validate_envelope(latitude, longitude)
        return QueryLocation(
            label=(
                f"{abs(latitude):g}°{'N' if latitude >= 0 else 'S'}, "
                f"{abs(longitude):g}°{'E' if longitude >= 0 else 'W'}"
            ),
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

    for name in sorted(REGION_NAMES, key=len, reverse=True):
        if name in query:
            region_id, label = REGION_NAMES[name]
            return _region_location(region_id, label, radius_km)

    for name in sorted(GAZETTEER, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", query):
            latitude, longitude, label = GAZETTEER[name]
            return QueryLocation(
                label=label,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
            )

    return None


# --- Deterministic parser ----------------------------------------------------


def parse_rule_based(raw_query: str) -> QueryParams:
    query = _normalize(raw_query)
    if not query:
        raise UnsupportedQuery("The question was empty.")
    if _any(query, policy.OUT_OF_SCOPE_TERMS):
        raise UnsupportedQuery("The question is outside temperature and salinity exploration.")

    parameters = extract_parameters(query)
    parameter = Parameter.ALL if len(parameters) > 1 else parameters[0]
    radius_km = extract_radius(query)
    location = extract_location(query, radius_km)
    if location is None:
        raise UnsupportedQuery("Include a named Indian Ocean location or latitude/longitude pair.")

    query_type = extract_query_type(query, parameters, location)
    date_from, date_to, month, year_start, year_end = extract_date_range(query)
    anomaly_requested = extract_anomaly_intent(query)
    return QueryParams(
        query_type=query_type,
        parameter=parameter,
        parameters=parameters,
        location=location,
        year_start=year_start,
        year_end=year_end,
        month=month,
        anomaly_requested=anomaly_requested,
        date_from=date_from,
        date_to=date_to,
        include_anomaly=anomaly_requested,
        parser_used=ParserUsed.RULE_BASED,
    )


# --- Optional LLM planner ----------------------------------------------------


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _semantic_parameters(raw_parameters: Any) -> list[Parameter]:
    if not isinstance(raw_parameters, list) or not raw_parameters:
        raise SchemaViolation("The provider omitted the parameters array.")
    try:
        parsed = [Parameter(str(value).lower()) for value in raw_parameters]
    except ValueError as exc:
        raise SchemaViolation("The provider returned an unsupported parameter.") from exc
    unique = list(dict.fromkeys(parsed))
    if len(unique) != len(parsed):
        raise SemanticValidationError("The provider repeated a parameter.")
    if Parameter.ALL in unique:
        raise SchemaViolation("The provider returned the internal 'all' parameter.")
    if {Parameter.TEMPERATURE, Parameter.SHALLOW_SST_PROXY} <= set(unique):
        raise SemanticValidationError(
            "temperature and the SST proxy cannot be combined as two temperature requests."
        )
    if len(unique) > 2:
        raise SchemaViolation("The provider returned more than two parameters.")
    return unique


def _semantic_dates(payload: dict[str, Any]) -> tuple[str, str]:
    date_from = str(payload.get("date_from") or "")
    date_to = str(payload.get("date_to") or "")
    try:
        parsed_from = date.fromisoformat(date_from)
        parsed_to = date.fromisoformat(date_to)
    except ValueError as exc:
        raise SchemaViolation("The provider returned an invalid ISO date.") from exc
    if parsed_from > parsed_to:
        raise SemanticValidationError("date_from is later than date_to.")
    low = date(policy.DATASET_MIN_YEAR, 1, 1)
    high = date(policy.DATASET_MAX_YEAR, 12, 31)
    if parsed_from < low or parsed_to > high:
        raise SemanticValidationError("The provider dates fall outside the dataset window.")
    return date_from, date_to


def _build_params(payload: dict[str, Any], parser_used: ParserUsed) -> QueryParams:
    if not isinstance(payload, dict):
        raise SchemaViolation("The provider output is not a JSON object.")
    if str(payload.get("query_type", "")).lower() in {"unsupported", "out_of_scope"}:
        raise UnsupportedQuery("The provider marked this query as out of scope.")
    try:
        query_type = QueryType(str(payload["query_type"]).lower())
    except (KeyError, ValueError) as exc:
        raise SchemaViolation("The provider returned an unsupported query type.") from exc

    parameters = _semantic_parameters(payload.get("parameters"))
    parameter = Parameter.ALL if len(parameters) > 1 else parameters[0]

    radius_value = payload.get("radius_km", policy.DEFAULT_RADIUS_KM)
    try:
        radius_km = float(radius_value)
    except (TypeError, ValueError) as exc:
        raise SchemaViolation("The provider returned a non-numeric radius.") from exc
    if not (policy.MIN_RADIUS_KM <= radius_km <= policy.MAX_RADIUS_KM):
        raise SemanticValidationError("The provider radius is outside the allowed range.")

    region_id = payload.get("region_id") or None
    has_coordinates = payload.get("lat") is not None and payload.get("lon") is not None
    if region_id and has_coordinates:
        raise SemanticValidationError("The provider returned both a region and coordinates.")

    if region_id:
        if region_id not in REGION_BOXES:
            raise SchemaViolation("The provider returned an unsupported named region.")
        location = _region_location(
            region_id,
            str(payload.get("location_label") or region_id.replace("-", " ").title()),
            radius_km,
        )
    else:
        if not has_coordinates:
            raise SemanticValidationError("The provider returned no usable location.")
        try:
            latitude = float(payload["lat"])
            longitude = float(payload["lon"])
        except (TypeError, ValueError) as exc:
            raise SchemaViolation("The provider returned non-numeric coordinates.") from exc
        _validate_envelope(latitude, longitude)
        location = QueryLocation(
            label=str(payload.get("location_label") or "Requested coordinates"),
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

    date_from, date_to = _semantic_dates(payload)
    year_start = int(date_from[:4])
    year_end = int(date_to[:4])
    month = int(date_from[5:7]) if date_from[:7] == date_to[:7] else None
    include_anomaly = bool(payload.get("include_anomaly", False))
    return QueryParams(
        query_type=query_type,
        parameter=parameter,
        parameters=parameters,
        location=location,
        year_start=year_start,
        year_end=year_end,
        month=month,
        anomaly_requested=include_anomaly,
        date_from=date_from,
        date_to=date_to,
        include_anomaly=include_anomaly,
        parser_used=parser_used,
    )


def _planner_prompt() -> str:
    return f"{policy.build_system_prompt()}\n\nExamples:\n{policy.few_shot_text()}"


def _configured_key() -> tuple[str, str] | None:
    if key := os.getenv("GEMINI_API_KEY"):
        return "gemini", key
    if key := os.getenv("FLOATCHAT_LLM_API_KEY"):
        return os.getenv("LLM_PROVIDER", "gemini").lower(), key
    if key := os.getenv("OPENAI_API_KEY"):
        return "openai", key
    if key := os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic", key
    return None


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    outputs = payload.get("outputs") or payload.get("output")
    if isinstance(outputs, list):
        for item in outputs:
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("output_text")
            if isinstance(text, str) and text.strip():
                return text
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        return str(part["text"])
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if not isinstance(content, dict) or not isinstance(content.get("parts"), list):
                continue
            for part in content["parts"]:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    return str(part["text"])
    raise MalformedProviderOutput("Gemini response did not contain output_text")


def parse_llm(raw_query: str, timeout: float | None = None) -> QueryParams:
    configuration = _configured_key()
    if configuration is None:
        raise ProviderNotConfigured("No server-side LLM parser is configured.")

    provider, api_key = configuration
    timeout = timeout if timeout is not None else get_settings().llm_timeout
    system_prompt = _planner_prompt()
    try:
        if provider == "gemini":
            base_url = os.getenv(
                "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
            ).rstrip("/")
            model = os.getenv("FLOATCHAT_LLM_MODEL") or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
            if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
                raise SchemaViolation("Gemini model name contains unsafe characters")
            style = os.getenv("GEMINI_API_STYLE", "generate_content").lower()
            if style == "interactions":
                url = f"{base_url}/interactions"
                request_json = {
                    "model": model,
                    "system_instruction": system_prompt,
                    "input": raw_query,
                    "response_format": {
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": QUERY_SCHEMA,
                    },
                }
            else:
                url = f"{base_url}/models/{model}:generateContent"
                request_json = {
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": raw_query}]}],
                    "generationConfig": {
                        "temperature": 0,
                        "responseMimeType": "application/json",
                        "responseJsonSchema": QUERY_SCHEMA,
                    },
                }
            response = httpx.post(
                url,
                headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                json=request_json,
                timeout=timeout,
            )
            response.raise_for_status()
            content = _extract_gemini_text(response.json())
        elif provider == "anthropic":
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                    "x-api-key": api_key,
                },
                json={
                    "model": os.getenv("FLOATCHAT_LLM_MODEL")
                    or os.getenv("LLM_MODEL")
                    or "claude-3-5-haiku-latest",
                    "max_tokens": 500,
                    "temperature": 0,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": raw_query}],
                },
                timeout=timeout,
            )
            response.raise_for_status()
            content = response.json()["content"][0]["text"]
        elif provider == "openai":
            base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            model = os.getenv("FLOATCHAT_LLM_MODEL") or os.getenv("LLM_MODEL") or "gpt-4o-mini"
            style = os.getenv("LLM_API_STYLE") or (
                "responses" if base_url == "https://api.openai.com/v1" else "chat_completions"
            )
            if style.startswith("chat_completions"):
                response_format: dict[str, Any]
                if style == "chat_completions_json_object":
                    response_format = {"type": "json_object"}
                else:
                    response_format = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "floatchat_query",
                            "strict": True,
                            "schema": QUERY_SCHEMA,
                        },
                    }
                url = f"{base_url}/chat/completions"
                request_json = {
                    "model": model,
                    "temperature": 0,
                    "response_format": response_format,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": raw_query},
                    ],
                }
            else:
                url = f"{base_url}/responses"
                request_json = {
                    "model": model,
                    "instructions": system_prompt,
                    "input": raw_query,
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "floatchat_query",
                            "strict": True,
                            "schema": QUERY_SCHEMA,
                        }
                    },
                }
            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=request_json,
                timeout=timeout,
            )
            response.raise_for_status()
            response_payload = response.json()
            content = (
                response_payload["choices"][0]["message"]["content"]
                if style.startswith("chat_completions")
                else response_payload["output_text"]
            )
        else:
            raise SchemaViolation("Unsupported LLM provider")
        payload = json.loads(_strip_json_fence(content))
        return _build_params(payload, ParserUsed.LLM)
    except UnsupportedQuery:
        raise  # already classified (provider/schema/semantic/unsupported)
    except httpx.TimeoutException as exc:
        raise ProviderTimeout("The optional parser timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise ProviderError("The optional parser returned an HTTP error.") from exc
    except httpx.HTTPError as exc:
        raise ProviderError("The optional parser could not be reached.") from exc
    except json.JSONDecodeError as exc:
        raise MalformedProviderOutput("The optional parser did not return valid JSON.") from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise MalformedProviderOutput(
            "The optional parser did not return valid structured output."
        ) from exc


def parse_query(raw_query: str) -> QueryParams:
    if _configured_key() is not None:
        try:
            return parse_llm(raw_query)
        except UnsupportedQuery:
            pass
        except Exception:
            pass
    return parse_rule_based(raw_query)
