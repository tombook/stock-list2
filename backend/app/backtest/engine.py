"""The single vectorized backtester.

Strategy emits a {0,1} target-position series known at bar `t`'s close; the
engine shifts it by one so a position earned at bar t+1 is decided on bar t
information (no lookahead). Cost is applied as `cost_bps * 1e-4 * turnover`
where turnover is the absolute change in position per bar.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class EngineResult:
    position: pd.Series          # realized position (shifted signal, no lookahead)
    asset_returns: pd.Series     # close.pct_change()
    strategy_returns: pd.Series  # position * asset_returns - trade_cost
    equity: pd.Series            # compounded, starts at 1.0
    n_entries: int               # 0→1 transitions
    n_closed_trades: int         # entries that subsequently exited


def _count_closed_trades(position: pd.Series) -> int:
    """Count 0→1→0 round trips; ignores any open position at the end."""
    in_position = False
    closed = 0
    for v in position:
        v = int(v)
        if not in_position and v == 1:
            in_position = True
        elif in_position and v == 0:
            in_position = False
            closed += 1
    return closed


def run(
    bars: pd.DataFrame,
    signal: pd.Series,
    *,
    cost_bps: float = 0.0,
) -> EngineResult:
    if cost_bps < 0:
        raise ValueError("cost_bps must be >= 0")
    if len(bars) != len(signal):
        raise ValueError("bars and signal length mismatch")

    position = signal.shift(1).fillna(0).astype("int64")
    asset_returns = bars["close"].pct_change().fillna(0.0)
    turnover = position.diff().abs().fillna(position.abs().astype("float64"))
    trade_cost = (cost_bps * 1e-4) * turnover
    strategy_returns = position * asset_returns - trade_cost
    equity = (1.0 + strategy_returns).cumprod()

    n_entries = int((position.diff() == 1).sum())
    n_closed = _count_closed_trades(position)

    return EngineResult(
        position=position,
        asset_returns=asset_returns,
        strategy_returns=strategy_returns,
        equity=equity,
        n_entries=n_entries,
        n_closed_trades=n_closed,
    )
