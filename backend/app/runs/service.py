"""Run service — bridges backtest results to persisted runs and back.

Owns the ORM↔pydantic conversion so the API layer never touches the ORM model
directly. Persistence is best-effort by design: a failed save must never block a
successful backtest from reaching the user.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.backtest.schemas import BacktestResponse
from app.runs.models import EquityRow, Run
from app.runs.repo import create_run, get_run, list_runs


def _equity_to_rows(resp: BacktestResponse) -> list[EquityRow]:
    """Flatten EquityPoint list into JSON-stable rows (ts as ISO8601 string)."""
    return [{"ts": p.ts.isoformat(), "equity": float(p.equity)} for p in resp.equity]


def run_from_response(resp: BacktestResponse, cost_bps: float) -> Run:
    """Build an unsaved Run from a backtest response + the originating cost."""
    return Run(
        symbol=resp.symbol,
        strategy_name=resp.strategy.name,
        strategy_params=dict(resp.strategy.params),
        timeframe=resp.timeframe,
        cost_bps=cost_bps,
        n_bars=resp.n_bars,
        period_start=resp.start,
        period_end=resp.end,
        total_return=resp.metrics.total_return,
        cagr=resp.metrics.cagr,
        sharpe=resp.metrics.sharpe,
        max_drawdown=resp.metrics.max_drawdown,
        win_rate=resp.metrics.win_rate,
        n_trades=resp.metrics.n_trades,
        equity=_equity_to_rows(resp),
    )


async def save_run(session: AsyncSession, resp: BacktestResponse, cost_bps: float) -> Run:
    """Persist a backtest response as a new run and return it (caller commits)."""
    return await create_run(session, run_from_response(resp, cost_bps))


async def fetch_runs(session: AsyncSession, limit: int = 50) -> list[Run]:
    return await list_runs(session, limit)


async def fetch_run(session: AsyncSession, run_id: int) -> Run | None:
    return await get_run(session, run_id)
