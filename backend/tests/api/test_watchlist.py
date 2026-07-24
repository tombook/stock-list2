"""Tests for the watchlist API endpoints (CRUD via httpx ASGI client)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_and_list_item(api_client: AsyncClient) -> None:
    resp = await api_client.post("/api/watchlist", json={"symbol": "AAPL", "note": "test"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["symbol"] == "AAPL"
    assert body["note"] == "test"

    resp = await api_client.get("/api/watchlist")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_patch_item_updates_fields(api_client: AsyncClient) -> None:
    resp = await api_client.post("/api/watchlist", json={"symbol": "MSFT"})
    item_id = resp.json()["id"]

    resp = await api_client.patch(
        f"/api/watchlist/{item_id}", json={"target_price": 450.0, "note": "updated"}
    )
    assert resp.status_code == 200
    assert resp.json()["target_price"] == 450.0
    assert resp.json()["note"] == "updated"


@pytest.mark.asyncio
async def test_delete_item_returns_204(api_client: AsyncClient) -> None:
    resp = await api_client.post("/api/watchlist", json={"symbol": "GOOG"})
    item_id = resp.json()["id"]

    resp = await api_client.delete(f"/api/watchlist/{item_id}")
    assert resp.status_code == 204

    # 确认已删除
    resp = await api_client.get("/api/watchlist")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_patch_missing_item_returns_404(api_client: AsyncClient) -> None:
    resp = await api_client.patch("/api/watchlist/99999", json={"note": "x"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_missing_item_returns_404(api_client: AsyncClient) -> None:
    resp = await api_client.delete("/api/watchlist/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_empty_watchlist_returns_empty_list(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/watchlist")
    assert resp.status_code == 200
    assert resp.json() == []
