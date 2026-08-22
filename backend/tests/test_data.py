import json
from pathlib import Path

import pandas as pd
import pytest

from app.models import Parameter
from app.services.data import DataRepository, haversine_km


def write_dataset(data_dir: Path) -> None:
    processed = data_dir / "processed"
    production = data_dir / "baselines" / "production"
    processed.mkdir(parents=True)
    production.mkdir(parents=True)
    frame = pd.DataFrame(
        [
            {
                "platform_number": "1",
                "cycle_number": "1",
                "profile_id": "1:1",
                "time": pd.Timestamp("2024-07-10", tz="UTC"),
                "latitude": 19.0,
                "longitude": 72.8,
                "pres": 5.0,
                "data_mode": "D",
                "position_qc": "1",
                "temp": 28.0,
                "temp_qc": "1",
                "temp_adjusted": 28.1,
                "temp_adjusted_qc": "1",
                "psal": 35.0,
                "psal_qc": "1",
                "psal_adjusted": 35.1,
                "psal_adjusted_qc": "1",
                "calendar_month": 7,
                "year": 2024,
                "_source_file": "fixture.csv",
                "source_row": 3,
            },
            {
                "platform_number": "2",
                "cycle_number": "1",
                "profile_id": "2:1",
                "time": pd.Timestamp("2024-07-10", tz="UTC"),
                "latitude": 10.0,
                "longitude": 60.0,
                "pres": 5.0,
                "data_mode": "D",
                "position_qc": "1",
                "temp": 25.0,
                "temp_qc": "1",
                "temp_adjusted": 25.1,
                "temp_adjusted_qc": "1",
                "psal": 36.0,
                "psal_qc": "1",
                "psal_adjusted": 36.1,
                "psal_adjusted_qc": "1",
                "calendar_month": 7,
                "year": 2024,
                "_source_file": "fixture.csv",
                "source_row": 4,
            },
        ]
    )
    frame.to_parquet(processed / "argo_profiles.parquet", index=False)
    pd.DataFrame([{"baseline_type": "production"}]).to_parquet(
        production / "baseline.parquet", index=False
    )
    (data_dir / "manifest.json").write_text(
        json.dumps(
            {
                "status": "ready",
                "dataset_version": "fixture-v1",
                "coverage": {"date_min": "2024-07-10"},
                "evidence_grade_policy": {
                    "reviewed": False,
                    "insufficient_valid_profile_threshold": 5,
                    "baseline_min_n": None,
                    "min_distinct_floats": None,
                    "min_qc_pass_rate": None,
                    "coverage_rule": None,
                },
                "artifacts": [
                    {"kind": "profiles", "path": "processed/argo_profiles.parquet"},
                    {
                        "kind": "production_baseline",
                        "path": "baselines/production/baseline.parquet",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_haversine_zero_and_known_distance() -> None:
    distances = haversine_km(0, 0, pd.Series([0, 1]), pd.Series([0, 0]))

    assert distances[0] == 0
    assert distances[1] == pytest.approx(111.195, rel=1e-3)


def test_repository_filters_space_time_and_parameter(tmp_path: Path) -> None:
    write_dataset(tmp_path)
    repository = DataRepository(tmp_path)

    records = repository.get_records(
        19.0,
        72.8,
        50,
        "2024-07-01",
        "2024-07-31",
        Parameter.TEMPERATURE,
    )

    assert records["profile_id"].tolist() == ["1:1"]
    assert "temp_adjusted" in records
    assert "psal_adjusted" not in records
    assert records["distance_km"].iloc[0] == pytest.approx(0)


def test_readiness_checks_profile_schema_and_production_baseline(tmp_path: Path) -> None:
    write_dataset(tmp_path)

    assert DataRepository(tmp_path).readiness()[0] is True
