import pandas as pd

from app.models import Parameter, QueryType
from app.services.aggregation import aggregate
from app.services.qc import apply_qc_filter


def observations() -> pd.DataFrame:
    rows = []
    for profile, platform, day, offset in (
        ("1:1", "1", 1, 0.0),
        ("2:1", "2", 2, 1.0),
    ):
        for pressure, temperature in ((5, 29.0), (20, 27.0), (75, 24.0), (150, 18.0)):
            rows.append(
                {
                    "profile_id": profile,
                    "platform_number": platform,
                    "time": pd.Timestamp(f"2024-07-{day:02d}", tz="UTC"),
                    "pres": pressure,
                    "source_row": pressure,
                    "position_qc": "1",
                    "data_mode": "D",
                    "temp_adjusted_qc": "1",
                    "temp_adjusted": temperature + offset,
                }
            )
    return pd.DataFrame(rows)


def test_profile_aggregation_uses_only_qc_retained_records() -> None:
    qc = apply_qc_filter(observations(), Parameter.TEMPERATURE)
    result = aggregate(qc, QueryType.PROFILE, Parameter.TEMPERATURE)

    assert result["type"] == "profile"
    assert len(result["bins"]) == 4
    assert result["bins"][0]["value"] == 29.5
    assert result["profile_count"] == 2
    assert result["overall_mean"] == 26.0
    assert "full-column per-profile medians" in result["aggregation_method"]


def test_shallow_time_series_uses_shallowest_observation_per_profile() -> None:
    qc = apply_qc_filter(observations(), Parameter.SHALLOW_SST_PROXY)
    result = aggregate(qc, QueryType.TIME_SERIES, Parameter.SHALLOW_SST_PROXY)

    assert result["series"][0]["value"] == 29.5
    assert "not satellite" in result["proxy_note"]
