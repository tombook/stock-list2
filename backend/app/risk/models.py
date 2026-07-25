"""Risk check result model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RiskViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: str
    message: str
    severity: str  # "block" or "warn"


class RiskCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    violations: list[RiskViolation]
