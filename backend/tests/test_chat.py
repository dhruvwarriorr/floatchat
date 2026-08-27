import asyncio
import json
from pathlib import Path

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient, Response

import app.api.chat as chat_module
from app.config import EvidenceGradeThresholds, Settings
from app.main import app
from app.services.parser import parse_rule_based


@pytest.fixture(autouse=True)
def disable_optional_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLOATCHAT_LLM_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def disable_live_source_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the live-source fallback off unless a test explicitly enables it.

    Without this, a developer's local .env (e.g. FLOATCHAT_LIVE_SOURCE_ENABLED=true
    for real manual testing) leaks into every no_data test via python-dotenv,
    making them issue real network calls to the public Argovis API and fail
    unpredictably. Tests must never depend on local .env state.
    """
    monkeypatch.delenv("FLOATCHAT_LIVE_SOURCE_ENABLED", raising=False)


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
        default_radius_km=300,
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
    assert response.json()["error"]["understanding"] == (
        "No safe structured Indian Ocean selection could be formed."
    )


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
    assert body["interpreted_title"] == "Temperature profile near Mumbai coast, Jul 2024"
    assert "Mumbai coast (19.00°N, 72.80°E, 300 km radius)" in body["summary"]
    assert "nearest observation is 0 km" in body["summary"]
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
    assert body["data_sufficiency"] == {
        "profile_count": 6,
        "coverage": "Within 300 km",
        "coverage_radius_km": 300.0,
        "requested_radius_km": 300.0,
        "actual_radius_km": 300.0,
        "radius_expanded": False,
        "nearest_observation_km": 0.0,
    }
    assert body["evidence_panel"]["baseline_month_used"] == 7
    assert body["evidence_panel"]["baseline_grid_cell"] == {
        "south": 18.0,
        "west": 72.0,
        "north": 20.0,
        "east": 74.0,
    }
    assert body["evidence_panel"]["depth_bins_used"]
    assert body["evidence_panel"]["aggregation_counts_per_bin"]
    assert body["evidence_panel"]["evidence_checks"]
    assert body["evidence_panel"]["float_positions"]
    assert "traceback" not in response.text.lower()


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("temperature near Mumbai in 2024", "Temperature profile near Mumbai coast, 2024"),
        ("is the Arabian Sea warming?", "Temperature trend across Arabian Sea"),
        ("is the Arabian Sea getting warmer?", "Temperature trend across Arabian Sea"),
        ("salinity near Goa in July 2024", "Salinity profile near Goa coast, Jul 2024"),
        (
            "temperature and salinity near Kochi from 2020 to 2024",
            "Temperature & salinity trend near Kochi coast, 2020–2024",
        ),
    ],
)
def test_interpreted_title_describes_the_accepted_query(query: str, expected: str) -> None:
    assert chat_module._interpreted_title(parse_rule_based(query)) == expected


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


def test_calendar_month_filter_excludes_other_months_before_qc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    artifact = tmp_path / "processed" / "argo_profiles.parquet"
    july = pd.read_parquet(artifact)
    june = july.copy()
    june["profile_id"] = "june:" + june["profile_id"].astype(str)
    june["time"] = pd.to_datetime(june["time"], utc=True).map(
        lambda value: value.replace(year=2023, month=6)
    )
    june["calendar_month"] = 6
    june["year"] = 2023
    pd.concat([june, july], ignore_index=True).to_parquet(artifact, index=False)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Temperature near Mumbai June of last 5 years"))

    assert response.status_code == 200
    body = response.json()
    assert body["params"]["calendar_month"] == 6
    assert body["evidence_panel"]["raw_observation_count"] == len(june)
    assert {point["month"] for point in body["data"]["series"]} == {"2023-06"}


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
    assert response.json()["error"]["understood"]["location_label"] == "Chennai coast"
    assert response.json()["error"]["searched"]
    assert response.json()["error"]["records_found"] == 0
    assert response.json()["error"]["suggested_query"]


def test_no_data_reports_nearest_distance_without_widening_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Temperature profile at 19N 70E within 100 km in July 2024"))

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["nearest_available_km"] == pytest.approx(294.8, abs=1)
    assert "within 100 km" in error["message"]
    assert "within 350 km" in error["suggested_query"]


def test_implicit_point_query_auto_expands_and_discloses_retrieval_distance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    artifact = tmp_path / "processed" / "argo_profiles.parquet"
    rows = pd.read_parquet(artifact)
    rows["longitude"] = 74.0
    rows.to_parquet(artifact, index=False)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Temperature profile at 19N 70E in July 2024"))

    assert response.status_code == 200
    body = response.json()
    assert body["params"]["location"]["radius_km"] == 500.0
    assert body["params"]["location"]["radius_explicit"] is False
    sufficiency = body["data_sufficiency"]
    assert sufficiency["requested_radius_km"] == 300.0
    assert sufficiency["actual_radius_km"] == 500.0
    assert sufficiency["radius_expanded"] is True
    assert 400 < sufficiency["nearest_observation_km"] < 500
    assert "expanded from 300 km" in body["summary"]
    assert "expanded from 300 km" in body["answer_explanation"]
    assert "nearest observation" in body["answer_explanation"]


def test_explicit_point_radius_is_not_auto_expanded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_query_ready_fixture(tmp_path)
    artifact = tmp_path / "processed" / "argo_profiles.parquet"
    rows = pd.read_parquet(artifact)
    rows["longitude"] = 74.0
    rows.to_parquet(artifact, index=False)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    response = asyncio.run(post_chat("Temperature profile at 19N 70E within 50 km in July 2024"))

    assert response.status_code == 404
    error = response.json()["error"]
    assert "within 50 km" in error["message"]
    assert error["nearest_available_km"] is not None


def test_no_data_behavior_is_unchanged_when_live_source_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression guard: the live-source addition must be inert by default.

    Runs the exact scenario from ``test_no_matching_location_returns_no_data``
    with the flag unset, then again with it explicitly "false", and asserts
    both responses are byte-for-byte identical to each other and to the
    original no_data contract -- proving the additive code path in
    ``chat.py`` changes nothing unless explicitly enabled.
    """
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))

    monkeypatch.delenv("FLOATCHAT_LIVE_SOURCE_ENABLED", raising=False)
    response_unset = asyncio.run(post_chat("Temperature profile near Chennai in July 2024"))

    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "false")
    response_disabled = asyncio.run(post_chat("Temperature profile near Chennai in July 2024"))

    assert response_unset.status_code == response_disabled.status_code == 404
    assert response_unset.json() == response_disabled.json()
    assert response_unset.json()["error"]["type"] == "no_data"
    assert "live" not in response_unset.text.lower()


