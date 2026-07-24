"""Metric math — pure numpy/pandas functions on a strategy's returns/equity."""

from __future__ import annotations

import numpy as np
import pandas as pd

_PERIODS_PER_YEAR: dict[str, int] = {
    "1d": 252,
    "1wk": 52,
    "1mo": 12,
    "1h": int(252 * 6.5),
    "30m": 252 * 13,
    "15m": 252 * 26,
    "5m": 252 * 78,
    "1m": 252 * 390,
}


def periods_per_year(timeframe: str) -> int:
    """Trading periods per year for a given timeframe. Unknown → 252."""
    return _PERIODS_PER_YEAR.get(timeframe, 252)


def total_return(equity: pd.Series) -> float:
    """equity[-1] / equity[0] - 1."""
    if len(equity) == 0:
        return 0.0
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def cagr(equity: pd.Series, periods_per_year: int) -> float:
    """Compound annual growth rate."""
    n = len(equity)
    if n < 2 or equity.iloc[0] <= 0:
        return 0.0
    years = (n - 1) / periods_per_year
    if years <= 0:
        return 0.0
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def sharpe(returns: pd.Series, periods_per_year: int) -> float:
    """Annualized Sharpe ratio; risk-free = 0. Zero std → 0."""
    std = float(returns.std(ddof=0))
    if std < 1e-15 or not np.isfinite(std):
        return 0.0
    return float(returns.mean() / std * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> float:
    """Largest peak-to-trough drop. Always <= 0."""
    if len(equity) == 0:
        return 0.0
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def win_rate(bars: pd.DataFrame, position: pd.Series) -> tuple[float, int]:
    """Fraction of closed round-trip trades that were profitable.

    A closed trade = entry (0→1) at bar `t` followed by exit (1→0) at bar `t' > t`.
    pnl = close[t'] / close[t] - 1. Open positions are ignored.
    Returns (win_rate, n_closed_trades).
    """
    close = bars["close"].reset_index(drop=True)
    pos = position.reset_index(drop=True)
    n = len(pos)
    in_position = False
    entry_idx = -1
    wins = 0
    closed = 0
    for i in range(n):
        cur = int(pos.iloc[i])
        prev = int(pos.iloc[i - 1]) if i > 0 else 0
        if not in_position and prev == 0 and cur == 1:
            in_position = True
            entry_idx = i
        elif in_position and prev == 1 and cur == 0:
            in_position = False
            pnl = float(close.iloc[i] / close.iloc[entry_idx] - 1.0)
            closed += 1
            if pnl > 0:
                wins += 1
    if closed == 0:
        return 0.0, 0
    return wins / closed, closed
