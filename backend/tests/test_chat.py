import asyncio
import json
from pathlib import Path

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient, Response

import app.api.chat as chat_module
from app.config import EvidenceGradeThresholds, Settings
from app.main import app


@pytest.fixture(autouse=True)
def disable_optional_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLOATCHAT_LLM_API_KEY", raising=False)


async def post_chat(query: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/chat", json={"query": query})


def settings(data_dir: Path) -> Settings:
    return Settings(
        environment="test",
        data_dir=data_dir,
        static_dir=data_dir / "static",
        llm_timeout=0.01,
        default_radius_km=100,
        grade_thresholds=EvidenceGradeThresholds(),
        cors_origins=("http://test",),
    )


def write_query_ready_fixture(data_dir: Path) -> None:
    processed = data_dir / "processed"
    production = data_dir / "baselines" / "production"
    processed.mkdir(parents=True)
    production.mkdir(parents=True)
    rows = []
    for profile_index in range(6):
        platform = str(1 + profile_index % 2)
        for row_index, (pressure, temperature) in enumerate(((5.0, 30.0), (50.0, 28.0))):
            rows.append(
                {
                    "platform_number": platform,
                    "cycle_number": str(profile_index),
                    "profile_id": f"{platform}:{profile_index}",
                    "time": pd.Timestamp(f"2024-07-{profile_index + 1:02d}", tz="UTC"),
                    "latitude": 19.0,
                    "longitude": 72.8,
                    "pres": pressure,
                    "temp": temperature,
                    "temp_qc": "1",
                    "temp_adjusted": temperature + profile_index / 10,
                    "temp_adjusted_qc": "1",
                    "psal": 35.0,
                    "psal_qc": "1",
                    "psal_adjusted": 35.0,
                    "psal_adjusted_qc": "1",
                    "data_mode": "D",
                    "position_qc": "1",
                    "calendar_month": 7,
                    "year": 2024,
                    "_source_file": "fixture.csv",
                    "source_row": profile_index * 2 + row_index + 3,
                }
            )
    pd.DataFrame(rows).to_parquet(processed / "argo_profiles.parquet", index=False)
    pd.DataFrame(
        [
            {
                "baseline_type": "production",
                "policy_version": "fixture",
                "parameter": "temperature",
                "selection_type": "grid",
                "selection_id": "grid-18-72",
                "grid_lat": 18.0,
                "grid_lon": 72.0,
                "calendar_month": 7,
                "mean": 27.0,
                "std": 1.0,
                "n": 50,
                "distinct_float_count": 5,
                "year_min": 2015,
                "year_max": 2023,
            }
        ]
    ).to_parquet(production / "baseline.parquet", index=False)
    (data_dir / "manifest.json").write_text(
        json.dumps(
            {
                "status": "ready",
                "dataset_version": "fixture-v1",
                "coverage": {},
                "evidence_grade_policy": {
                    "reviewed": True,
                    "insufficient_valid_profile_threshold": 5,
                    "baseline_min_n": 10,
                    "min_distinct_floats": 2,
                    "min_qc_pass_rate": 0.3,
                    "coverage_rule": "reviewed test fixture",
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


def test_unsupported_query_returns_typed_parse_error() -> None:
    response = asyncio.run(post_chat("Will it rain tomorrow?"))

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "parse_error"


def test_supported_query_does_not_invent_data_when_dataset_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Show temperature profile near Mumbai in July 2024"))

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "general_error"
    assert "traceback" not in response.text.lower()
    assert str(tmp_path) not in response.text


def test_success_response_contains_complete_trust_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Show temperature profile near Mumbai in July 2024"))

    assert response.status_code == 200
    body = response.json()
    assert body["query_type"] == "profile"
    assert body["evidence_grade"] == "Supported"
    assert body["parser_used"] == "rule_based"
    assert body["evidence_panel"]["raw_observation_count"] == 12
    assert body["evidence_panel"]["valid_profile_count"] == 6
    assert body["evidence_panel"]["distinct_float_count"] == 2
    assert body["data"]["bins"]
    assert body["data"]["bins"][0]["trace"]["profile_ids"]
    assert body["evidence_panel"]["source_record_sample"]
    assert body["anomaly"] is not None
    assert set(body["secondary_views"]) == {"time_series", "regional_average"}
    assert {"ts_diagram", "density_profile", "seasonal_cycle", "hovmoller"} <= set(
        body["supplementary_data"]
    )
    assert body["params"]["location"]["coordinate_precision"] == 2
    assert "traceback" not in response.text.lower()


def test_anomaly_uses_qc_passed_aggregate_and_production_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Is temperature near Mumbai unusual in July 2024?"))

    assert response.status_code == 200
    body = response.json()
    assert body["anomaly"] is not None
    assert body["anomaly"]["baseline_n"] == 50
    assert "marine heatwave" not in response.text.lower()


def test_multi_parameter_query_runs_independent_pipelines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(
        post_chat("Compare temperature and salinity profiles near Mumbai in July 2024")
    )

    assert response.status_code == 200
    body = response.json()
    assert body["params"]["parameter"] == "all"
    assert set(body["results_by_parameter"]) == {"temperature", "salinity"}
    assert body["results_by_parameter"]["temperature"]["data"]["bins"]
    assert body["results_by_parameter"]["salinity"]["data"]["bins"]


def test_paired_scientific_views_require_both_parameter_qc_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    artifact = tmp_path / "processed" / "argo_profiles.parquet"
    rows = pd.read_parquet(artifact)
    rows.loc[rows.index[0], "psal_adjusted_qc"] = "4"
    rows.to_parquet(artifact, index=False)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Show temperature profile near Mumbai in July 2024"))

    assert response.status_code == 200
    points = response.json()["supplementary_data"]["ts_diagram"]["points"]
    assert len(points) == len(rows) - 1


def test_no_matching_location_returns_no_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Temperature profile near Chennai in July 2024"))

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "no_data"
