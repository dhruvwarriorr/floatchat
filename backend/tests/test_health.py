import asyncio

from httpx import ASGITransport, AsyncClient, Response

from app.main import app


async def get(path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_liveness_is_independent_of_scientific_data() -> None:
    response = asyncio.run(get("/health/live"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_is_honest_when_manifest_is_missing() -> None:
    response = asyncio.run(get("/health/ready"))

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
