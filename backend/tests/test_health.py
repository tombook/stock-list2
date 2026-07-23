"""Health endpoint — no real DB/network: db.ping is stubbed."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.main import app


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health_reports_ok_when_db_up(client: httpx.AsyncClient) -> None:
    with patch("app.core.db.ping", new=AsyncMock(return_value=True)):
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["dependencies"]["postgres"]["status"] == "ok"
    assert body["dependencies"]["market_data"]["status"] == "ok"


async def test_health_degraded_when_db_down(client: httpx.AsyncClient) -> None:
    with patch("app.core.db.ping", new=AsyncMock(return_value=False)):
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"
