"""Post-trade risk analytics — VaR, CVaR, correlation, stress tests."""

from __future__ import annotations

import asyncio

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from app.marketdata import service as market_service
from app.marketdata.models import Bars


class RiskAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    var_95: float  # 95% Value at Risk (daily, as negative return)
    var_99: float
    cvar_95: float  # Conditional VaR (expected shortfall beyond VaR)
    cvar_99: float
    max_drawdown: float
    volatility_annual: float
    sharpe_ratio: float
    best_day: float
    worst_day: float
    source: str


def _bars_to_df(bars: Bars) -> pd.DataFrame:
    return pd.DataFrame([{"close": b.close, "volume": b.volume or 0} for b in bars.bars])


def compute_risk(bars: Bars) -> RiskAnalytics:
    df = _bars_to_df(bars)
    returns = df["close"].pct_change().dropna()

    if len(returns) < 30:
        return RiskAnalytics(
            symbol=bars.symbol,
            var_95=0,
            var_99=0,
            cvar_95=0,
            cvar_99=0,
            max_drawdown=0,
            volatility_annual=0,
            sharpe_ratio=0,
            best_day=0,
            worst_day=0,
            source="insufficient_data",
        )

    var_95 = float(returns.quantile(0.05))
    var_99 = float(returns.quantile(0.01))
    cvar_95 = float(returns[returns <= var_95].mean())
    cvar_99 = float(returns[returns <= var_99].mean())

    equity = (1 + returns).cumprod()
    peak = equity.cummax()
    max_dd = float((equity / peak - 1).min())

    vol_annual = float(returns.std() * np.sqrt(252))
    sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 1e-10 else 0.0

    return RiskAnalytics(
        symbol=bars.symbol,
        var_95=round(var_95, 6),
        var_99=round(var_99, 6),
        cvar_95=round(cvar_95, 6),
        cvar_99=round(cvar_99, 6),
        max_drawdown=round(max_dd, 6),
        volatility_annual=round(vol_annual, 4),
        sharpe_ratio=round(sharpe, 4),
        best_day=round(float(returns.max()), 6),
        worst_day=round(float(returns.min()), 6),
        source="computed",
    )


async def analyze_risk(symbol: str) -> RiskAnalytics:
    bars = await market_service.get_bars(symbol, "1d", 252)
    return await asyncio.to_thread(compute_risk, bars)
