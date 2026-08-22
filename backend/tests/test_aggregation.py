import pandas as pd

from app.models import Parameter, QueryType
from app.services.aggregation import (
    aggregate,
    compute_density_profile,
    compute_heat_content,
    compute_hovmoller,
    compute_seasonal_cycle,
    compute_supplementary_views,
    compute_ts_diagram,
    compute_year_over_year,
)
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


def supplementary_observations() -> pd.DataFrame:
    rows = []
    source_row = 0
    for year in (2023, 2024):
        for month in (1, 7):
            profile_id = f"{year}:{month}"
            for pressure, temperature, salinity in (
                (0.0, 29.0, 34.2),
                (50.0, 26.0, 34.8),
                (150.0, 20.0, 35.1),
                (300.0, 14.0, 35.0),
            ):
                source_row += 1
                rows.append(
                    {
                        "profile_id": profile_id,
                        "platform_number": str(year),
                        "time": pd.Timestamp(f"{year}-{month:02d}-15", tz="UTC"),
                        "pres": pressure,
                        "source_row": source_row,
                        "temp_adjusted": temperature + (year - 2023) * 0.2,
                        "psal_adjusted": salinity,
                    }
                )
    return pd.DataFrame(rows)


def test_supplementary_ocean_views_have_units_and_chartable_values() -> None:
    frame = supplementary_observations()

    ts = compute_ts_diagram(frame)
    density = compute_density_profile(frame)
    heat = compute_heat_content(frame, "temp_adjusted")
    hovmoller = compute_hovmoller(frame, "temp_adjusted", Parameter.TEMPERATURE)
    seasonal = compute_seasonal_cycle(frame, "temp_adjusted", Parameter.TEMPERATURE)
    yearly = compute_year_over_year(frame, "temp_adjusted", Parameter.TEMPERATURE)

    assert ts is not None and len(ts["points"]) == len(frame)
    assert density is not None and density["bins"][0]["unit"] == "kg/m³"
    assert heat is not None and heat["value_mj_per_m2"] > 0
    assert hovmoller is not None and {cell["month"] for cell in hovmoller["grid"]}
    assert seasonal is not None and [month["month"] for month in seasonal["months"]] == [1, 7]
    assert yearly is not None and set(yearly["years"]) == {"2023", "2024"}


def test_ts_diagram_sampling_is_bounded_and_deterministic() -> None:
    frame = pd.concat([supplementary_observations()] * 40, ignore_index=True)

    first = compute_ts_diagram(frame)
    second = compute_ts_diagram(frame)

    assert first is not None and second is not None
    assert len(first["points"]) == 500
    assert first["points"] == second["points"]
    assert first["profile_count"] == 4


def test_supplementary_views_are_best_effort_and_keep_successful_results() -> None:
    frame = supplementary_observations().drop(columns=["psal_adjusted"])

    result = compute_supplementary_views(
        frame,
        Parameter.TEMPERATURE,
        value_col="temp_adjusted",
    )

    assert "ts_diagram" not in result
    assert "density_profile" not in result
    assert {"heat_content", "hovmoller", "seasonal_cycle", "year_over_year"} <= set(result)
