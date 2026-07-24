"""Engine — vectorized simulator, no lookahead, optional cost."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.backtest.engine import EngineResult, run


def _bars(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    return pd.DataFrame(
        {
            "ts": pd.date_range("2024-01-01", periods=n, freq="D"),
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [1000.0] * n,
        }
    )


def test_position_is_signal_shifted_with_no_lookahead() -> None:
    bars = _bars([1, 1, 1, 1, 1])
    signal = pd.Series([0, 1, 1, 0, 0], dtype="int64")
    result = run(bars, signal)
    # position[0] always 0; position[t] == signal[t-1] for t >= 1
    assert result.position.iloc[0] == 0
    for t in range(1, len(signal)):
        assert result.position.iloc[t] == signal.iloc[t - 1]


def test_equity_with_zero_cost_matches_manual_compound() -> None:
    bars = _bars([100, 110, 121])  # +10% each day
    signal = pd.Series([1, 1, 1], dtype="int64")  # always long
    result = run(bars, signal, cost_bps=0.0)
    # position[1]=1 earns (110/100-1)=0.1; position[2]=1 earns (121/110-1)=0.1
    # equity = [1.0, 1.1, 1.21]
    assert result.equity.iloc[0] == 1.0
    assert result.equity.iloc[1] == 1.1
    assert result.equity.iloc[2] == pytest.approx(1.21, rel=1e-12)


def test_cost_reduces_equity_on_turnover() -> None:
    bars = _bars([100, 100, 100, 100])
    # Enter at bar 0 → position from bar 1; exit at bar 2 → flat from bar 3
    signal = pd.Series([1, 1, 0, 0], dtype="int64")
    no_cost = run(bars, signal, cost_bps=0.0)
    with_cost = run(bars, signal, cost_bps=100.0)  # 1% per turnover unit
    assert with_cost.equity.iloc[-1] < no_cost.equity.iloc[-1]
    # 100 bps = 0.01 fractional cost; turnover happens at bar 1 (0→1) and bar 3 (1→0)
    # Each costs 0.01 off that bar's return (which is 0 since price flat).
    # So equity should be 1.0 * (1 - 0.01) * (1 - 0.01) = 0.9801
    assert abs(with_cost.equity.iloc[-1] - 0.9801) < 1e-9


def test_n_entries_and_n_closed_trades() -> None:
    bars = _bars([1, 1, 1, 1, 1, 1])
    # Enter at bar 0 → position from bar 1; exit at bar 2 → flat from bar 3;
    # re-enter at bar 3 → position from bar 4; never exit (open at end).
    signal = pd.Series([1, 1, 0, 1, 1, 1], dtype="int64")
    result = run(bars, signal)
    assert result.n_entries == 2           # signal 0→1 at bar 0; 0→1 at bar 3
    assert result.n_closed_trades == 1     # only the first cycle closed


def test_engine_result_type_and_lengths() -> None:
    bars = _bars([1, 2, 3, 4])
    signal = pd.Series([1, 1, 1, 1], dtype="int64")
    result = run(bars, signal)
    assert isinstance(result, EngineResult)
    n = len(bars)
    assert len(result.position) == n
    assert len(result.equity) == n
    assert len(result.strategy_returns) == n
