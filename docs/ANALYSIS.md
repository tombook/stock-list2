# Analysis — problems found in the original `stock-list`

This is the evidence base that drove stock-list2's design. Every item below was
observed directly in `/root/stock-list`, not assumed.

## Structural problems (high impact)

### 1. DB connection config copy-pasted across 9+ modules
The single most damaging pattern. Each persistence module defined its own
`_DB_CONFIG` dict, several of them **hard-coding `port: 5432`** while only reading
the password from env:

```python
# repeated, with variations, in: llm_config_store, session/store, routers/agent_v2,
# daily_analysis_store, dashboard_data, watchlist_store, swarm/store, yf_pg_store, yf_sync
_DB_CONFIG = {"host": "127.0.0.1", "port": 5432, "dbname": "tradingdb",
              "user": "postgres", "password": os.getenv("DB_PASS", "")}
```

Consequence: on this host (where port 5432 belongs to a different project and the
DB is on 5433) the app connected to the **wrong database** or failed auth at
startup. This is a whole class of bugs created by having N copies of one fact.
(Only `bt142_runner_service.py` did it right — env-driven. The inconsistency is
the smell.)

**Fix in stock-list2:** one async engine in `app/core/db.py`, built from the single
`Settings` source. No module constructs its own connection.

### 2. Giant files doing many things
- `agent/src/engine/request_batcher.py` — **3987 lines**
- `agent/src/engine/middleware.py` — 2819
- `agent/routers/auto_features.py` — 2802
- `agent/api_server.py` — was 4037 (split to ~1994, still large)
- `agent/cli.py` — 1761

Files this size can't be held in working memory, can't be reasoned about safely,
and accumulate unrelated responsibilities. **Fix:** hard <300 LOC-per-file rule
with single responsibility.

### 3. Configuration not centralized
`_ENV_CANDIDATES` in `providers/llm.py` loads the **first** `.env` found
(`~/.vibe-trading/.env`, then `agent/.env`, then `cwd/.env`) and stops. So the DB
vars living in the project-root `.env` were silently never loaded. **Fix in
stock-list2:** pydantic-settings as the single source; no scattered `load_dotenv`.

## Scope problems (value-for-maintenance is poor)

### 4. Auto-evolved bulk with low marginal value
- **420 skill directories** under `agent/src/skills/`, many duplicated (e.g.
  `skill_r120.py` exists both as a flat file and inside `skill-r120/`).
- 29 swarm presets, 18 governance ADRs, a full blue-green deploy machinery
  (`deploy.sh`, `blue-green.sh`, nginx templates), MCP server, CLI/TUI.
- 9 backtest engines.

Most of this is machine-generated "evolution" output. It inflates the codebase to
**~302K LOC** in `agent/` without proportional capability. **Decision:** drop it
from v1; ship 5–8 hand-written tools and one vectorized backtester instead.

### 5. Tests exist but the safety net was never used
229 backend test files, but `pytest` was in the optional `[dev]` group and the
default `uv sync` didn't install it — so the suite effectively never ran in this
environment. Frontend had **4** test files. **Fix in stock-list2:** `pytest` and
`vitest` are first-class from day one; every layer has tests.

### 6. Manifest gaps
`psycopg2` is imported by several modules but missing from `pyproject.toml`
dependencies. The runtime only worked because it got installed ad-hoc. **Fix in
stock-list2:** `uv lock` is the contract; nothing runs that isn't declared.

### 7. Pinned-below dependencies
`langgraph>=0.2.50,<0.3` blocks the 0.3 line. Combined with the langchain/langgraph
dependency tree (a large surface for a tool-calling agent), this is a maintenance
tax. **Decision for stock-list2:** drop langchain/langgraph entirely; talk to an
OpenAI-compatible endpoint directly with `httpx`. Far less surface area.

## Frontend problems

- Pages routinely 1000–1600 lines (`StockGraph.tsx` 1633, `StockDetail` 1412,
  `TechnicalIndicators` 1315, `Agent` 1234, `Settings` 1138).
- A monolithic 806-line `api.ts`.
- No state management (per-page `useState`) and almost no tests.

**Fix in stock-list2:** feature-folder structure, a module API layer, `zustand`
for client state, small typed components, vitest from the start.
