"""ML prediction result model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FeatureImportance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    importance: float


class PredictionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    probability_up: float  # 0.0 to 1.0
    predicted_direction: str  # "up" or "down"
    confidence: float  # 0.5 to 1.0
    top_features: list[FeatureImportance]
    horizon: int  # prediction horizon in bars
    accuracy: float | None  # model accuracy on validation set
    source: str
