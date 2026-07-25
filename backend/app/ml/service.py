"""ML prediction service — AdaBoost classifier for direction prediction.

Walk-forward training: trains on historical data, predicts the probability
that the price will be higher in `horizon` bars. Returns feature importance
to explain which factors drive the prediction.

Key lesson from stock-ai-terminal: honest accuracy reporting (~57% is meaningful
edge over random 50%). The value is in explainability, not the prediction itself.
"""

from __future__ import annotations

import asyncio

import pandas as pd
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import accuracy_score

from app.backtest.service import _to_dataframe
from app.core.errors import DomainError
from app.marketdata import service as market_service
from app.ml.features import FEATURE_NAMES, build_features
from app.ml.models import FeatureImportance, PredictionResult


def _create_labels(df: pd.DataFrame, horizon: int) -> pd.Series:
    """Binary label: 1 if close[t+horizon] > close[t], else 0."""
    future = df["close"].shift(-horizon)
    return (future > df["close"]).astype(float)


def _train_and_predict(
    df: pd.DataFrame, horizon: int
) -> tuple[float, float, float, list[tuple[str, float]], float | None]:
    """Train AdaBoost, predict last bar. Returns (prob_up, direction,
    confidence, feature_importance, accuracy)."""
    features = build_features(df)
    labels = _create_labels(df, horizon)

    valid = features.dropna().index.intersection(labels.dropna().index)
    if len(valid) < 100:
        raise DomainError(f"insufficient data ({len(valid)} bars) for ML prediction")

    X = features.loc[valid, FEATURE_NAMES]
    y = labels.loc[valid]

    split = int(len(valid) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = AdaBoostClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    acc = float(accuracy_score(y_test, model.predict(X_test)))

    last_features = X.iloc[[-1]]
    prob_up = float(model.predict_proba(last_features)[0, 1])

    importances = sorted(
        zip(FEATURE_NAMES, model.feature_importances_, strict=True),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    direction = "up" if prob_up >= 0.5 else "down"
    confidence = max(prob_up, 1.0 - prob_up)

    return prob_up, direction, confidence, importances, acc


async def predict_direction(symbol: str, horizon: int = 5) -> PredictionResult:
    if horizon < 1 or horizon > 30:
        raise DomainError("horizon must be 1-30 bars")

    bars = await market_service.get_bars(symbol, "1d", 500)
    df = _to_dataframe(bars)

    if len(df) < 150:
        raise DomainError(f"insufficient history ({len(df)} bars), need 150+")

    prob_up, direction, confidence, importances, acc = await asyncio.to_thread(
        _train_and_predict, df, horizon
    )

    return PredictionResult(
        symbol=symbol.upper(),
        probability_up=round(prob_up, 4),
        predicted_direction=direction,
        confidence=round(confidence, 4),
        top_features=[
            FeatureImportance(name=name, importance=round(imp, 4)) for name, imp in importances
        ],
        horizon=horizon,
        accuracy=round(acc, 4) if acc is not None else None,
        source="adaboost",
    )
