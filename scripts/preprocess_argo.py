"""Build an auditable query-ready Parquet file from local INCOIS ARGO CSV exports."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = [
    "platform_number",
    "cycle_number",
    "time",
    "latitude",
    "longitude",
    "pres",
    "temp",
    "temp_qc",
    "temp_adjusted",
    "temp_adjusted_qc",
    "psal",
    "psal_qc",
    "psal_adjusted",
    "psal_adjusted_qc",
    "data_mode",
    "position_qc",
]
STRING_COLUMNS = [
    "platform_number",
    "cycle_number",
    "temp_qc",
    "temp_adjusted_qc",
    "psal_qc",
    "psal_adjusted_qc",
    "data_mode",
    "position_qc",
]
NUMERIC_COLUMNS = [
    "latitude",
    "longitude",
    "pres",
    "temp",
    "temp_adjusted",
    "psal",
    "psal_adjusted",
]
DTYPES = {column: "string" for column in STRING_COLUMNS}
MODE_PRIORITY = {"D": 0, "A": 1, "R": 2}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_header(path: Path) -> None:
    header = pd.read_csv(path, nrows=0).columns.tolist()
    if header != EXPECTED_COLUMNS:
        raise ValueError(
            f"{path.name}: CSV columns do not match the frozen 16-column schema"
        )
    units = (
        pd.read_csv(path, header=None, skiprows=1, nrows=1).iloc[0].astype(str).tolist()
    )
    if len(units) != len(EXPECTED_COLUMNS) or units[2] != "UTC":
        raise ValueError(f"{path.name}: the required units row is missing or malformed")


def normalize_chunk(chunk: pd.DataFrame, source_name: str) -> pd.DataFrame:
    chunk = chunk.loc[chunk["platform_number"].astype(str) != "platform_number"].copy()
    for column in STRING_COLUMNS:
        chunk[column] = chunk[column].astype("string").str.strip()
    for column in NUMERIC_COLUMNS:
        chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
    chunk["time"] = pd.to_datetime(chunk["time"], utc=True, errors="coerce")
    chunk["longitude"] = ((chunk["longitude"] + 180) % 360) - 180
    chunk = chunk.dropna(
        subset=[
            "platform_number",
            "cycle_number",
            "time",
            "latitude",
            "longitude",
            "pres",
            "data_mode",
            "position_qc",
        ]
    )
    chunk["profile_id"] = (
        chunk["platform_number"].astype(str) + ":" + chunk["cycle_number"].astype(str)
    )
    chunk["_mode_priority"] = (
        chunk["data_mode"].map(MODE_PRIORITY).fillna(99).astype("int8")
    )
    chunk = chunk.sort_values(
        ["profile_id", "pres", "_mode_priority", "source_row"], kind="stable"
    ).drop_duplicates(["profile_id", "pres"], keep="first")
    chunk = chunk.drop(columns="_mode_priority")
    chunk["calendar_month"] = chunk["time"].dt.month.astype("int8")
    chunk["year"] = chunk["time"].dt.year.astype("int16")
    chunk["_source_file"] = source_name
    return chunk[
        EXPECTED_COLUMNS
        + ["profile_id", "calendar_month", "year", "_source_file", "source_row"]
    ].reset_index(drop=True)


def update_coverage(coverage: dict[str, Any], frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    coverage["processed_rows"] += len(frame)
    for column in ("latitude", "longitude"):
        minimum = float(frame[column].min())
        maximum = float(frame[column].max())
        coverage[f"{column}_min"] = (
            minimum
            if coverage[f"{column}_min"] is None
            else min(coverage[f"{column}_min"], minimum)
        )
        coverage[f"{column}_max"] = (
            maximum
            if coverage[f"{column}_max"] is None
            else max(coverage[f"{column}_max"], maximum)
        )
    time_min = frame["time"].min()
    time_max = frame["time"].max()
    coverage["date_min"] = (
        time_min
        if coverage["date_min"] is None
        else min(coverage["date_min"], time_min)
    )
    coverage["date_max"] = (
        time_max
        if coverage["date_max"] is None
        else max(coverage["date_max"], time_max)
    )


def build_profiles(
    raw_dir: Path,
    output_path: Path,
    chunk_size: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_paths = sorted(raw_dir.glob("ArgoFloats_*.csv"))
    if not source_paths:
        raise FileNotFoundError(f"No ArgoFloats_*.csv files found under {raw_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".parquet.tmp")
    temporary_path.unlink(missing_ok=True)
    writer: pq.ParquetWriter | None = None
    coverage: dict[str, Any] = {
        "input_rows": 0,
        "processed_rows": 0,
        "date_min": None,
        "date_max": None,
        "latitude_min": None,
        "latitude_max": None,
        "longitude_min": None,
        "longitude_max": None,
    }
    profile_ids: set[str] = set()
    float_ids: set[str] = set()
    source_manifest: list[dict[str, Any]] = []

    try:
        for file_number, path in enumerate(source_paths, start=1):
            print(
                f"[{file_number}/{len(source_paths)}] Validating and hashing {path.name}",
                flush=True,
            )
            validate_header(path)
            file_hash = sha256_file(path)
            file_input_rows = 0
            carry = pd.DataFrame()
            reader = pd.read_csv(
                path,
                header=0,
                skiprows=[1],
                dtype=DTYPES,
                chunksize=chunk_size,
                low_memory=False,
            )
            for chunk_number, chunk in enumerate(reader, start=1):
                chunk["source_row"] = chunk.index.astype("int64") + 3
                file_input_rows += len(chunk)
                coverage["input_rows"] += len(chunk)
                if not carry.empty:
                    chunk = pd.concat([carry, chunk], ignore_index=True)
                    carry = pd.DataFrame()

                raw_profile = (
                    chunk["platform_number"].astype("string").str.strip()
                    + ":"
                    + chunk["cycle_number"].astype("string").str.strip()
                )
                if len(chunk) > 1:
                    last_profile = raw_profile.iloc[-1]
                    carry_mask = raw_profile.eq(last_profile)
                    carry = chunk.loc[carry_mask].copy()
                    chunk = chunk.loc[~carry_mask].copy()

                normalized = normalize_chunk(chunk, path.name)
                if not normalized.empty:
                    update_coverage(coverage, normalized)
                    profile_ids.update(normalized["profile_id"].astype(str).unique())
                    float_ids.update(normalized["platform_number"].astype(str).unique())
                    table = pa.Table.from_pandas(normalized, preserve_index=False)
                    if writer is None:
                        writer = pq.ParquetWriter(
                            temporary_path,
                            table.schema,
                            compression="zstd",
                            use_dictionary=True,
                        )
                    writer.write_table(table, row_group_size=250_000)
                print(
                    f"  chunk {chunk_number}: {file_input_rows:,} input rows processed",
                    flush=True,
                )

            if not carry.empty:
                normalized = normalize_chunk(carry, path.name)
                update_coverage(coverage, normalized)
                profile_ids.update(normalized["profile_id"].astype(str).unique())
                float_ids.update(normalized["platform_number"].astype(str).unique())
                table = pa.Table.from_pandas(normalized, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(
                        temporary_path,
                        table.schema,
                        compression="zstd",
                        use_dictionary=True,
                    )
                writer.write_table(table, row_group_size=250_000)

            source_manifest.append(
                {
                    "name": path.name,
                    "origin": (
                        "Ifremer ARGO ERDDAP"
                        if "ERDDAP" in path.name
                        else "INCOIS ARGO export supplied to project"
                    ),
                    "source_url": (
                        "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.html"
                        if "ERDDAP" in path.name
                        else "https://incois.gov.in/argo/"
                    ),
                    "sha256": file_hash,
                    "size_bytes": path.stat().st_size,
                    "input_rows": file_input_rows,
                }
            )
            print(f"  completed {path.name}: {file_input_rows:,} rows", flush=True)
    finally:
        if writer is not None:
            writer.close()

    if not temporary_path.is_file():
        raise RuntimeError("Preprocessing produced no Parquet artifact")
    temporary_path.replace(output_path)
    coverage["total_profiles"] = len(profile_ids)
    coverage["total_floats"] = len(float_ids)
    coverage["date_min"] = coverage["date_min"].isoformat()
    coverage["date_max"] = coverage["date_max"].isoformat()
    coverage["coverage_note"] = (
        "Coverage describes the installed local exports only. Locations outside these bounds "
        "return no_data; the files are not a complete global Indian Ocean collection."
    )
    return coverage, source_manifest


def write_manifest(
    data_dir: Path,
    output_path: Path,
    dataset_version: str,
    accessed_at: str,
    coverage: dict[str, Any],
    source_files: list[dict[str, Any]],
) -> None:
    manifest = {
        "status": "draft",
        "dataset_version": dataset_version,
        "source": {
            "name": "INCOIS Indian ARGO CSV exports supplied to the project",
            "url": "https://incois.gov.in/argo/",
            "accessed_at": accessed_at,
            "provenance_notes": (
                "Local Arabian Sea exports supplied by the project team. Exact file hashes "
                "and origins are recorded; no provider is contacted at request time."
            ),
            "licence_note": (
                "Redistribution terms were not bundled with the local exports and require "
                "human review before publishing the large source or derived artifacts."
            ),
            "acknowledgement": (
                "These data were collected and made freely available by the International "
                "Argo Program and the national programs that contribute to it."
            ),
            "files": source_files,
        },
        "created_at": datetime.now(UTC).isoformat(),
        "build_command": "python scripts/preprocess_argo.py",
        "qc_policy": {
            "version": "scientific-policy-0.2",
            "accepted_flags": ["1"],
            "adjusted_value_precedence": "A/D modes use adjusted values only; no raw substitution",
            "accepted_data_modes": ["A", "D"],
            "notes": "R-mode records remain auditable but are excluded from scientific aggregates.",
        },
        "evidence_grade_policy": {
            "version": "pending-reviewed-coverage-thresholds",
            "reviewed": False,
            "insufficient_valid_profile_threshold": 5,
            "baseline_min_n": None,
            "min_distinct_floats": None,
            "min_qc_pass_rate": None,
            "coverage_rule": None,
        },
        "coverage": coverage,
        "artifacts": [
            {
                "path": str(output_path.relative_to(data_dir)),
                "kind": "profiles",
                "sha256": sha256_file(output_path),
                "size_bytes": output_path.stat().st_size,
                "row_count": coverage["processed_rows"],
            }
        ],
    }
    (data_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--chunk-size", type=int, default=500_000)
    parser.add_argument("--dataset-version", default="argo-arabian-sea-2026-08-21-v1")
    parser.add_argument("--accessed-at", default="2026-08-21")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    output_path = data_dir / "processed" / "argo_profiles.parquet"
    coverage, source_files = build_profiles(
        data_dir / "raw", output_path, args.chunk_size
    )
    write_manifest(
        data_dir,
        output_path,
        args.dataset_version,
        args.accessed_at,
        coverage,
        source_files,
    )
    print(
        f"Wrote {coverage['processed_rows']:,} rows, {coverage['total_profiles']:,} profiles, "
        f"and {coverage['total_floats']:,} floats to {output_path}",
        flush=True,
    )
    print(
        "Manifest is draft until production and validation baselines are built.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
