"""Metric math — pure functions on known arrays."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.backtest.metrics import (
    cagr,
    max_drawdown,
    periods_per_year,
    sharpe,
    total_return,
    win_rate,
)


def test_periods_per_year_known_timeframes() -> None:
    assert periods_per_year("1d") == 252
    assert periods_per_year("1wk") == 52
    assert periods_per_year("1mo") == 12
    assert periods_per_year("unknown") == 252  # fallback


def test_total_return_on_known_equity() -> None:
    equity = pd.Series([1.0, 1.1, 1.2])
    assert round(total_return(equity), 6) == round(0.2, 6)


def test_cagr_on_year_long_flat() -> None:
    # 252 bars from 1.0 to 1.25 → 25% over 1 year → CAGR 0.25
    equity = pd.Series([1.0 + 0.25 * i / 251 for i in range(252)])
    cagr_val = cagr(equity, periods_per_year=252)
    assert 0.24 < cagr_val < 0.26


def test_sharpe_zero_std_returns_zero() -> None:
    returns = pd.Series([0.001] * 10)
    assert sharpe(returns, periods_per_year=252) == 0.0


def test_sharpe_positive_for_positive_returns() -> None:
    rng = np.random.default_rng(42)
    returns = pd.Series(rng.normal(0.002, 0.01, 500))
    assert sharpe(returns, periods_per_year=252) > 0


def test_max_drawdown_known_dip() -> None:
    # Peak 1.2, trough 0.9 → -25%
    equity = pd.Series([1.0, 1.2, 0.9, 1.1])
    assert round(max_drawdown(equity), 4) == round(-0.25, 4)


def test_win_rate_two_closed_trades_one_winner() -> None:
    # closes: enter@10 exit@12 (win), enter@12 exit@10 (loss)
    closes = [10, 10, 12, 12, 10, 10]
    bars = pd.DataFrame(
        {"close": closes, "open": closes, "high": closes, "low": closes, "volume": [1.0] * 6}
    )
    position = pd.Series([0, 1, 1, 0, 0, 0])  # enter at idx1 (close=10), exit at idx3 (close=12)
    rate, n_closed = win_rate(bars, position)
    assert n_closed == 1
    assert rate == 1.0


def test_win_rate_no_closed_trades_returns_zero() -> None:
    bars = pd.DataFrame({"close": [1.0, 1.0, 1.0]})
    position = pd.Series([1, 1, 1])  # enters but never exits
    rate, n_closed = win_rate(bars, position)
    assert rate == 0.0
    assert n_closed == 0
