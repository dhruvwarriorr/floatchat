from __future__ import annotations

import re

from app.models import Parameter, ParserUsed, QueryLocation, QueryParams, QueryType


class UnsupportedQuery(ValueError):
    """Raised when the supported deterministic grammar cannot parse a query."""


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _years(query: str) -> tuple[int | None, int | None]:
    years = [int(year) for year in re.findall(r"\b20\d{2}\b", query)]
    if not years:
        return None, None
    if len(years) == 1:
        return years[0], years[0]
    return years[0], years[1]


def _month(query: str) -> int | None:
    return next((number for name, number in MONTHS.items() if name in query), None)


def parse_rule_based(raw_query: str) -> QueryParams:
    query = raw_query.lower().replace("–", "-").replace("—", "-").replace("°", "")
    year_start, year_end = _years(query)
    anomaly_requested = any(
        word in query for word in ("anomaly", "anomalous", "unusual", "warming")
    )

    if "mumbai" in query and "temperature" in query:
        return QueryParams(
            query_type=QueryType.PROFILE,
            parameter=Parameter.TEMPERATURE,
            location=QueryLocation(label="Mumbai coast", latitude=19.0, longitude=72.8),
            year_start=year_start,
            year_end=year_end,
            month=_month(query),
            anomaly_requested=anomaly_requested,
            parser_used=ParserUsed.RULE_BASED,
        )

    if "bay of bengal" in query and "salinity" in query:
        return QueryParams(
            query_type=QueryType.REGIONAL_AVERAGE,
            parameter=Parameter.SALINITY,
            location=QueryLocation(label="Bay of Bengal", region_id="bay-of-bengal"),
            year_start=year_start,
            year_end=year_end,
            month=_month(query),
            anomaly_requested=anomaly_requested,
            parser_used=ParserUsed.RULE_BASED,
        )

    has_pinned_coordinates = "19n" in query and "72.8e" in query
    if "sst" in query or has_pinned_coordinates:
        return QueryParams(
            query_type=QueryType.TIME_SERIES,
            parameter=Parameter.SHALLOW_SST_PROXY,
            location=QueryLocation(
                label="Mumbai offshore point", latitude=19.0, longitude=72.8
            ),
            year_start=year_start,
            year_end=year_end,
            month=_month(query),
            anomaly_requested=anomaly_requested,
            parser_used=ParserUsed.RULE_BASED,
        )

    if "arabian sea" in query and "warming" in query:
        return QueryParams(
            query_type=QueryType.TIME_SERIES,
            parameter=Parameter.TEMPERATURE,
            location=QueryLocation(label="Arabian Sea", region_id="arabian-sea"),
            year_start=year_start,
            year_end=year_end,
            month=_month(query),
            anomaly_requested=True,
            parser_used=ParserUsed.RULE_BASED,
        )

    raise UnsupportedQuery(
        "The query is outside the frozen profile, regional-average, and time-series grammar."
    )
