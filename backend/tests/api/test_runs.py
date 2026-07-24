"""GET /api/runs — list and detail of persisted runs."""

from __future__ import annotations

from app.runs import repo
from tests.runs.test_repo import make_run


async def test_list_returns_persisted_runs(api_client: object, db_session: object) -> None:
    await repo.create_run(db_session, make_run("AAPL"))  # type: ignore[arg-type]
    await db_session.commit()  # type: ignore[attr-defined]

    resp = await api_client.get("/api/runs")  # type: ignore[union-attr]
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
    # summary shape must omit the heavy equity curve
    assert "equity" not in rows[0]


async def test_detail_returns_full_run_with_equity(api_client: object, db_session: object) -> None:
    run = await repo.create_run(db_session, make_run("MSFT"))  # type: ignore[arg-type]
    await db_session.commit()  # type: ignore[attr-defined]

    resp = await api_client.get(f"/api/runs/{run.id}")  # type: ignore[union-attr]
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == run.id
    assert body["strategy_name"] == "sma_cross"
    assert body["equity"] == [{"ts": "2024-01-01T00:00:00+00:00", "equity": 1.0}]


async def test_detail_unknown_run_returns_404(api_client: object) -> None:
    resp = await api_client.get("/api/runs/99999")  # type: ignore[union-attr]
    assert resp.status_code == 404
