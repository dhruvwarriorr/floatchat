import pytest

from app.models import Parameter, ParserUsed, QueryType
from app.services.parser import UnsupportedQuery, parse_rule_based


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


def test_unsupported_query_is_rejected() -> None:
    with pytest.raises(UnsupportedQuery):
        parse_rule_based("Will it rain tomorrow?")
