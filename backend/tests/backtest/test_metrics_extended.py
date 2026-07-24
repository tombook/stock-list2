"""Tests for extended metrics (sortino, calmar, volatility, VaR, etc.)."""

from __future__ import annotations

import math

import pandas as pd

from app.backtest import metrics  # noqa: F401


def _equity_series(values: list[float]) -> pd.Series:
    return pd.Series(values)


def _returns_from_equity(equity: pd.Series) -> pd.Series:
    return equity.pct_change().fillna(0.0)


class TestExtendedMetrics:
    def test_sortino_penalizes_only_downside(self) -> None:
        equity = _equity_series([1.0, 1.1, 1.05, 1.15, 1.1, 1.2])
        returns = _returns_from_equity(equity)
        s = metrics.sortino(returns, 252)
        assert s > 0

    def test_sortino_zero_when_no_downside(self) -> None:
        equity = _equity_series([1.0, 1.1, 1.2, 1.3])
        returns = _returns_from_equity(equity)
        assert metrics.sortino(returns, 252) == 0.0

    def test_calmar_is_cagr_over_abs_maxdd(self) -> None:
        equity = _equity_series([1.0, 1.2, 1.1, 1.3])
        c = metrics.calmar(equity, 252)
        assert c > 0

    def test_volatility_annualized(self) -> None:
        returns = pd.Series([0.01, -0.01, 0.02, -0.02] * 10)
        vol = metrics.volatility(returns, 252)
        assert vol > 0

    def test_var_is_negative_quantile(self) -> None:
        returns = pd.Series([-0.05, -0.02, 0.01, 0.03, -0.01, 0.02])
        var = metrics.value_at_risk(returns, 0.05)
        assert var <= 0

    def test_profit_factor_greater_than_one_when_profitable(self) -> None:
        returns = pd.Series([0.05, -0.02, 0.03, -0.01, 0.04])
        pf = metrics.profit_factor(returns)
        assert pf > 1.0

    def test_profit_factor_inf_when_no_losses(self) -> None:
        returns = pd.Series([0.05, 0.03, 0.02])
        assert math.isinf(metrics.profit_factor(returns))

    def test_avg_trade_duration_counts_bars(self) -> None:
        bars = pd.DataFrame({
            "close": [10, 11, 12, 11, 10],
            "ts": pd.date_range("2024-01-01", periods=5),
        })
        position = pd.Series([0.0, 1.0, 1.0, 1.0, 0.0])
        dur = metrics.avg_trade_duration(bars, position)
        assert dur == 3.0

    def test_max_consecutive_losses(self) -> None:
        bars = pd.DataFrame({
            "close": [10, 12, 10, 12, 10, 12, 10],
            "ts": pd.date_range("2024-01-01", periods=7),
        })
        position = pd.Series([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
        mcl = metrics.max_consecutive_losses(bars, position)
        assert mcl == 3
