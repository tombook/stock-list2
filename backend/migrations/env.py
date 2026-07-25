"""Alembic environment — async, wired to the app's single Settings + Base.metadata.

The DSN comes from app.core.settings (never duplicated). Importing the runs model
ensures its table is registered on Base.metadata before autogenerate compares.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.db import Base  # 导入应用唯一的 Declarative 基类
from app.core.settings import get_settings
from app.runs import models as _runs_models  # noqa: F401 — 注册 runs 表到 metadata
from app.watchlist import models as _watchlist_models  # noqa: F401 — 注册 watchlist 表
from app.marketdata.bar_cache import BarCache as _bar_cache_model  # noqa: F401
from app.trading.models import Account as _trading_account  # noqa: F401
from app.trading.models import Order as _trading_order  # noqa: F401
from app.trading.models import Position as _trading_position  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection."""
    context.configure(
        url=get_settings().db_dsn,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine from Settings and run migrations against the live DB."""
    connectable = async_engine_from_config(
        {"sqlalchemy.url": get_settings().db_dsn},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
