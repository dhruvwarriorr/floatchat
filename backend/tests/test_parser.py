import pytest

from app.models import Parameter, ParserUsed, QueryType
from app.services.parser import (
    GAZETTEER,
    REGION_NAMES,
    UnsupportedQuery,
    parse_llm,
    parse_query,
    parse_rule_based,
)


@pytest.mark.parametrize(
    ("query", "query_type", "parameter"),
    [
        (
            "Show temperature profile near Mumbai in July 2024",
            QueryType.PROFILE,
            Parameter.TEMPERATURE,
        ),
        (
            "Plot SST time series at 19N, 72.8E from 2015-2024 and tell me if it is unusual",
            QueryType.TIME_SERIES,
            Parameter.SHALLOW_SST_PROXY,
        ),
        (
            "Show average salinity in the Bay of Bengal in 2023",
            QueryType.REGIONAL_AVERAGE,
            Parameter.SALINITY,
        ),
    ],
)
def test_pinned_query_grammar(query: str, query_type: QueryType, parameter: Parameter) -> None:
    parsed = parse_rule_based(query)

    assert parsed.query_type is query_type
    assert parsed.parameter is parameter
    assert parsed.parser_used is ParserUsed.RULE_BASED


def test_profile_query_extracts_month_and_year() -> None:
    parsed = parse_rule_based("Show temperature profile near Mumbai in July 2024")

    assert parsed.month == 7
    assert parsed.year_start == 2024
    assert parsed.year_end == 2024
    assert parsed.date_from == "2024-07-01"
    assert parsed.date_to == "2024-07-31"


@pytest.mark.parametrize("location", ["Chennai", "Maldives", "Kochi"])
def test_city_gazetteer_matches(location: str) -> None:
    parsed = parse_rule_based(f"Temperature profile near {location} in March 2022")

    assert parsed.location.latitude is not None
    assert parsed.location.longitude is not None


def test_deterministic_parser_has_at_least_50_place_aliases() -> None:
    assert len(GAZETTEER) >= 50


@pytest.mark.parametrize("location", sorted(GAZETTEER))
def test_every_gazetteer_alias_is_parseable(location: str) -> None:
    parsed = parse_rule_based(f"Show temperature near {location} in 2024")

    assert parsed.location.latitude is not None
    assert parsed.location.longitude is not None


@pytest.mark.parametrize("region", sorted(REGION_NAMES))
def test_every_named_region_alias_is_parseable(region: str) -> None:
    parsed = parse_rule_based(f"Show average salinity in the {region} in 2023")

    assert parsed.location.region_id is not None


def test_lat_lon_regex_handles_hemispheres() -> None:
    parsed = parse_rule_based("Salinity profile at 4.5°S, 55.2°E in 2024")

    assert parsed.location.latitude == -4.5
    assert parsed.location.longitude == 55.2


@pytest.mark.parametrize(
    ("query", "date_from", "date_to"),
    [
        ("temperature near Mumbai 2020-2024", "2020-01-01", "2024-12-31"),
        ("temperature near Mumbai April 2024", "2024-04-01", "2024-04-30"),
        ("temperature near Mumbai 2024", "2024-01-01", "2024-12-31"),
    ],
)
def test_date_extraction(query: str, date_from: str, date_to: str) -> None:
    parsed = parse_rule_based(query)

    assert parsed.date_from == date_from
    assert parsed.date_to == date_to


def test_parse_query_uses_deterministic_parser_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "GEMINI_API_KEY",
        "FLOATCHAT_LLM_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    assert parse_query("Temperature near Mumbai 2024").parser_used is ParserUsed.RULE_BASED


def test_unsupported_query_is_rejected() -> None:
    with pytest.raises(UnsupportedQuery):
        parse_rule_based("Will it rain tomorrow?")


def test_out_of_range_date_is_rejected() -> None:
    with pytest.raises(UnsupportedQuery):
        parse_rule_based("Temperature near Mumbai in 1999")


def test_rule_parser_understands_both_parameters() -> None:
    parsed = parse_rule_based(
        "Compare temperature and salinity near Kochi from 2021 to 2024 over time"
    )

    assert parsed.parameter is Parameter.ALL
    assert parsed.parameters == [Parameter.TEMPERATURE, Parameter.SALINITY]
    assert parsed.query_type is QueryType.TIME_SERIES


def test_rule_parser_preserves_sst_proxy_in_multi_parameter_query() -> None:
    parsed = parse_rule_based(
        "Plot SST and salinity near Kochi from 2021 to 2024 over time"
    )

    assert parsed.parameters == [Parameter.SHALLOW_SST_PROXY, Parameter.SALINITY]


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


def test_gemini_structured_output_is_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "server-only-test-key")
    monkeypatch.setenv("FLOATCHAT_LLM_MODEL", "gemini-2.5-flash")
    captured: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> _FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return _FakeResponse(
            {
                "output_text": """{
                  "query_type":"time_series",
                  "parameters":["temperature","salinity"],
                  "lat":9.97,"lon":76.24,"region_id":null,
                  "location_label":"Kochi coast",
                  "date_from":"2021-01-01","date_to":"2024-12-31",
                  "radius_km":100,"include_anomaly":true
                }"""
            }
        )

    monkeypatch.setattr("app.services.parser.httpx.post", fake_post)
    parsed = parse_llm("Compare temperature and salinity near Kochi")

    assert parsed.parser_used is ParserUsed.LLM
    assert parsed.parameter is Parameter.ALL
    assert parsed.parameters == [Parameter.TEMPERATURE, Parameter.SALINITY]
    assert str(captured["url"]).endswith(
        "/v1beta/models/gemini-2.5-flash:generateContent"
    )
    request_json = captured["json"]
    assert isinstance(request_json, dict)
    assert request_json["generationConfig"]["responseMimeType"] == "application/json"
    assert request_json["generationConfig"]["responseJsonSchema"]["additionalProperties"] is False
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["x-goog-api-key"] == "server-only-test-key"


@pytest.mark.parametrize("failure", [RuntimeError("provider exploded"), ValueError("bad JSON")])
def test_any_provider_failure_falls_back(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "server-only-test-key")

    def fail_post(*_args: object, **_kwargs: object) -> object:
        raise failure

    monkeypatch.setattr("app.services.parser.httpx.post", fail_post)
    parsed = parse_query("Show temperature near Mumbai in July 2024")

    assert parsed.parser_used is ParserUsed.RULE_BASED


def test_malformed_gemini_output_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "server-only-test-key")
    monkeypatch.setattr(
        "app.services.parser.httpx.post",
        lambda *_args, **_kwargs: _FakeResponse({"output_text": "not-json"}),
    )

    parsed = parse_query("Show salinity near Chennai in 2024")

    assert parsed.parser_used is ParserUsed.RULE_BASED
