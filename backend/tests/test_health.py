import asyncio
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient, Response

import app.api.health as health_module
from app.config import EvidenceGradeThresholds, Settings
from app.main import app


async def get(path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_liveness_is_independent_of_scientific_data() -> None:
    response = asyncio.run(get("/health/live"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_is_honest_when_manifest_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(
            environment="test",
            data_dir=tmp_path,
            static_dir=tmp_path / "static",
            llm_timeout=1,
            default_radius_km=100,
            grade_thresholds=EvidenceGradeThresholds(),
            cors_origins=("http://test",),
        ),
    )
    response = asyncio.run(get("/health/ready"))

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
