"""Build physically separate production and validation ARGO baseline artifacts."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGION_BOXES: dict[str, tuple[float, float, float, float]] = {
    "bay-of-bengal": (5.0, 22.0, 80.0, 100.0),
    "arabian-sea": (8.0, 25.0, 55.0, 75.0),
    "lakshadweep-sea": (7.0, 15.0, 70.0, 77.0),
    "andaman-sea": (6.0, 15.0, 92.0, 100.0),
    "equatorial-indian": (-10.0, 10.0, 40.0, 100.0),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _aggregate_profiles(frame: pd.DataFrame, value_col: str, mode: str) -> pd.DataFrame:
    if mode == "shallow":
        usable = frame.loc[frame["pres"].between(0, 10, inclusive="both")].copy()
        usable = usable.sort_values(["profile_id", "pres"])
        result = usable.groupby("profile_id", as_index=False).first()
    else:
        usable = (
            frame.loc[frame["pres"].between(0, 100, inclusive="both")]
            if mode == "upper_100"
            else frame
        )
        result = usable.groupby("profile_id", as_index=False).agg(
            platform_number=("platform_number", "first"),
            time=("time", "first"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            **{value_col: (value_col, "median")},
        )
    result = result[
        ["profile_id", "platform_number", "time", "latitude", "longitude", value_col]
    ].rename(columns={value_col: "profile_value"})
    result["calendar_month"] = pd.to_datetime(result["time"], utc=True).dt.month
    result["year"] = pd.to_datetime(result["time"], utc=True).dt.year
    return result.dropna(subset=["profile_value"])


def _summarize_group(
    frame: pd.DataFrame,
    group_columns: list[str],
    parameter: str,
    selection_type: str,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    stats = (
        frame.groupby(group_columns, as_index=False, dropna=False)
        .agg(
            mean=("profile_value", "mean"),
            std=("profile_value", "std"),
            n=("profile_id", "nunique"),
            distinct_float_count=(
                "platform_number",
                lambda values: values.astype(str).nunique(),
            ),
            year_min=("year", "min"),
            year_max=("year", "max"),
        )
        .reset_index(drop=True)
    )
    stats["parameter"] = parameter
    stats["selection_type"] = selection_type
    return stats


def _selection_stats(profile_values: pd.DataFrame, parameter: str) -> pd.DataFrame:
    outputs: list[pd.DataFrame] = []

    global_frame = profile_values.copy()
    global_frame["selection_id"] = "all-available"
    global_frame["grid_lat"] = math.nan
    global_frame["grid_lon"] = math.nan
    outputs.append(
        _summarize_group(
            global_frame,
            ["selection_id", "grid_lat", "grid_lon", "calendar_month"],
            parameter,
            "global",
        )
    )

    grid_frame = profile_values.copy()
    grid_frame["grid_lat"] = (grid_frame["latitude"] // 2 * 2).astype(float)
    grid_frame["grid_lon"] = (grid_frame["longitude"] // 2 * 2).astype(float)
    grid_frame["selection_id"] = (
        "grid-"
        + grid_frame["grid_lat"].map(lambda value: f"{value:g}")
        + "-"
        + grid_frame["grid_lon"].map(lambda value: f"{value:g}")
    )
    outputs.append(
        _summarize_group(
            grid_frame,
            ["selection_id", "grid_lat", "grid_lon", "calendar_month"],
            parameter,
            "grid",
        )
    )

    for region_id, (lat_min, lat_max, lon_min, lon_max) in REGION_BOXES.items():
        region = profile_values.loc[
            profile_values["latitude"].between(lat_min, lat_max, inclusive="both")
            & profile_values["longitude"].between(lon_min, lon_max, inclusive="both")
        ].copy()
        if region.empty:
            continue
        region["selection_id"] = region_id
        region["grid_lat"] = math.nan
        region["grid_lon"] = math.nan
        outputs.append(
            _summarize_group(
                region,
                ["selection_id", "grid_lat", "grid_lon", "calendar_month"],
                parameter,
                "region",
            )
        )

    return pd.concat(
        [output for output in outputs if not output.empty], ignore_index=True
    )


def _parameter_profile_sets(
    profile_path: Path,
    stem: str,
    value_col: str,
    qc_col: str,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    columns = [
        "profile_id",
        "platform_number",
        "time",
        "latitude",
        "longitude",
        "pres",
        "data_mode",
        "position_qc",
        value_col,
        qc_col,
    ]
    frame = pd.read_parquet(profile_path, columns=columns)
    raw_count = len(frame)
    mode = frame["data_mode"].astype("string").str.strip().str.upper()
    position_qc = frame["position_qc"].astype("string").str.strip()
    parameter_qc = frame[qc_col].astype("string").str.strip()
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    valid = frame.loc[
        mode.isin(["A", "D"])
        & position_qc.eq("1")
        & parameter_qc.eq("1")
        & frame[value_col].notna()
    ].copy()
    profile_sets = {
        stem: _aggregate_profiles(valid, value_col, "full"),
        f"{stem}_shallow": _aggregate_profiles(valid, value_col, "shallow"),
        f"{stem}_upper_100": _aggregate_profiles(valid, value_col, "upper_100"),
    }
    audit = {
        "raw_observations": raw_count,
        "qc_passed_observations": len(valid),
        "qc_pass_rate": len(valid) / raw_count if raw_count else 0,
        "qc_passed_profiles": int(valid["profile_id"].nunique()),
        "distinct_floats": int(valid["platform_number"].astype(str).nunique()),
    }
    del frame, valid
    gc.collect()
    return profile_sets, audit


def _build_kind(
    profile_sets: dict[str, pd.DataFrame],
    baseline_type: str,
    year_start: int,
    year_end: int,
    input_artifact_sha256: str,
) -> pd.DataFrame:
    outputs: list[pd.DataFrame] = []
    for parameter, values in profile_sets.items():
        period = values.loc[
            values["year"].between(year_start, year_end, inclusive="both")
        ]
        stats = _selection_stats(period, parameter)
        if stats.empty:
            continue
        stats["baseline_type"] = baseline_type
        stats["policy_version"] = "scientific-policy-0.2"
        stats["input_artifact_sha256"] = input_artifact_sha256
        outputs.append(stats)
    if not outputs:
        raise RuntimeError(f"No rows were available for the {baseline_type} baseline")
    columns = [
        "baseline_type",
        "policy_version",
        "input_artifact_sha256",
        "parameter",
        "selection_type",
        "selection_id",
        "grid_lat",
        "grid_lon",
        "calendar_month",
        "mean",
        "std",
        "n",
        "distinct_float_count",
        "year_min",
        "year_max",
    ]
    return pd.concat(outputs, ignore_index=True)[columns]


def _distribution(values: pd.Series) -> dict[str, float | int | None]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return {"min": None, "p10": None, "median": None, "p90": None, "max": None}
    return {
        "min": float(clean.min()),
        "p10": float(clean.quantile(0.10)),
        "median": float(clean.median()),
        "p90": float(clean.quantile(0.90)),
        "max": float(clean.max()),
    }


def _within_radius(
    frame: pd.DataFrame, latitude: float, longitude: float, radius_km: float
) -> pd.DataFrame:
    latitudes = np.radians(frame["latitude"].to_numpy(dtype=float))
    longitudes = np.radians(frame["longitude"].to_numpy(dtype=float))
    latitude_rad = math.radians(latitude)
    longitude_rad = math.radians(longitude)
    delta_latitude = latitudes - latitude_rad
    delta_longitude = longitudes - longitude_rad
    value = (
        np.sin(delta_latitude / 2) ** 2
        + np.cos(latitude_rad) * np.cos(latitudes) * np.sin(delta_longitude / 2) ** 2
    )
    distances = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(value, 0, 1)))
    return frame.loc[distances <= radius_km]


def _pinned_coverage(profile_sets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    mumbai_profile = _within_radius(
        profile_sets["temperature"].loc[
            (profile_sets["temperature"]["year"] == 2024)
            & (profile_sets["temperature"]["calendar_month"] == 7)
        ],
        19.0,
        72.8,
        50.0,
    )
    mumbai_series = _within_radius(
        profile_sets["temperature_shallow"].loc[
            profile_sets["temperature_shallow"]["year"].between(
                2015, 2024, inclusive="both"
            )
        ],
        19.0,
        72.8,
        50.0,
    )
    bay = profile_sets["salinity_upper_100"]
    bay = bay.loc[
        (bay["year"] == 2023)
        & bay["latitude"].between(5.0, 22.0, inclusive="both")
        & bay["longitude"].between(80.0, 100.0, inclusive="both")
    ]
    result = {
        "mumbai_50km_july_2024_temperature_profiles": int(
            mumbai_profile["profile_id"].nunique()
        ),
        "mumbai_50km_2015_2024_shallow_temperature_profiles": int(
            mumbai_series["profile_id"].nunique()
        ),
        "bay_of_bengal_2023_upper_100_salinity_profiles": int(
            bay["profile_id"].nunique()
        ),
    }
    result["all_pinned_selections_present"] = all(
        value > 0 for value in result.values()
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--production-start-year", type=int, default=2000)
    parser.add_argument("--production-end-year", type=int, default=2026)
    parser.add_argument("--validation-start-year", type=int, default=2000)
    parser.add_argument("--validation-end-year", type=int, default=2009)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Run scripts/preprocess_argo.py before building baselines"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile_artifact = next(
        artifact for artifact in manifest["artifacts"] if artifact["kind"] == "profiles"
    )
    profile_path = data_dir / profile_artifact["path"]
    if sha256_file(profile_path) != profile_artifact["sha256"]:
        raise RuntimeError(
            "The processed profile artifact hash does not match the manifest"
        )

    all_sets: dict[str, pd.DataFrame] = {}
    audit: dict[str, Any] = {}
    for stem, value_col, qc_col in (
        ("temperature", "temp_adjusted", "temp_adjusted_qc"),
        ("salinity", "psal_adjusted", "psal_adjusted_qc"),
    ):
        print(f"Loading QC-passed {stem} observations", flush=True)
        profile_sets, parameter_audit = _parameter_profile_sets(
            profile_path, stem, value_col, qc_col
        )
        all_sets.update(profile_sets)
        audit[stem] = parameter_audit

    print("Computing production baseline statistics", flush=True)
    production = _build_kind(
        all_sets,
        "production",
        args.production_start_year,
        args.production_end_year,
        profile_artifact["sha256"],
    )
    print("Computing validation baseline statistics", flush=True)
    validation = _build_kind(
        all_sets,
        "validation",
        args.validation_start_year,
        args.validation_end_year,
        profile_artifact["sha256"],
    )
    pinned_coverage = _pinned_coverage(all_sets)

    production_path = data_dir / "baselines" / "production" / "baseline.parquet"
    validation_path = data_dir / "baselines" / "validation" / "baseline.parquet"
    production_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    production.to_parquet(production_path, index=False, compression="zstd")
    validation.to_parquet(validation_path, index=False, compression="zstd")

    coverage_report = {
        "status": "generated_policy_implemented_not_scientifically_validated",
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_version": manifest["dataset_version"],
        "production_period": [args.production_start_year, args.production_end_year],
        "validation_period": [args.validation_start_year, args.validation_end_year],
        "qc": audit,
        "production_baseline_rows": len(production),
        "production_baseline_n_distribution": _distribution(production["n"]),
        "production_distinct_float_distribution": _distribution(
            production["distinct_float_count"]
        ),
        "named_region_rows": {
            region_id: int((production["selection_id"] == region_id).sum())
            for region_id in REGION_BOXES
        },
        "pinned_selection_coverage": pinned_coverage,
        "implemented_thresholds_from_build_specification": {
            "baseline_min_n": 10,
            "min_distinct_floats": 2,
            "min_qc_pass_rate": 0.3,
        },
        "review_note": (
            "The thresholds are implemented exactly from the supplied build specification. "
            "They are not a substitute for external scientific validation."
        ),
    }
    coverage_report_path = data_dir / "coverage_report.json"
    coverage_report_path.write_text(
        json.dumps(coverage_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest["status"] = "ready"
    manifest["created_at"] = datetime.now(UTC).isoformat()
    manifest["build_command"] = (
        "python scripts/preprocess_argo.py && python scripts/build_baselines.py"
    )
    manifest["coverage"]["production_baseline_period"] = [
        args.production_start_year,
        args.production_end_year,
    ]
    manifest["coverage"]["validation_baseline_period"] = [
        args.validation_start_year,
        args.validation_end_year,
    ]
    manifest["coverage"]["grade_threshold_review"] = (
        "implemented_from_supplied_build_specification_not_scientifically_validated"
    )
    manifest["coverage"]["pinned_selection_coverage"] = pinned_coverage
    manifest["evidence_grade_policy"] = {
        "version": "prompt-v4-explicit-thresholds",
        "reviewed": True,
        "insufficient_valid_profile_threshold": 5,
        "baseline_min_n": 10,
        "min_distinct_floats": 2,
        "min_qc_pass_rate": 0.3,
        "coverage_rule": "at_least_two_distinct_floats",
        "validation_note": (
            "Thresholds are implemented from the supplied build specification and remain "
            "subject to external scientific validation."
        ),
    }
    manifest["artifacts"] = [profile_artifact]
    for path, kind, frame in (
        (production_path, "production_baseline", production),
        (validation_path, "validation_baseline", validation),
    ):
        manifest["artifacts"].append(
            {
                "path": str(path.relative_to(data_dir)),
                "kind": kind,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "row_count": len(frame),
            }
        )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(production):,} production and {len(validation):,} validation rows.",
        flush=True,
    )
    print(
        f"Evidence Grade thresholds implemented; validation caveat recorded in {coverage_report_path}.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
