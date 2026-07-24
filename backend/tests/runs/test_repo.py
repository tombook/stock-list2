"""Run repository CRUD against the real Postgres (db_session fixture)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.runs import repo
from app.runs.models import Run


def make_run(symbol: str = "AAPL") -> Run:
    """Build a fully-populated Run (no id / created_at — those are server-generated)."""
    return Run(
        symbol=symbol,
        strategy_name="sma_cross",
        strategy_params={"fast": 5, "slow": 20},
        timeframe="1d",
        cost_bps=0.0,
        n_bars=252,
        period_start=datetime(2024, 1, 1, tzinfo=UTC),
        period_end=datetime(2024, 12, 31, tzinfo=UTC),
        total_return=0.12,
        cagr=0.12,
        sharpe=1.1,
        max_drawdown=-0.08,
        win_rate=0.5,
        n_trades=6,
        equity=[{"ts": "2024-01-01T00:00:00+00:00", "equity": 1.0}],
    )


async def test_create_assigns_id_and_round_trips(db_session: object) -> None:
    run = await repo.create_run(db_session, make_run())  # type: ignore[arg-type]
    await db_session.commit()  # type: ignore[attr-defined]

    assert run.id > 0
    assert run.created_at is not None

    fetched = await repo.get_run(db_session, run.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.symbol == "AAPL"
    assert fetched.total_return == 0.12
    assert fetched.strategy_params == {"fast": 5, "slow": 20}
    assert fetched.equity == [{"ts": "2024-01-01T00:00:00+00:00", "equity": 1.0}]


async def test_get_missing_run_returns_none(db_session: object) -> None:
    assert await repo.get_run(db_session, 999_999) is None  # type: ignore[arg-type]


async def test_list_runs_orders_newest_first(db_session: object) -> None:
    first = await repo.create_run(db_session, make_run("MSFT"))  # type: ignore[arg-type]
    await db_session.commit()  # type: ignore[attr-defined]
    second = await repo.create_run(db_session, make_run("GOOG"))  # type: ignore[arg-type]
    await db_session.commit()  # type: ignore[attr-defined]

    rows = await repo.list_runs(db_session)  # type: ignore[arg-type]
    # created_at server-defaults may tie at millisecond resolution; ids strictly increase.
    assert rows[0].id == second.id
    assert rows[1].id == first.id
