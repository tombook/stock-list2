"""POST /api/backtest persists the run best-effort alongside returning metrics.

Market data is faked so the test is hermetic (no yfinance network call).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.marketdata import service as market_service
from app.marketdata.models import Bar, Bars


@pytest.fixture
def _fake_bars(monkeypatch: pytest.MonkeyPatch) -> None:
    """60 daily bars with a gentle uptrend — enough for any strategy to produce a run."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [
        Bar(
            ts=base + timedelta(days=i),
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1_000_000.0,
        )
        for i in range(60)
    ]
    fixture = Bars(symbol="AAPL", timeframe="1d", bars=bars, source="test")

    async def fake_get_bars(symbol: str, timeframe: str = "1d", limit: int = 120) -> Bars:
        return fixture

    monkeypatch.setattr(market_service, "get_bars", fake_get_bars)


async def test_backtest_persists_a_run(api_client: object, _fake_bars: None) -> None:
    resp = await api_client.post(  # type: ignore[union-attr]
        "/api/backtest",
        json={
            "symbol": "AAPL",
            "strategy": {"name": "buy_hold", "params": {}},
            "timeframe": "1d",
            "limit": 50,
            "cost_bps": 0,
        },
    )
    assert resp.status_code == 200

    runs = await api_client.get("/api/runs")  # type: ignore[union-attr]
    assert runs.status_code == 200
    rows = runs.json()
    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["strategy_name"] == "buy_hold"

    detail = await api_client.get(f"/api/runs/{rows[0]['id']}")  # type: ignore[union-attr]
    assert detail.status_code == 200
    assert len(detail.json()["equity"]) == 60
