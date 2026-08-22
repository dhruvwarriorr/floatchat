from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.models import Parameter, QueryType
from app.services.qc import QCResult

DEPTH_BINS = [0.0, 10.0, 25.0, 50.0, 100.0, 200.0, 300.0, 500.000001]
DEPTH_LABELS = ["0–10", "10–25", "25–50", "50–100", "100–200", "200–300", "300–500"]
TRACE_SAMPLE_LIMIT = 25


def _light_trace(frame: pd.DataFrame) -> dict[str, Any]:
    """Cheap counts-only trace for secondary views that never render IDs.

    Skips the source-record dedup/sort, which dominates aggregation cost on large
    regional frames.
    """

    return {
        "observation_count": int(len(frame)),
        "profile_count": int(frame["profile_id"].nunique()) if "profile_id" in frame else 0,
        "float_count": int(frame["platform_number"].nunique()) if "platform_number" in frame else 0,
        "profile_ids": [],
        "float_ids": [],
        "source_records": [],
        "truncated": False,
    }


def _trace(frame: pd.DataFrame, *, light: bool = False) -> dict[str, Any]:
    if light:
        return _light_trace(frame)
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


def _profile(
    df: pd.DataFrame, value_col: str, parameter: Parameter, with_trace: bool = True
) -> dict[str, Any]:
    light = not with_trace
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
                    usable.loc[usable["depth_bin"].astype(str) == label], light=light
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
        "trace": _trace(df, light=light),
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


def _time_series(
    df: pd.DataFrame, value_col: str, parameter: Parameter, with_trace: bool = True
) -> dict[str, Any]:
    light = not with_trace
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
                "trace": _trace(contributing, light=light),
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
        "trace": _trace(df, light=light),
    }
    if parameter is Parameter.SHALLOW_SST_PROXY:
        result["proxy_note"] = (
            "Shallowest QC-passed ARGO observation from 0–10 dbar; "
            "not satellite sea-surface temperature."
        )
    return result


def _regional(
    df: pd.DataFrame, value_col: str, parameter: Parameter, with_trace: bool = True
) -> dict[str, Any]:
    light = not with_trace
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
                "trace": _trace(contributing, light=light),
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
        "trace": _trace(upper, light=light),
    }


def aggregate(
    qc_result: QCResult,
    query_type: QueryType,
    parameter: Parameter,
    with_trace: bool = True,
) -> dict[str, Any]:
    if query_type is QueryType.PROFILE:
        return _profile(qc_result.retained, qc_result.value_col, parameter, with_trace)
    if query_type is QueryType.TIME_SERIES:
        return _time_series(qc_result.retained, qc_result.value_col, parameter, with_trace)
    if query_type is QueryType.REGIONAL_AVERAGE:
        return _regional(qc_result.retained, qc_result.value_col, parameter, with_trace)
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


# ---------------------------------------------------------------------------
# Supplementary scientific views.
#
# Every function below is best-effort: it returns ``None`` when the QC-passed
# frame lacks the columns or density it needs. None of them replace the primary
# aggregation, the QC boundary, or the evidence policy; they are additional
# read-only visualisations derived from the same QC-passed observations.
# ---------------------------------------------------------------------------

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TS_DIAGRAM_LIMIT = 500


def _calendar_month(frame: pd.DataFrame) -> pd.Series:
    if "calendar_month" in frame:
        return pd.to_numeric(frame["calendar_month"], errors="coerce")
    return pd.to_datetime(frame["time"], utc=True, errors="coerce").dt.month


