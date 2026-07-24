# Roadmap — stock-list2

stock-list2 is built incrementally. v0 (the foundation) is done. Everything below
is prioritized by leverage: each item unblocks the next.

## Done — v0 foundation

- [x] Core: async settings/db/logging/errors (single engine, single config source).
- [x] Market-data backbone: typed models, TTL cache, yfinance source, fallback
      registry, service. `/health`, `/api/quote/{symbol}`, `/api/bars/{symbol}`.
- [x] Tests: pytest-asyncio + httpx (ASGI), registry mocked. 5 green.
- [x] Independent `stocklist2` database (reuses the existing PG container on :5433).

## Done — v0.1 agent core (the product's heart)

- [x] `app/agent/`: a tight async ReAct/tool-calling loop. **No langchain** — talks to
      an OpenAI-compatible endpoint directly via `httpx` (`llm.py`).
- [x] Hand-written tools, few and typed: `get_quote`, `get_bars` (delegating to the
      market-data service). `run_backtest` lands with v0.2.
- [x] `POST /api/analyze` — streams the loop as SSE events
      (`step`, `tool_call`, `tool_result`, `final`, `error`, `done`).
- [x] Tests with a stubbed LLM (deterministic tool-call → final; tool failure path;
      SSE endpoint incl. error event). 9 backend tests green.

> Live end-to-end run needs a valid LLM credential in `backend/.env`
> (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`). The key reused from the original
> project (zhipu) is expired — both endpoints return 401. Any OpenAI-compatible
> provider works (OpenAI, DeepSeek, OpenRouter, Moonshot, a fresh Zhipu key, …).

## Done — v0.2 one good backtester

- [x] `app/backtest/`: a single vectorized engine (pandas/numpy). One engine, not
      nine. Strategy = a pure function `bars → signals`.
- [x] Metrics: total return, CAGR, Sharpe, max drawdown, win rate.
- [x] `POST /api/backtest` and a `run_backtest` agent tool.

## Done — v0.3 persistence + UI wiring

- [x] First ORM domain (runs) via async SQLAlchemy; Alembic introduced (`migrations/`).
      `GET /api/runs`, `GET /api/runs/{id}`, best-effort persist on `POST /api/backtest`.
- [x] Frontend: Analyze page (chat + SSE streaming), backtest panel, runs history
      list + detail pages, candlestick price chart on Markets page.

## Deliberately out of scope for v1

The following from the original project are **dropped** unless a concrete need
appears: 260 auto-evolved skills, 9 backtest engines, Pine/TDX/MT5 multi-export,
shadow account, trade-journal analyzer, geopolitical-risk, blue-green deploy +
nginx templates, MCP server, CLI/TUI, 29 swarm presets, stock2026/supabase.

## Operating the running service

```bash
cd /root/stock-list2/backend
uv sync --extra dev
uv run uvicorn app.main:app --host 0.0.0.0 --port 8900   # API on :8900
uv run pytest                                              # tests
uv run ruff check app                                      # lint
```
