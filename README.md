# stock-list2

Greenfield rebuild of the `stock-list` (Vibe-Trading) trading-research platform.

This project is a clean, layered, behavior-compatible reimplementation. It is **not** a
1:1 line-for-line copy. The goal is a smaller, better-structured core that is easy to
test and grow, with a clear migration path for the remaining domains from
`/root/stock-list`.

## Why a rebuild

The original project works, but its structure fights maintainers:

- One `api_server.py` had grown to 4037 lines (since split to ~1994, still large).
- Giant modules: `request_batcher.py` (3987), `middleware.py` (2819),
  `auto_features.py` (2802), `stats.py` (1830).
- DB connection config copy-pasted across 9+ modules, several of them hard-coding
  the wrong port — a real, recurring bug class.
- 229 backend test files but `pytest` was not even in the default install group,
  so the suite effectively never ran. Frontend had only 4 test files.
- 420 skill directories with duplicates (e.g. `skill_r120.py` exists both as a flat
  file and inside `skill-r120/`).

See `docs/ANALYSIS.md` for the full problem list and `docs/ROADMAP.md` for what's
built versus what comes next.

## Stack

- Backend: Python 3.11+ (managed with `uv`), FastAPI, PostgreSQL, Redis.
- Frontend: Vite + React 19 + TypeScript + Tailwind + zustand.
- Same stack as the original on purpose — to minimize migration friction and keep
  the focus on structural improvements.

## Layout

```
stock-list2/
  backend/
    app/
      core/       # settings, db (single source of truth), logging, errors
      schemas/    # pydantic request/response models
      domains/    # one folder per business domain (repo + service)
      api/        # thin routers, one per domain
      main.py     # app factory + wiring
    tests/
  frontend/       # Vite + React (see frontend/README)
  docs/
    ANALYSIS.md       # problems identified in stock-list
    ARCHITECTURE.md   # layering and rules for this codebase
    ROADMAP.md        # what's built vs. what comes next
```

## Run (development)

```bash
# Backend (uses the existing stock-list Postgres on :5433 + Redis on :6379)
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8900
# -> http://localhost:8900/health

# Frontend
cd frontend
npm install && npm run dev
# -> http://localhost:5900  (proxies /api and /health to :8900)
```

Environment: copy `backend/.env.example` to `backend/.env` and set the DB/Redis
vars (defaults point at the existing stock-list containers).

## Status

Foundation (v0) is live. The **market-data backbone** is fully wired (typed,
async, cached, yfinance, fallback-ready) with `/health`, `/api/quote`,
`/api/bars`, and green unit tests. The next milestone is the agent core
(`docs/ROADMAP.md`).
