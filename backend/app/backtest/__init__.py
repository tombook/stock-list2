"""Backtest domain — vectorized engine + strategies + service entry."""

from app.backtest.service import run_backtest

__all__ = ["run_backtest"]
