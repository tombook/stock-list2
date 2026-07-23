# Architecture — stock-list2

A focused, async, type-safe trading-research **core**. Not a port of stock-list;
a from-scratch design that keeps only what matters and drops the rest (see
`ANALYSIS.md` and `ROADMAP.md`).

## Stack and the reasoning behind it

| Layer | Choice | Why |
|------|--------|-----|
| API | FastAPI (async) | Async-native, typed, the obvious fit. |
| DB | SQLAlchemy 2.0 async + asyncpg | One engine, pool, real concurrency. Replaces raw psycopg2 + N copies of `_DB_CONFIG`. |
| Config | pydantic-settings | Single source of truth; 12-factor. |
| LLM | OpenAI-compatible via `httpx` | Direct tool-calling loop. Drops langchain/langgraph (heavy, version-pinned). |
| Data | yfinance (→ akshare/ccxt later), wrapped in `asyncio.to_thread` | Free sources, sync libs kept off the event loop. |
| Compute | pandas + numpy | Vectorized backtest (one engine, not nine). |
| Logging | structlog | Structured logs from the start. |
| Tests | pytest + pytest-asyncio + httpx (ASGI); vitest (frontend) | Safety net from day one. |
| Tooling | uv, ruff | Fast, modern. |

## Layering (dependency flows downward only)

```
api/          thin routers — one per domain; no business logic, no DB/HTTP calls
  ↓
domains/      business logic (e.g. agent loop, backtest) + market-data service
  ↓
core/         settings, db (single engine), logging, errors  — the foundation
```

Rules:
- `core` depends on nothing in the app.
- A `domain` may use `core` and other domains' public service functions, never
  another domain's internals.
- `api` only calls domain services. It never touches a DB session or an HTTP
  client directly.

## What's built now (v0)

- `app/core/` — `settings`, `db` (async engine + `get_session` + `ping`),
  `logging` (structlog), `errors` (domain exceptions → HTTP).
- `app/marketdata/` — typed `Quote`/`Bar`/`Bars` models, a TTL cache, a
  `DataSource` protocol, a yfinance source (async-wrapped), a fallback `registry`,
  and a `service` that is the only public entry point.
- `app/api/` — `/health` (real Postgres + market-data checks) and
  `/api/quote/{symbol}`, `/api/bars/{symbol}`.
- `tests/` — unit tests for health and the market service (registry mocked); all
  green.

## Decisions that are deliberately NOT made yet

- **Persistence domains** (watchlist, runs, sessions): the engine exists; the first
  ORM domain lands when a feature needs it, with Alembic from that point on.
- **Auth**: none in v0. Add an OAuth/API-key layer when the surface is exposed.
- **Migrations**: tables created via `create_all` until the first real schema
  change, then Alembic is introduced.

## File-size and style rules (enforced by review, soon by ruff/CI)

- One responsibility per file, <300 LOC.
- No `Any`, no `# type: ignore`, no `as any` on the frontend.
- All external I/O is async or offloaded to a thread.
- Every public function has typed params and return types.
