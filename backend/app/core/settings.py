"""Application settings — single source of truth for all runtime config.

12-factor: everything comes from the environment (optionally an .env file).
No other module reads os.environ directly for config; it imports get_settings().
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8900
    log_level: str = "INFO"

    # PostgreSQL (async; asyncpg driver)
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "stocklist2"
    db_user: str = "postgres"
    db_pass: str = ""

    # Redis is a soft dependency — the app runs without it.
    redis_url: str | None = "redis://localhost:6379/0"

    # API auth: when set, all API routes require X-API-Key header.
    # Empty value disables auth (dev mode only).
    api_key: str = ""

    # CORS: comma-separated origins; empty == allow all (dev default).
    cors_origins: str = ""

    # LLM provider config (any OpenAI-compatible chat completions endpoint).
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_temperature: float = 0.0
    llm_timeout: float = 60.0
    agent_max_iterations: int = 8

    # Alpaca (optional — for real-time data + paper trading)
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""

    @property
    def db_dsn(self) -> str:
        from urllib.parse import quote_plus

        user = quote_plus(self.db_user)
        password = quote_plus(self.db_pass)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
