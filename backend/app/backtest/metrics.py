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

    Works with float positions: entry = flat→nonzero, exit = nonzero→flat.
    Short positions (negative) profit when price falls.
    Returns (win_rate, n_closed_trades).
    """
    close = bars["close"].reset_index(drop=True)
    pos = position.reset_index(drop=True)
    n = len(pos)
    in_position = False
    entry_idx = -1
    entry_dir = 1.0
    wins = 0
    closed = 0
    for i in range(n):
        cur_active = abs(float(pos.iloc[i])) > 1e-10
        prev_active = abs(float(pos.iloc[i - 1])) > 1e-10 if i > 0 else False
        if not in_position and not prev_active and cur_active:
            in_position = True
            entry_idx = i
            entry_dir = 1.0 if float(pos.iloc[i]) > 0 else -1.0
        elif in_position and prev_active and not cur_active:
            in_position = False
            pnl = entry_dir * (float(close.iloc[i] / close.iloc[entry_idx] - 1.0))
            closed += 1
            if pnl > 0:
                wins += 1
    if closed == 0:
        return 0.0, 0
    return wins / closed, closed


def sortino(returns: pd.Series, periods_per_year: int) -> float:
    """Annualized Sortino ratio; only penalizes downside deviation. Zero → 0."""
    downside = returns[returns < 0]
    dd_std = float(downside.std(ddof=0)) if len(downside) > 1 else 0.0
    if dd_std < 1e-15 or not np.isfinite(dd_std):
        return 0.0
    return float(returns.mean() / dd_std * np.sqrt(periods_per_year))


def calmar(equity: pd.Series, ppy: int) -> float:
    """CAGR / |Max Drawdown|. Measures return per unit of worst drawdown."""
    mdd = abs(max_drawdown(equity))
    if mdd < 1e-15:
        return 0.0
    return cagr(equity, ppy) / mdd


def volatility(returns: pd.Series, periods_per_year: int) -> float:
    """Annualized volatility of returns."""
    return float(returns.std(ddof=0) * np.sqrt(periods_per_year))


def value_at_risk(returns: pd.Series, confidence: float = 0.05) -> float:
    """Historical VaR at the given confidence level (default 5%). Always <= 0."""
    if len(returns) == 0:
        return 0.0
    return float(returns.quantile(confidence))


def profit_factor(returns: pd.Series) -> float:
    """Gross profit / gross loss. >1 = profitable, inf = no losses."""
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses < 1e-15:
        return float("inf") if gains > 0 else 0.0
    return float(gains / losses)


def avg_trade_duration(bars: pd.DataFrame, position: pd.Series) -> float:
    """Average bars held per closed round-trip trade. 0 if no closed trades."""
    if "ts" not in bars.columns or len(position) == 0:
        return 0.0
    pos = position.reset_index(drop=True)
    n = len(pos)
    in_position = False
    entry_idx = -1
    durations: list[int] = []
    for i in range(n):
        cur_active = abs(float(pos.iloc[i])) > 1e-10
        prev_active = abs(float(pos.iloc[i - 1])) > 1e-10 if i > 0 else False
        if not in_position and not prev_active and cur_active:
            in_position = True
            entry_idx = i
        elif in_position and prev_active and not cur_active:
            in_position = False
            durations.append(i - entry_idx)
    if not durations:
        return 0.0
    return float(np.mean(durations))


def max_consecutive_losses(bars: pd.DataFrame, position: pd.Series) -> int:
    """Longest streak of consecutive losing closed trades."""
    close = bars["close"].reset_index(drop=True)
    pos = position.reset_index(drop=True)
    n = len(pos)
    in_position = False
    entry_idx = -1
    entry_dir = 1.0
    max_streak = 0
    cur_streak = 0
    for i in range(n):
        cur_active = abs(float(pos.iloc[i])) > 1e-10
        prev_active = abs(float(pos.iloc[i - 1])) > 1e-10 if i > 0 else False
        if not in_position and not prev_active and cur_active:
            in_position = True
            entry_idx = i
            entry_dir = 1.0 if float(pos.iloc[i]) > 0 else -1.0
        elif in_position and prev_active and not cur_active:
            in_position = False
            pnl = entry_dir * (float(close.iloc[i] / close.iloc[entry_idx] - 1.0))
            if pnl < 0:
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
            else:
                cur_streak = 0
    return max_streak