def _live_argovis_document() -> dict:
    """A minimal, realistically-shaped Argovis /argo document.

    Mirrors the exact structure captured from the live API (see
    live_source.py's module docstring): data_info is
    [keys, ["units","data_keys_mode"], [[unit, mode], ...]], data is a
    column-major matrix aligned to keys.
    """
    return {
        "_id": "7901125_002",
        "geolocation": {"type": "Point", "coordinates": [80.27, 13.08]},
        "timestamp": "2024-07-15T14:02:01.999Z",
        "cycle_number": 2,
        "geolocation_argoqc": 1,
        "data_info": [
            ["pressure", "temperature", "salinity", "temperature_argoqc", "salinity_argoqc"],
            ["units", "data_keys_mode"],
            [["decibar", "D"], ["degree_Celsius", "D"], ["psu", "D"], [None, None], [None, None]],
        ],
        "data": [[5.0, 50.0], [29.5, 28.7], [34.9, 35.0], [1, 1], [1, 1]],
    }


def test_live_source_fills_a_local_no_data_gap_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The enabled path must still work after main's auto-expansion retrieval.

    This composes two independently-built no-data recoveries: local radius
    auto-expansion (tried first, still empty here) and the live-source
    fallback (tried second). Only the network call is mocked; retrieval, QC,
    aggregation, and evidence grading all run for real against the live-shaped
    frame, proving the fallback still reaches the existing pipeline intact
    after the merge restructured chat.py around it.
    """
    write_query_ready_fixture(tmp_path)
    monkeypatch.setattr(chat_module, "get_settings", lambda: settings(tmp_path))
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    monkeypatch.setattr(
        chat_module, "fetch_argo_profiles", lambda *_a, **_k: [_live_argovis_document()]
    )

    response = asyncio.run(post_chat("Temperature profile near Chennai in July 2024"))

    assert response.status_code == 200
    body = response.json()
    assert body["live_source_used"] is True
    assert body["live_source_caveat"] and "Argovis" in body["live_source_caveat"]
    assert body["data"]["bins"]
