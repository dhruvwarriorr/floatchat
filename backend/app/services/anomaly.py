from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import Parameter, QueryType


@dataclass(frozen=True)
class AnomalyScoreResult:
    z_score: float
    label: str
    current_value: float
    baseline_mean: float
    baseline_std: float
    baseline_n: int
    baseline_period: str
    explanation: str


def load_production_baseline(baseline_dir: Path) -> pd.DataFrame | None:
    path = baseline_dir / "production" / "baseline.parquet"
    if not path.is_file():
        return None
    frame = pd.read_parquet(path)
    if "baseline_type" not in frame or not frame["baseline_type"].eq("production").all():
        raise RuntimeError("SAFETY: Non-production baseline loaded!")
    return frame


def baseline_parameter_name(parameter: Parameter | str, query_type: QueryType | str) -> str:
    parameter_value = parameter.value if isinstance(parameter, Parameter) else str(parameter)
    query_value = query_type.value if isinstance(query_type, QueryType) else str(query_type)
    if query_value == QueryType.REGIONAL_AVERAGE.value:
        base = "salinity" if parameter_value == Parameter.SALINITY.value else "temperature"
        return f"{base}_upper_100"
    if parameter_value == Parameter.SHALLOW_SST_PROXY.value:
        return "temperature_shallow"
    return parameter_value


def get_baseline_for_month(
    baseline_df: pd.DataFrame | None,
    parameter: str,
    month: int,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    region_id: str | None = None,
) -> dict[str, Any] | None:
    if baseline_df is None or baseline_df.empty:
        return None
    subset = baseline_df.loc[
        (baseline_df["parameter"].astype(str) == parameter)
        & (pd.to_numeric(baseline_df["calendar_month"], errors="coerce") == month)
    ]
    if subset.empty:
        return None

    selected = pd.DataFrame()
    if region_id and "selection_type" in subset and "selection_id" in subset:
        selected = subset.loc[
            (subset["selection_type"] == "region") & (subset["selection_id"] == region_id)
        ]
    if (
        selected.empty
        and latitude is not None
        and longitude is not None
        and {
            "grid_lat",
            "grid_lon",
        }
        <= set(subset.columns)
    ):
        grid_lat = math.floor(latitude / 2.0) * 2.0
        grid_lon = math.floor(longitude / 2.0) * 2.0
        selected = subset.loc[
            (subset["selection_type"] == "grid")
            & (subset["grid_lat"] == grid_lat)
            & (subset["grid_lon"] == grid_lon)
        ]
    if selected.empty and "selection_type" in subset:
        selected = subset.loc[subset["selection_type"] == "global"]
    if selected.empty:
        return None

    row = selected.iloc[0]
    standard_deviation = float(row["std"])
    if not math.isfinite(standard_deviation):
        standard_deviation = 0.0
    selection_type = str(row.get("selection_type", "global"))
    grid_lat = row.get("grid_lat")
    grid_lon = row.get("grid_lon")
    grid_bounds = None
    if selection_type == "grid" and pd.notna(grid_lat) and pd.notna(grid_lon):
        south = float(grid_lat)
        west = float(grid_lon)
        grid_bounds = {"south": south, "west": west, "north": south + 2.0, "east": west + 2.0}
    return {
        "mean": float(row["mean"]),
        "std": standard_deviation,
        "n": int(row["n"]),
        "calendar_month": int(row["calendar_month"]),
        "distinct_float_count": int(row.get("distinct_float_count", 0)),
        "year_min": int(row["year_min"]),
        "year_max": int(row["year_max"]),
        "selection_id": str(row.get("selection_id", "all-available")),
        "selection_type": selection_type,
        "grid_bounds": grid_bounds,
    }


def score_anomaly(
    current_value: float,
    baseline: dict[str, Any],
    parameter: Parameter | str,
) -> AnomalyScoreResult | None:
    standard_deviation = float(baseline["std"])
    if standard_deviation <= 0 or not math.isfinite(standard_deviation):
        return None
    baseline_mean = float(baseline["mean"])
    if not math.isfinite(current_value) or not math.isfinite(baseline_mean):
        return None

    z_score = (current_value - baseline_mean) / standard_deviation
    magnitude = abs(z_score)
    if magnitude < 1.5:
        label = "normal"
    elif magnitude < 2.5:
        label = "mild_positive" if z_score > 0 else "mild_negative"
    else:
        label = "strong_positive" if z_score > 0 else "strong_negative"

    parameter_value = parameter.value if isinstance(parameter, Parameter) else str(parameter)
    anomaly_name = (
        "salinity anomaly" if "salinity" in parameter_value else "upper-ocean temperature anomaly"
    )
    direction = "above" if z_score >= 0 else "below"
    baseline_period = f"{int(baseline['year_min'])}–{int(baseline['year_max'])}"
    explanation = (
        f"The QC-passed aggregate is {abs(z_score):.2f} standard deviations {direction} "
        f"the {baseline_period} production baseline for this selection. This is a "
        f"{anomaly_name} screening result, not a formal event declaration."
    )
    return AnomalyScoreResult(
        z_score=float(z_score),
        label=label,
        current_value=float(current_value),
        baseline_mean=baseline_mean,
        baseline_std=standard_deviation,
        baseline_n=int(baseline["n"]),
        baseline_period=baseline_period,
        explanation=explanation,
    )
