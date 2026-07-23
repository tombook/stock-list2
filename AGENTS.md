# AGENTS.md — stock-list2

stock-list2 is an **opinionated, async, type-safe trading-research core**, rebuilt
from scratch from `/root/stock-list` (the "Vibe-Trading" project). It is **not** a
port — see `docs/ANALYSIS.md` for what was wrong with the original and the decisions
below for what was deliberately dropped.

When working here, follow this file. It is the single source for "how we build."

## Identity & philosophy

- Small core, done well. **Not** feature parity with the old 302K-LOC project.
- Async end-to-end. Typed everywhere. Tested from day one.
- One responsibility per file, **<300 LOC**. No `Any`, no `# type: ignore`, no `as any`.

## What we keep vs. drop (do not re-introduce the dropped items)

**Keep:** market-data backbone · a tight LLM tool-calling agent (no langchain) · one
vectorized backtester · clean FastAPI surface · focused React UI · async persistence.

**Dropped (do not add back without an explicit need):** langchain/langgraph · 260
auto-evolved skills · 9 backtest engines · Pine/TDX/MT5 multi-export · shadow account
· trade-journal analyzer · blue-green deploy + nginx templates · MCP server · CLI/TUI
· swarm presets · stock2026/supabase module.

## Architecture (dependency flows downward only)

```
api/          thin routers, one per domain; no business logic, no direct DB/HTTP
  ↓
domains/      business logic + the agent loop + market-data service
  ↓
core/         settings, db (single engine), logging, errors
```

- `core` depends on nothing in the app.
- A domain may use `core` and other domains' public service functions only.
- `api` calls domain services only — never a DB session or HTTP client directly.
- **One async DB engine** in `app/core/db.py`, built from the single `Settings`.
  Never copy connection config into another module (this was the old project's
  worst recurring bug).

## Stack

- Backend: Python `>=3.11,<3.14`, FastAPI, SQLAlchemy 2.0 async + asyncpg,
  pydantic v2 + pydantic-settings, httpx (LLM + future clients), structlog,
  yfinance (wrapped via `asyncio.to_thread`), pandas/numpy (backtest). Tooling: uv, ruff, pytest.
- Frontend: Vite + React 19 + TS strict + Tailwind + zustand + sonner; vitest.
- LLM: OpenAI-compatible via httpx directly (provider configured in settings).

## Working rules

- All external I/O is async or offloaded to a thread.
- Config comes only from `app/core/settings.py` (env / `.env`). Don't read `os.environ` elsewhere.
- Errors: raise `DomainError`/`NotFoundError`/`UpstreamError` from `app/core/errors.py`;
  they map to HTTP in one place.
- Logging: `structlog` via `app.core.logging.get_logger`.
- Tests: every layer has unit tests; external calls (LLM, network) are mocked.
  Run: `uv run pytest` (backend), `npm run test` / `npm run build` (frontend).

## Run

`uv` is on the system PATH (symlinked to `/usr/local/bin/uv`), and `node`/`npm` are
system-wide. Backend deps live in `backend/.venv`; frontend deps in `frontend/node_modules`.

```bash
cd backend && uv sync --extra dev
uv run uvicorn app.main:app --host 0.0.0.0 --port 8900   # API
uv run pytest                                              # tests (9, all green)
cd ../frontend && npm run dev                              # UI on :5900 (proxies /api,/health -> :8900)
npm run build && npm run test                             # build + vitest (5, green)
```

The services are likely already running (detached). Check with `ss -tlnp | grep -E ':(8900|5900|85)'`.
To restart one, kill by port then relaunch, e.g.
`pids=$(ss -tlnpH 'sport = :8900' | grep -oP 'pid=\K[0-9]+'|sort -u); for p in $pids; do kill $p; done`.
nginx `:85 → :5900` is configured at `/etc/nginx/sites-enabled/stock-list2.conf`.

## Status & next

- **v0 foundation** and **v0.1 agent core** are done and **live-verified**: `POST /api/analyze`
  streams SSE (`tool_call`→`tool_result`→`final`), and glm-5.2 really calls `get_quote`
  and answers from live data.
- LLM is configured in `backend/.env` (`LLM_*`): glm-5.2 on Zhipu's **coding** paas
  endpoint (`https://open.bigmodel.cn/api/coding/paas/v4`) — the mainstream `paas/v4`
  returns 429 for this key.
- **Next is v0.2**: one vectorized backtester (pandas/numpy), `POST /api/backtest`,
  and a `run_backtest` agent tool. See `docs/ROADMAP.md` for the full plan and
  `docs/ARCHITECTURE.md` for the layering.
