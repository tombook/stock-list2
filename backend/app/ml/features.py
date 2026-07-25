"""Feature engineering — converts OHLCV bars into ML features.

Uses the indicator engine (app/indicators/) to compute technical indicators
that serve as model features. Walk-forward safe: features at bar t use only
data available at bar t's close.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.indicators import ma, momentum, volatility


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute a feature matrix from OHLCV bars. Returns aligned DataFrame."""
    features = pd.DataFrame(index=df.index)

    features["ret_1d"] = df["close"].pct_change(1)
    features["ret_5d"] = df["close"].pct_change(5)
    features["ret_10d"] = df["close"].pct_change(10)

    features["rsi_14"] = momentum.rsi(df, 14)
    features["roc_12"] = momentum.roc(df, 12)
    features["cci_20"] = momentum.cci(df, 20)

    features["atr_14"] = volatility.atr(df, 14)
    features["volatility_20"] = df["close"].pct_change().rolling(20).std()

    features["sma_10_dist"] = df["close"] / ma.sma(df, 10) - 1
    features["sma_20_dist"] = df["close"] / ma.sma(df, 20) - 1
    features["sma_50_dist"] = df["close"] / ma.sma(df, 50) - 1

    features["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

    features["high_low_range"] = (df["high"] - df["low"]) / df["close"]

    features = features.replace([np.inf, -np.inf], np.nan)
    return features


FEATURE_NAMES = [
    "ret_1d",
    "ret_5d",
    "ret_10d",
    "rsi_14",
    "roc_12",
    "cci_20",
    "atr_14",
    "volatility_20",
    "sma_10_dist",
    "sma_20_dist",
    "sma_50_dist",
    "volume_ratio",
    "high_low_range",
]
