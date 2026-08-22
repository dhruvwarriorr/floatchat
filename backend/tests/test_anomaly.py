from pathlib import Path

import pandas as pd
import pytest

from app.services.anomaly import (
    get_baseline_for_month,
    load_production_baseline,
    score_anomaly,
)


def baseline(std: float = 1.0) -> dict[str, float | int]:
    return {
        "mean": 0.0,
        "std": std,
        "n": 21,
        "year_min": 2015,
        "year_max": 2023,
    }


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        (1.49, "normal"),
        (1.5, "mild_positive"),
        (2.49, "mild_positive"),
        (2.5, "strong_positive"),
        (-1.5, "mild_negative"),
        (-2.5, "strong_negative"),
    ],
)
def test_z_score_policy_boundaries(current: float, expected: str) -> None:
    result = score_anomaly(current, baseline(), "temperature")

    assert result is not None
    assert result.label == expected
    assert "marine heatwave" not in result.explanation.lower()


@pytest.mark.parametrize("standard_deviation", [0.0, -1.0])
def test_invalid_standard_deviation_skips_scoring(standard_deviation: float) -> None:
    assert score_anomaly(3.0, baseline(standard_deviation), "salinity") is None


def test_runtime_rejects_validation_baseline(tmp_path: Path) -> None:
    directory = tmp_path / "production"
    directory.mkdir()
    pd.DataFrame([{"baseline_type": "validation", "mean": 1.0, "std": 1.0, "n": 10}]).to_parquet(
        directory / "baseline.parquet"
    )

    with pytest.raises(RuntimeError, match="Non-production"):
        load_production_baseline(tmp_path)


def test_baseline_lookup_returns_the_selected_calendar_month() -> None:
    frame = pd.DataFrame(
        [
            {
                "parameter": "temperature",
                "selection_type": "grid",
                "selection_id": "grid-10-70",
                "grid_lat": 10.0,
                "grid_lon": 70.0,
                "calendar_month": 7,
                "mean": 27.5,
                "std": 0.5,
                "n": 24,
                "distinct_float_count": 3,
                "year_min": 2015,
                "year_max": 2023,
            }
        ]
    )

    result = get_baseline_for_month(frame, "temperature", 7, latitude=10.0, longitude=70.0)

    assert result is not None
    assert result["mean"] == 27.5
    assert result["calendar_month"] == 7
