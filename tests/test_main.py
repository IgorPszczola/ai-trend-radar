import os
import importlib
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient


os.environ.setdefault("RAPIDAPI_KEY", "test-rapidapi-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")

main = importlib.import_module("main")


class FakeCollection:
    def __init__(self):
        self.deleted_filters = []
        self.inserted_docs = []

    async def delete_many(self, filt):
        self.deleted_filters.append(filt)

    async def insert_many(self, docs):
        for idx, doc in enumerate(docs):
            doc["_id"] = f"fake-id-{idx}"
        self.inserted_docs.extend(docs)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        return FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_fetch_instagram_trends_success(monkeypatch):
    payload = {
        "data": {
            "items": [
                {
                    "caption": {"text": "Summer outfit", "hashtags": ["fashion", "street"]},
                    "location": {"name": "Warsaw"},
                    "code": "ABC123",
                    "taken_at": 1710000000,
                },
                {
                    "caption": {"text": ""},
                    "location": {"name": "Paris"},
                    "code": "SKIPME",
                    "taken_at": 1710001000,
                },
            ]
        }
    }

    fake_collection = FakeCollection()

    monkeypatch.setattr(main, "collection", fake_collection)
    monkeypatch.setattr(main, "generate_pro_prompt", AsyncMock(return_value="pro prompt"))
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient(payload))

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/trends/instagram", params={"username": "fit_aitana"})

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["source"] == "instagram/fit_aitana"
    assert body["count"] == 1
    assert len(body["trends"]) == 1

    trend = body["trends"][0]
    assert trend["text"] == "Summer outfit"
    assert trend["ai_prompt"] == "pro prompt"
    assert trend["hashtags"] == ["fashion", "street"]
    assert trend["location"] == "Warsaw"
    assert trend["url"] == "https://www.instagram.com/p/ABC123/"
    assert "fake-id-0" == trend["_id"]

    assert fake_collection.deleted_filters
    assert "$lt" in fake_collection.deleted_filters[0]["fetched_at"]
    assert isinstance(datetime.fromisoformat(trend["published_at"].replace("Z", "+00:00")), datetime)


@pytest.mark.asyncio
async def test_fetch_instagram_trends_returns_debug_payload_for_unexpected_schema(monkeypatch):
    payload = {"unexpected": "shape"}

    monkeypatch.setattr(main.httpx, "AsyncClient", lambda *args, **kwargs: FakeAsyncClient(payload))

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/trends/instagram")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "UWAGA" in body
    assert body["DEBUG_RAW_DATA"] == payload


@pytest.mark.asyncio
async def test_fetch_instagram_trends_maps_http_errors_to_502(monkeypatch):
    class ErrorClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            raise main.httpx.HTTPError("boom")

    monkeypatch.setattr(main.httpx, "AsyncClient", lambda *args, **kwargs: ErrorClient())

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/trends/instagram")

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "RapidAPI" in response.json()["detail"]


@pytest.mark.asyncio
async def test_root_endpoint_serves_html():
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    assert "Prompt" in response.text