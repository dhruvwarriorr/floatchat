from __future__ import annotations

from typing import Any

import pandas as pd

from app.models import Parameter, QueryType
from app.services.qc import QCResult

DEPTH_BINS = [0.0, 10.0, 25.0, 50.0, 100.0, 200.0, 300.0, 500.000001]
DEPTH_LABELS = ["0–10", "10–25", "25–50", "50–100", "100–200", "200–300", "300–500"]
TRACE_SAMPLE_LIMIT = 25


def _trace(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "observation_count": 0,
            "profile_count": 0,
            "float_count": 0,
            "profile_ids": [],
            "float_ids": [],
            "source_records": [],
            "truncated": False,
        }
    profiles = sorted(frame["profile_id"].dropna().astype(str).unique().tolist())
    floats = sorted(frame["platform_number"].dropna().astype(str).unique().tolist())
    source_records: list[str] = []
    if {"_source_file", "source_row"}.issubset(frame.columns):
        refs = (
            frame[["_source_file", "source_row"]]
            .dropna()
            .drop_duplicates()
            .sort_values(["_source_file", "source_row"])
        )
        source_records = [
            f"{source_file}:{int(source_row)}"
            for source_file, source_row in refs.itertuples(index=False, name=None)
        ]
    truncated = any(
        len(values) > TRACE_SAMPLE_LIMIT for values in (profiles, floats, source_records)
    )
    return {
        "observation_count": int(len(frame)),
        "profile_count": len(profiles),
        "float_count": len(floats),
        "profile_ids": profiles[:TRACE_SAMPLE_LIMIT],
        "float_ids": floats[:TRACE_SAMPLE_LIMIT],
        "source_records": source_records[:TRACE_SAMPLE_LIMIT],
        "truncated": truncated,
    }


def _unit(parameter: Parameter | str) -> str:
    value = parameter.value if isinstance(parameter, Parameter) else str(parameter)
    return "PSU" if value == Parameter.SALINITY.value else "°C"


def _empty(kind: str, parameter: Parameter | str, method: str) -> dict[str, Any]:
    value = parameter.value if isinstance(parameter, Parameter) else str(parameter)
    return {
        "type": kind,
        "parameter": value,
        "unit": _unit(parameter),
        "aggregation_method": method,
        "current_value": None,
    }


def _profile(df: pd.DataFrame, value_col: str, parameter: Parameter) -> dict[str, Any]:
    method = (
        "Display: per-profile median within fixed pressure bins, then median across "
        "profiles; representative value: mean of full-column per-profile medians"
    )
    if df.empty:
        return {**_empty("profile", parameter, method), "bins": [], "overall_mean": None}

    usable = df.loc[df["pres"].between(0, 500, inclusive="both")].copy()
    if usable.empty:
        return {**_empty("profile", parameter, method), "bins": [], "overall_mean": None}
    usable["depth_bin"] = pd.cut(
        usable["pres"], bins=DEPTH_BINS, labels=DEPTH_LABELS, right=False, include_lowest=True
    )
    per_profile = (
        usable.dropna(subset=["depth_bin"])
        .groupby(["profile_id", "platform_number", "depth_bin"], observed=True)[value_col]
        .median()
        .reset_index(name="profile_value")
    )
    rows: list[dict[str, Any]] = []
    for index, label in enumerate(DEPTH_LABELS):
        subset = per_profile.loc[per_profile["depth_bin"].astype(str) == label]
        if subset.empty:
            continue
        depth_min = DEPTH_BINS[index]
        depth_max = 500.0 if index == len(DEPTH_LABELS) - 1 else DEPTH_BINS[index + 1]
        rows.append(
            {
                "depth_bin": label,
                "depth_min": depth_min,
                "depth_max": depth_max,
                "depth_mid": (depth_min + depth_max) / 2,
                "value": float(subset["profile_value"].median()),
                "profile_count": int(subset["profile_id"].nunique()),
                "float_count": int(subset["platform_number"].astype(str).nunique()),
                "unit": _unit(parameter),
                "trace": _trace(
                    usable.loc[usable["depth_bin"].astype(str) == label]
                ),
            }
        )
    # The production full-column baseline is built from one full-depth median per
    # profile. Use the identical current-period statistic for any later z-score;
    # the fixed 0–500 dbar bins remain a separate display aggregation.
    overall = float(df.groupby("profile_id")[value_col].median().mean())
    return {
        "type": "profile",
        "parameter": parameter.value,
        "bins": rows,
        "overall_mean": overall,
        "current_value": overall,
        "profile_count": int(per_profile["profile_id"].nunique()),
        "unit": _unit(parameter),
        "aggregation_method": method,
        "trace": _trace(df),
    }


def _profile_values_for_time_series(
    df: pd.DataFrame, value_col: str, parameter: Parameter
) -> pd.DataFrame:
    if parameter is Parameter.SHALLOW_SST_PROXY:
        shallow = df.loc[df["pres"].between(0, 10, inclusive="both")].copy()
        if shallow.empty:
            return shallow
        shallow = shallow.sort_values(["profile_id", "pres", "source_row"])
        return shallow.groupby("profile_id", as_index=False).first()[
            ["profile_id", "platform_number", "time", value_col]
        ]
    return (
        df.groupby("profile_id", as_index=False)
        .agg(
            platform_number=("platform_number", "first"),
            time=("time", "first"),
            **{value_col: (value_col, "median")},
        )
        .dropna(subset=[value_col])
    )


