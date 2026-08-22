from __future__ import annotations

import json
import math
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from app.config import EvidenceGradeThresholds
from app.models import Parameter, QueryParams


class DataUnavailable(RuntimeError):
    """Raised when validated query-ready artifacts cannot be loaded."""


class NoDataFound(LookupError):
    """Raised when valid retrieval criteria match no local observations."""


REQUIRED_PROFILE_COLUMNS = {
    "platform_number",
    "cycle_number",
    "profile_id",
    "time",
    "latitude",
    "longitude",
    "pres",
    "data_mode",
    "position_qc",
    "temp_adjusted",
    "temp_adjusted_qc",
    "psal_adjusted",
    "psal_adjusted_qc",
}

IDENTITY_COLUMNS = [
    "platform_number",
    "cycle_number",
    "profile_id",
    "time",
    "latitude",
    "longitude",
    "pres",
    "data_mode",
    "position_qc",
    "calendar_month",
    "year",
    "_source_file",
    "source_row",
]

PARAMETER_COLUMNS = {
    Parameter.TEMPERATURE.value: ["temp", "temp_qc", "temp_adjusted", "temp_adjusted_qc"],
    Parameter.SHALLOW_SST_PROXY.value: [
        "temp",
        "temp_qc",
        "temp_adjusted",
        "temp_adjusted_qc",
    ],
    Parameter.SALINITY.value: ["psal", "psal_qc", "psal_adjusted", "psal_adjusted_qc"],
    "all": [
        "temp",
        "temp_qc",
        "temp_adjusted",
        "temp_adjusted_qc",
        "psal",
        "psal_qc",
        "psal_adjusted",
        "psal_adjusted_qc",
    ],
}


def haversine_km(
    lat1: float,
    lon1: float,
    lat2_arr: np.ndarray | pd.Series,
    lon2_arr: np.ndarray | pd.Series,
) -> np.ndarray:
    """Return vectorized great-circle distances using IUGG's mean Earth radius."""

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(np.asarray(lat2_arr, dtype=float))
    lon2_rad = np.radians(np.asarray(lon2_arr, dtype=float))
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad
    a = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _safe_artifact_path(data_dir: Path, relative_path: str) -> Path:
    target = (data_dir / relative_path).resolve()
    try:
        target.relative_to(data_dir.resolve())
    except ValueError as exc:
        raise DataUnavailable("The data manifest contains an unsafe artifact path.") from exc
    return target


class DataRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir.resolve()
        self.manifest_path = self.data_dir / "manifest.json"
        self._manifest: dict[str, Any] | None = None
        self._dataset: ds.Dataset | None = None

    def _read_manifest(self) -> dict[str, Any]:
        if self._manifest is not None:
            return self._manifest
        if not self.manifest_path.is_file():
            raise DataUnavailable("The data manifest is missing.")
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DataUnavailable("The data manifest is unreadable.") from exc
        if not isinstance(manifest, dict):
            raise DataUnavailable("The data manifest has an invalid structure.")
        self._manifest = manifest
        return manifest

    def _artifact_path(self, kind: str) -> Path:
        manifest = self._read_manifest()
        for artifact in manifest.get("artifacts", []):
            if artifact.get("kind") == kind and artifact.get("path"):
                return _safe_artifact_path(self.data_dir, str(artifact["path"]))
        raise DataUnavailable(f"The data manifest has no {kind.replace('_', ' ')} artifact.")

    @property
    def profile_path(self) -> Path:
        return self._artifact_path("profiles")

    def _load(self) -> ds.Dataset:
        if self._dataset is not None:
            return self._dataset
        profile_path = self.profile_path
        if not profile_path.is_file():
            raise DataUnavailable("The query-ready profile artifact is missing.")
        try:
            dataset = ds.dataset(profile_path, format="parquet")
        except (OSError, ValueError) as exc:
            raise DataUnavailable("The query-ready profile artifact is unreadable.") from exc
        missing = REQUIRED_PROFILE_COLUMNS - set(dataset.schema.names)
        if missing:
            raise DataUnavailable("The query-ready profile artifact is missing required columns.")
        self._dataset = dataset
        return dataset

    def readiness(self) -> tuple[bool, str]:
        try:
            manifest = self._read_manifest()
            if manifest.get("status") != "ready":
                return False, "data manifest is not marked ready"
            artifacts = manifest.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                return False, "data manifest has no artifacts"
            for artifact in artifacts:
                relative_path = artifact.get("path")
                if (
                    not relative_path
                    or not _safe_artifact_path(self.data_dir, str(relative_path)).is_file()
                ):
                    return False, "a declared data artifact is missing"
            self._load()
            production_path = self._artifact_path("production_baseline")
            if not production_path.is_file():
                return False, "the production baseline is missing"
        except DataUnavailable as exc:
            return False, str(exc)
        return True, "query-ready profiles and production baseline are present"

    def get_data_coverage(self) -> dict[str, Any]:
        try:
            coverage = self._read_manifest().get("coverage", {})
        except DataUnavailable:
            return {}
        return coverage if isinstance(coverage, dict) else {}

    def get_manifest_version(self) -> str:
        return str(self._read_manifest().get("dataset_version", "unversioned"))

    def get_source_name(self) -> str:
        source = self._read_manifest().get("source", {})
        return str(source.get("name", "ARGO observations"))

    def get_profile_artifact_info(self) -> tuple[str | None, str | None]:
        for artifact in self._read_manifest().get("artifacts", []):
            if artifact.get("kind") == "profiles":
                return (
                    str(artifact.get("path")) if artifact.get("path") else None,
                    str(artifact.get("sha256")) if artifact.get("sha256") else None,
                )
        return None, None

    def get_grade_thresholds(self) -> EvidenceGradeThresholds:
        policy = self._read_manifest().get("evidence_grade_policy", {})
        reviewed = bool(policy.get("reviewed", False))
        return EvidenceGradeThresholds(
            min_valid_profiles=int(policy.get("insufficient_valid_profile_threshold", 5)),
            min_baseline_n=(
                int(policy["baseline_min_n"]) if policy.get("baseline_min_n") is not None else None
            ),
            min_distinct_floats=(
                int(policy["min_distinct_floats"])
                if policy.get("min_distinct_floats") is not None
                else None
            ),
            min_qc_pass_rate=(
                float(policy["min_qc_pass_rate"])
                if policy.get("min_qc_pass_rate") is not None
                else None
            ),
            coverage_rule=policy.get("coverage_rule"),
            reviewed=reviewed,
        )

    @staticmethod
    def _date_bounds(date_from: str, date_to: str) -> tuple[datetime, datetime]:
        try:
            start_date = date.fromisoformat(date_from)
            end_date = date.fromisoformat(date_to)
        except ValueError as exc:
            raise NoDataFound("The requested date range is invalid.") from exc
        start = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_exclusive = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        return start, end_exclusive

    def _columns_for(self, parameter: Parameter | str) -> list[str]:
        value = parameter.value if isinstance(parameter, Parameter) else str(parameter)
        requested = IDENTITY_COLUMNS + PARAMETER_COLUMNS.get(value, PARAMETER_COLUMNS["all"])
        available = set(self._load().schema.names)
        return [column for column in requested if column in available]

    def _scan(self, expression: ds.Expression, parameter: Parameter | str) -> pd.DataFrame:
        try:
            table = self._load().to_table(columns=self._columns_for(parameter), filter=expression)
        except (OSError, ValueError, TypeError) as exc:
            raise DataUnavailable("The profile artifact could not be queried safely.") from exc
        frame = table.to_pandas()
        if "time" in frame:
            frame["time"] = pd.to_datetime(frame["time"], utc=True, errors="coerce")
        return frame

    def get_records(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        date_from: str,
        date_to: str,
        parameter: Parameter | str,
    ) -> pd.DataFrame:
        start, end_exclusive = self._date_bounds(date_from, date_to)
        lat_delta = radius_km / 110.574
        lon_delta = radius_km / (111.320 * max(abs(math.cos(math.radians(lat))), 0.2))
        expression = (
            (ds.field("time") >= start)
            & (ds.field("time") < end_exclusive)
            & (ds.field("latitude") >= lat - lat_delta)
            & (ds.field("latitude") <= lat + lat_delta)
            & (ds.field("longitude") >= lon - lon_delta)
            & (ds.field("longitude") <= lon + lon_delta)
        )
        frame = self._scan(expression, parameter)
        if frame.empty:
            return frame
        distances = haversine_km(lat, lon, frame["latitude"], frame["longitude"])
        frame = frame.loc[distances <= radius_km].copy()
        frame["distance_km"] = distances[distances <= radius_km]
        return frame.reset_index(drop=True)

    def get_region_records(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        date_from: str,
        date_to: str,
        parameter: Parameter | str,
    ) -> pd.DataFrame:
        start, end_exclusive = self._date_bounds(date_from, date_to)
        expression = (
            (ds.field("time") >= start)
            & (ds.field("time") < end_exclusive)
            & (ds.field("latitude") >= lat_min)
            & (ds.field("latitude") <= lat_max)
            & (ds.field("longitude") >= lon_min)
            & (ds.field("longitude") <= lon_max)
        )
        return self._scan(expression, parameter).reset_index(drop=True)

    def query(self, params: QueryParams) -> pd.DataFrame:
        """Compatibility entry point used by scripts and older callers."""

        if not params.date_from or not params.date_to:
            raise DataUnavailable("The parsed query has no validated date range.")
        if params.location.latitude is None or params.location.longitude is None:
            raise DataUnavailable("The parsed query has no validated coordinates.")
        return self.get_records(
            params.location.latitude,
            params.location.longitude,
            params.location.radius_km,
            params.date_from,
            params.date_to,
            params.parameter,
        )
