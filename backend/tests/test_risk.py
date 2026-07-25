"""Tests for pre-trade risk engine and post-trade analytics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from app.marketdata.models import Bar, Bars, Quote
from app.risk.analytics import compute_risk
from app.risk.engine import check_order
from app.trading.models import Account, Order

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _fake_bars(n: int = 100) -> Bars:
    rng = np.random.default_rng(42)
    close = 100 * np.exp(rng.standard_normal(n).cumsum() * 0.02)
    return Bars(
        symbol="TEST",
        timeframe="1d",
        source="test",
        bars=[
            Bar(
                ts=_BASE + timedelta(days=i),
                open=c,
                high=c + 1,
                low=c - 1,
                close=c,
                volume=1e6,
            )
            for i, c in enumerate(close)
        ],
    )


class TestRiskEngine:
    @pytest.mark.asyncio
    async def test_small_order_passes(self, db_session) -> None:
        account = Account(cash=100_000, initial_cash=100_000)
        db_session.add(account)
        await db_session.flush()

        order = Order(
            account_id=account.id,
            symbol="AAPL",
            side="buy",
            qty=1,
            order_type="market",
        )
        db_session.add(order)
        await db_session.flush()

        with patch(
            "app.risk.engine.market_service.get_quote",
            new=AsyncMock(return_value=Quote(symbol="AAPL", price=150.0, source="test")),
        ):
            result = await check_order(db_session, account, order)

        assert result.passed is True
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_large_order_warns(self, db_session) -> None:
        account = Account(cash=100_000, initial_cash=100_000)
        db_session.add(account)
        await db_session.flush()

        order = Order(
            account_id=account.id,
            symbol="BRK.A",
            side="buy",
            qty=100,
            order_type="market",
        )
        db_session.add(order)
        await db_session.flush()

        with patch(
            "app.risk.engine.market_service.get_quote",
            new=AsyncMock(return_value=Quote(symbol="BRK.A", price=50000.0, source="test")),
        ):
            result = await check_order(db_session, account, order)

        assert any(v.severity == "warn" for v in result.violations)

    @pytest.mark.asyncio
    async def test_drawdown_blocks(self, db_session) -> None:
        account = Account(cash=50_000, initial_cash=100_000)
        db_session.add(account)
        await db_session.flush()

        order = Order(
            account_id=account.id,
            symbol="AAPL",
            side="buy",
            qty=1,
            order_type="market",
        )
        db_session.add(order)
        await db_session.flush()

        with patch(
            "app.risk.engine.market_service.get_quote",
            new=AsyncMock(return_value=Quote(symbol="AAPL", price=150.0, source="test")),
        ):
            result = await check_order(db_session, account, order)

        assert result.passed is False
        assert any(v.rule == "max_drawdown_stop" for v in result.violations)


class TestRiskAnalytics:
    def test_compute_risk_returns_valid_metrics(self) -> None:
        bars = _fake_bars(252)
        result = compute_risk(bars)

        assert result.symbol == "TEST"
        assert result.var_95 < 0  # VaR is negative
        assert result.var_99 < result.var_95  # 99% is worse
        assert result.cvar_95 <= result.var_95  # CVaR worse than VaR
        assert result.max_drawdown < 0
        assert result.volatility_annual > 0
        assert result.worst_day < 0
        assert result.best_day > 0

    def test_compute_risk_insufficient_data(self) -> None:
        bars = Bars(
            symbol="NEW",
            timeframe="1d",
            source="test",
            bars=[Bar(ts=_BASE, open=100, high=101, low=99, close=100, volume=1e6)],
        )
        result = compute_risk(bars)
        assert result.source == "insufficient_data"
        assert result.var_95 == 0