def _time_series(df: pd.DataFrame, value_col: str, parameter: Parameter) -> dict[str, Any]:
    method = (
        "Shallowest QC-passed 0–10 dbar observation per profile, then monthly mean"
        if parameter is Parameter.SHALLOW_SST_PROXY
        else "Per-profile full-column median, then monthly mean"
    )
    if df.empty:
        return {**_empty("time_series", parameter, method), "series": []}
    profile_values = _profile_values_for_time_series(df, value_col, parameter)
    if profile_values.empty:
        return {**_empty("time_series", parameter, method), "series": []}
    profile_values["month"] = (
        pd.to_datetime(profile_values["time"], utc=True)
        .dt.tz_convert(None)
        .dt.to_period("M")
        .astype(str)
    )
    monthly = (
        profile_values.groupby("month", as_index=False)
        .agg(
            value=(value_col, "mean"),
            profile_count=("profile_id", "nunique"),
            float_count=("platform_number", lambda values: values.astype(str).nunique()),
        )
        .sort_values("month")
    )
    series = []
    for row in monthly.itertuples(index=False):
        month = str(row.month)
        ids = set(profile_values.loc[profile_values["month"] == month, "profile_id"].astype(str))
        contributing = df.loc[df["profile_id"].astype(str).isin(ids)]
        series.append(
            {
                "month": month,
                "value": float(row.value),
                "profile_count": int(row.profile_count),
                "float_count": int(row.float_count),
                "unit": _unit(parameter),
                "trace": _trace(contributing),
            }
        )
    current_value = float(monthly["value"].mean())
    result: dict[str, Any] = {
        "type": "time_series",
        "parameter": parameter.value,
        "series": series,
        "current_value": current_value,
        "profile_count": int(profile_values["profile_id"].nunique()),
        "unit": _unit(parameter),
        "aggregation_method": method,
        "trace": _trace(df),
    }
    if parameter is Parameter.SHALLOW_SST_PROXY:
        result["proxy_note"] = (
            "Shallowest QC-passed ARGO observation from 0–10 dbar; "
            "not satellite sea-surface temperature."
        )
    return result


def _regional(df: pd.DataFrame, value_col: str, parameter: Parameter) -> dict[str, Any]:
    method = "0–100 dbar median per profile, monthly means, then mean of represented months"
    if df.empty:
        return {
            **_empty("regional_average", parameter, method),
            "monthly_means": [],
            "annual_mean": None,
            "represented_months": 0,
            "depth_range": "0–100 dbar",
        }
    upper = df.loc[df["pres"].between(0, 100, inclusive="both")]
    if upper.empty:
        return {
            **_empty("regional_average", parameter, method),
            "monthly_means": [],
            "annual_mean": None,
            "represented_months": 0,
            "depth_range": "0–100 dbar",
        }
    profile_values = upper.groupby("profile_id", as_index=False).agg(
        platform_number=("platform_number", "first"),
        time=("time", "first"),
        **{value_col: (value_col, "median")},
    )
    profile_values["month"] = (
        pd.to_datetime(profile_values["time"], utc=True)
        .dt.tz_convert(None)
        .dt.to_period("M")
        .astype(str)
    )
    monthly = (
        profile_values.groupby("month", as_index=False)
        .agg(
            value=(value_col, "mean"),
            profile_count=("profile_id", "nunique"),
            float_count=("platform_number", lambda values: values.astype(str).nunique()),
        )
        .sort_values("month")
    )
    rows = []
    for row in monthly.itertuples(index=False):
        month = str(row.month)
        ids = set(profile_values.loc[profile_values["month"] == month, "profile_id"].astype(str))
        contributing = upper.loc[upper["profile_id"].astype(str).isin(ids)]
        rows.append(
            {
                "month": month,
                "value": float(row.value),
                "profile_count": int(row.profile_count),
                "float_count": int(row.float_count),
                "unit": _unit(parameter),
                "trace": _trace(contributing),
            }
        )
    annual_mean = float(monthly["value"].mean())
    return {
        "type": "regional_average",
        "parameter": parameter.value,
        "monthly_means": rows,
        "annual_mean": annual_mean,
        "current_value": annual_mean,
        "represented_months": len(rows),
        "depth_range": "0–100 dbar",
        "unit": _unit(parameter),
        "aggregation_method": method,
        "trace": _trace(upper),
    }


def aggregate(qc_result: QCResult, query_type: QueryType, parameter: Parameter) -> dict[str, Any]:
    if query_type is QueryType.PROFILE:
        return _profile(qc_result.retained, qc_result.value_col, parameter)
    if query_type is QueryType.TIME_SERIES:
        return _time_series(qc_result.retained, qc_result.value_col, parameter)
    if query_type is QueryType.REGIONAL_AVERAGE:
        return _regional(qc_result.retained, qc_result.value_col, parameter)
    raise ValueError(f"Unsupported query type: {query_type}")


def compute_current_mean(agg_data: dict[str, Any], query_type: QueryType) -> float | None:
    if query_type is QueryType.PROFILE:
        value = agg_data.get("overall_mean")
    elif query_type is QueryType.TIME_SERIES:
        series = agg_data.get("series", [])
        values = [float(point["value"]) for point in series if point.get("value") is not None]
        value = sum(values) / len(values) if values else None
    elif query_type is QueryType.REGIONAL_AVERAGE:
        value = agg_data.get("annual_mean")
    else:
        value = None
    return float(value) if value is not None else None
