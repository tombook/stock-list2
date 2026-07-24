"""run_from_response — pure conversion from BacktestResponse to an unsaved Run."""

from __future__ import annotations

from datetime import UTC, datetime

from app.backtest.schemas import BacktestResponse, EquityPoint, Metrics, StrategyRef
from app.runs.service import run_from_response


def _resp() -> BacktestResponse:
    return BacktestResponse(
        symbol="MSFT",
        strategy=StrategyRef(name="momentum", params={"lookback": 10}),
        timeframe="1d",
        n_bars=100,
        start=datetime(2024, 1, 1, tzinfo=UTC),
        end=datetime(2024, 6, 1, tzinfo=UTC),
        metrics=Metrics(
            total_return=0.05,
            cagr=0.10,
            sharpe=0.9,
            max_drawdown=-0.03,
            win_rate=0.6,
            n_trades=4,
        ),
        equity=[
            EquityPoint(ts=datetime(2024, 1, 1, tzinfo=UTC), equity=1.0),
            EquityPoint(ts=datetime(2024, 6, 1, tzinfo=UTC), equity=1.05),
        ],
    )


def test_run_from_response_maps_inputs_and_metrics() -> None:
    run = run_from_response(_resp(), cost_bps=2.0)

    assert run.symbol == "MSFT"
    assert run.strategy_name == "momentum"
    assert run.strategy_params == {"lookback": 10}
    assert run.cost_bps == 2.0
    assert run.n_bars == 100
    assert run.total_return == 0.05
    assert run.sharpe == 0.9
    assert run.n_trades == 4


def test_run_from_response_serialises_equity_to_iso_rows() -> None:
    run = run_from_response(_resp(), cost_bps=0.0)

    assert run.equity == [
        {"ts": "2024-01-01T00:00:00+00:00", "equity": 1.0},
        {"ts": "2024-06-01T00:00:00+00:00", "equity": 1.05},
    ]