def _per_profile_value(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    return (
        df.groupby("profile_id", as_index=False)
        .agg(
            platform_number=("platform_number", "first"),
            time=("time", "first"),
            **{value_col: (value_col, "median")},
        )
        .dropna(subset=[value_col])
    )


def _seawater_density(temperature: pd.Series, salinity: pd.Series) -> pd.Series:
    """Simplified Millero & Poisson (1981) surface density in kg/m³.

    This is a rough at-surface approximation (pressure term omitted); it is used
    only for a relative density-profile visualisation, never for a scientific
    claim.
    """

    t = pd.to_numeric(temperature, errors="coerce")
    s = pd.to_numeric(salinity, errors="coerce")
    rho_w = (
        999.842594
        + 6.793952e-2 * t
        - 9.095290e-3 * t**2
        + 1.001685e-4 * t**3
        - 1.120083e-6 * t**4
        + 6.536332e-9 * t**5
    )
    coefficient = (
        0.824493
        - 4.0899e-3 * t
        + 7.6438e-5 * t**2
        - 8.2467e-7 * t**3
        + 5.3875e-9 * t**4
    )
    return rho_w + coefficient * s


def compute_ts_diagram(df: pd.DataFrame) -> dict[str, Any] | None:
    if df.empty or not {"temp_adjusted", "psal_adjusted", "pres"}.issubset(df.columns):
        return None
    usable = df.dropna(subset=["temp_adjusted", "psal_adjusted"]).copy()
    usable = usable.loc[pd.to_numeric(usable["temp_adjusted"], errors="coerce").notna()]
    usable = usable.loc[pd.to_numeric(usable["psal_adjusted"], errors="coerce").notna()]
    if usable.empty:
        return None
    if len(usable) > TS_DIAGRAM_LIMIT:
        usable = usable.sample(TS_DIAGRAM_LIMIT, random_state=0)
    points = [
        {
            "temperature": float(row.temp_adjusted),
            "salinity": float(row.psal_adjusted),
            "pressure": float(row.pres) if pd.notna(row.pres) else None,
            "profile_id": str(row.profile_id),
        }
        for row in usable.itertuples(index=False)
    ]
    return {
        "type": "ts_diagram",
        "points": points,
        "profile_count": int(usable["profile_id"].nunique()),
        "float_count": int(usable["platform_number"].astype(str).nunique()),
    }


def compute_density_profile(df: pd.DataFrame) -> dict[str, Any] | None:
    if df.empty or not {"temp_adjusted", "psal_adjusted", "pres"}.issubset(df.columns):
        return None
    usable = df.dropna(subset=["temp_adjusted", "psal_adjusted"]).copy()
    usable = usable.loc[usable["pres"].between(0, 500, inclusive="both")]
    if usable.empty:
        return None
    usable["density"] = _seawater_density(usable["temp_adjusted"], usable["psal_adjusted"])
    usable = usable.dropna(subset=["density"])
    if usable.empty:
        return None
    usable["depth_bin"] = pd.cut(
        usable["pres"], bins=DEPTH_BINS, labels=DEPTH_LABELS, right=False, include_lowest=True
    )
    bins: list[dict[str, Any]] = []
    for index, label in enumerate(DEPTH_LABELS):
        subset = usable.loc[usable["depth_bin"].astype(str) == label]
        if subset.empty:
            continue
        depth_min = DEPTH_BINS[index]
        depth_max = 500.0 if index == len(DEPTH_LABELS) - 1 else DEPTH_BINS[index + 1]
        bins.append(
            {
                "depth_bin": label,
                "depth_mid": (depth_min + depth_max) / 2,
                "density": float(subset["density"].median()),
                "unit": "kg/m³",
            }
        )
    return {"type": "density_profile", "bins": bins} if bins else None


def compute_heat_content(df: pd.DataFrame, value_col: str) -> dict[str, Any] | None:
    if df.empty or value_col != "temp_adjusted" or "pres" not in df.columns:
        return None
    upper = df.loc[df["pres"].between(0, 300, inclusive="both")].dropna(subset=[value_col])
    if upper.empty:
        return None
    density, specific_heat = 1025.0, 3850.0
    integrals: list[float] = []
    for _profile_id, group in upper.groupby("profile_id"):
        ordered = group.sort_values("pres")
        pressures = ordered["pres"].to_numpy(dtype=float)
        temperatures = ordered[value_col].to_numpy(dtype=float)
        if len(pressures) < 2:
            continue
        integrals.append(float(np.trapezoid(temperatures, pressures)))
    if not integrals:
        return None
    mean_integral = sum(integrals) / len(integrals)
    heat_content = density * specific_heat * mean_integral / 1e6
    return {
        "type": "heat_content",
        "value_mj_per_m2": float(heat_content),
        "profile_count": len(integrals),
        "depth_range": "0–300 dbar",
    }


def compute_hovmoller(
    df: pd.DataFrame, value_col: str, parameter: Parameter
) -> dict[str, Any] | None:
    if df.empty or "pres" not in df.columns:
        return None
    usable = df.loc[df["pres"].between(0, 500, inclusive="both")].dropna(subset=[value_col]).copy()
    if usable.empty:
        return None
    usable["month"] = (
        pd.to_datetime(usable["time"], utc=True).dt.tz_convert(None).dt.to_period("M").astype(str)
    )
    usable["depth_bin"] = pd.cut(
        usable["pres"], bins=DEPTH_BINS, labels=DEPTH_LABELS, right=False, include_lowest=True
    )
    grid: list[dict[str, Any]] = []
    grouped = (
        usable.dropna(subset=["depth_bin"])
        .groupby(["month", "depth_bin"], observed=True)[value_col]
        .median()
        .reset_index()
    )
    depth_mid = {
        label: (
            DEPTH_BINS[index]
            + (500.0 if index == len(DEPTH_LABELS) - 1 else DEPTH_BINS[index + 1])
        )
        / 2
        for index, label in enumerate(DEPTH_LABELS)
    }
    for row in grouped.itertuples(index=False):
        label = str(row.depth_bin)
        grid.append(
            {
                "month": str(row.month),
                "depth_bin": label,
                "depth_mid": depth_mid.get(label),
                "value": float(getattr(row, value_col)),
            }
        )
    if not grid:
        return None
    return {
        "type": "hovmoller",
        "grid": grid,
        "parameter": parameter.value,
        "unit": _unit(parameter),
    }


def compute_seasonal_cycle(
    df: pd.DataFrame, value_col: str, parameter: Parameter
) -> dict[str, Any] | None:
    if df.empty:
        return None
    per_profile = _per_profile_value(df, value_col)
    if per_profile.empty:
        return None
    per_profile["calendar_month"] = pd.to_datetime(
        per_profile["time"], utc=True
    ).dt.tz_convert(None).dt.month
    months: list[dict[str, Any]] = []
    for month in range(1, 13):
        subset = per_profile.loc[per_profile["calendar_month"] == month]
        if subset.empty:
            continue
        values = subset[value_col]
        months.append(
            {
                "month": month,
                "month_label": MONTH_LABELS[month - 1],
                "mean": float(values.mean()),
                "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
                "count": int(len(values)),
            }
        )
    if not months:
        return None
    return {
        "type": "seasonal_cycle",
        "months": months,
        "parameter": parameter.value,
        "unit": _unit(parameter),
    }


def compute_year_over_year(
    df: pd.DataFrame, value_col: str, parameter: Parameter
) -> dict[str, Any] | None:
    if df.empty:
        return None
    per_profile = _per_profile_value(df, value_col)
    if per_profile.empty:
        return None
    stamps = pd.to_datetime(per_profile["time"], utc=True).dt.tz_convert(None)
    per_profile["year"] = stamps.dt.year
    per_profile["calendar_month"] = stamps.dt.month
    years: dict[str, list[dict[str, Any]]] = {}
    grouped = (
        per_profile.groupby(["year", "calendar_month"], as_index=False)[value_col].mean()
    )
    if grouped["year"].nunique() < 2:
        return None
    for row in grouped.itertuples(index=False):
        year = str(int(row.year))
        years.setdefault(year, []).append(
            {
                "month": int(row.calendar_month),
                "month_label": MONTH_LABELS[int(row.calendar_month) - 1],
                "value": float(getattr(row, value_col)),
            }
        )
    for entries in years.values():
        entries.sort(key=lambda item: item["month"])
    return {
        "type": "year_over_year",
        "years": years,
        "parameter": parameter.value,
        "unit": _unit(parameter),
    }


def compute_anomaly_trend(
    df: pd.DataFrame,
    value_col: str,
    parameter: Parameter,
    baseline_df: Any,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    region_id: str | None = None,
) -> dict[str, Any] | None:
    if df.empty or baseline_df is None:
        return None
    from app.services.anomaly import baseline_parameter_name, get_baseline_for_month, score_anomaly

    baseline_parameter = baseline_parameter_name(parameter, QueryType.TIME_SERIES)
    per_profile = _per_profile_value(df, value_col)
    if per_profile.empty:
        return None
    stamps = pd.to_datetime(per_profile["time"], utc=True).dt.tz_convert(None)
    per_profile["month"] = stamps.dt.to_period("M").astype(str)
    monthly = per_profile.groupby("month", as_index=False)[value_col].mean().sort_values("month")
    series: list[dict[str, Any]] = []
    for row in monthly.itertuples(index=False):
        month_str = str(row.month)
        calendar_month = int(month_str[5:7])
        baseline = get_baseline_for_month(
            baseline_df,
            baseline_parameter,
            calendar_month,
            latitude=latitude,
            longitude=longitude,
            region_id=region_id,
        )
        if baseline is None:
            continue
        scored = score_anomaly(float(getattr(row, value_col)), baseline, parameter)
        if scored is None:
            continue
        series.append(
            {
                "month": month_str,
                "z_score": float(scored.z_score),
                "label": scored.label,
                "current_value": float(scored.current_value),
                "baseline_mean": float(scored.baseline_mean),
            }
        )
    if not series:
        return None
    return {
        "type": "anomaly_trend",
        "series": series,
        "parameter": parameter.value,
        "unit": _unit(parameter),
    }


def compute_supplementary_views(
    df: pd.DataFrame,
    parameter: Parameter,
    baseline_df: Any = None,
    value_col: str | None = None,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    region_id: str | None = None,
) -> dict[str, Any]:
    """Run every supplementary view, isolating individual failures."""

    if df.empty:
        return {}
    column = value_col or ("psal_adjusted" if parameter is Parameter.SALINITY else "temp_adjusted")
    results: dict[str, Any] = {}
    attempts: list[tuple[str, Any]] = [
        ("ts_diagram", lambda: compute_ts_diagram(df)),
        ("density_profile", lambda: compute_density_profile(df)),
        ("heat_content", lambda: compute_heat_content(df, column)),
        ("hovmoller", lambda: compute_hovmoller(df, column, parameter)),
        ("seasonal_cycle", lambda: compute_seasonal_cycle(df, column, parameter)),
        ("year_over_year", lambda: compute_year_over_year(df, column, parameter)),
        (
            "anomaly_trend",
            lambda: compute_anomaly_trend(
                df,
                column,
                parameter,
                baseline_df,
                latitude=latitude,
                longitude=longitude,
                region_id=region_id,
            ),
        ),
    ]
    for name, builder in attempts:
        try:
            result = builder()
        except Exception:
            result = None
        if result is not None:
            results[name] = result
    return results
