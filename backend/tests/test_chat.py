import asyncio

from httpx import ASGITransport, AsyncClient, Response

from app.main import app


async def post_chat(query: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/chat", json={"query": query})


def test_unsupported_query_returns_typed_parse_error() -> None:
    response = asyncio.run(post_chat("Will it rain tomorrow?"))

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "parse_error"


def test_supported_query_does_not_invent_data_when_dataset_is_absent() -> None:
    response = asyncio.run(post_chat("Show temperature profile near Mumbai in July 2024"))

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "general_error"
    assert "trace" not in response.text.lower()
