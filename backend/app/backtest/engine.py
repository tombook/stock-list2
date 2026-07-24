"""The single Vectorized backtester.

Strategy emits a target-position series known at bar `t`'s close; the engine
shifts it by one so a position earned at bar t+1 is decided on bar t
information (no lookahead). Cost is applied as `model.total_bps * 1e-4 * turnover`
where turnover is the absolute change in position per bar.

Position is a float in [-1, +1]: +1 = full long, -1 = full short, 0 = flat.
Negative positions × negative asset returns yield positive returns (short PnL).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.backtest.cost_model import CostModel


@dataclass(frozen=True)
class EngineResult:
    position: pd.Series          # realized position (shifted signal, no lookahead)
    asset_returns: pd.Series     # close.pct_change()
    strategy_returns: pd.Series  # position * asset_returns - trade_cost
    equity: pd.Series            # compounded, starts at 1.0
    n_entries: int               # flat→nonzero transitions (long or short)
    n_closed_trades: int         # entries that subsequently exited to flat


def _count_closed_trades(position: pd.Series) -> int:
    """Count nonzero→flat round trips; ignores any open position at the end."""
    in_position = False
    closed = 0
    for v in position:
        active = abs(float(v)) > 1e-10
        if not in_position and active:
            in_position = True
        elif in_position and not active:
            in_position = False
            closed += 1
    return closed


def run(
    bars: pd.DataFrame,
    signal: pd.Series,
    *,
    cost_bps: float = 0.0,
    cost_model: CostModel | None = None,
) -> EngineResult:
    if cost_bps < 0:
        raise ValueError("cost_bps must be >= 0")
    if len(bars) != len(signal):
        raise ValueError("bars and signal length mismatch")

    model = cost_model or CostModel.from_bps(cost_bps)

    # shift(1) 确保信号在下一根 bar 生效（无 lookahead）；float 仓位支持做空和部分仓位
    position = signal.shift(1).fillna(0.0).astype("float64")
    asset_returns = bars["close"].pct_change().fillna(0.0)
    turnover = position.diff().abs().fillna(position.abs().astype("float64"))
    trade_cost = (model.total_bps * 1e-4) * turnover
    strategy_returns = position * asset_returns - trade_cost
    equity = (1.0 + strategy_returns).cumprod()

    # 入场计数：从平仓（|pos|≈0）到持仓（|pos|>0）的转换
    was_flat = position.shift(1).abs() <= 1e-10
    now_active = position.abs() > 1e-10
    n_entries = int((was_flat & now_active).sum())
    n_closed = _count_closed_trades(position)

    return EngineResult(
        position=position,
        asset_returns=asset_returns,
        strategy_returns=strategy_returns,
        equity=equity,
        n_entries=n_entries,
        n_closed_trades=n_closed,
    )
