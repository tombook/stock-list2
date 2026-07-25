"""Strategy editor — validate + execute user-supplied strategy code.

User code must define a function: def strategy(bars: pd.DataFrame, **params) -> pd.Series[float]
The bars DataFrame has columns [ts, open, high, low, close, volume].
The function returns a position series where:
    0 = flat, 0 < v <= 1 = long, -1 <= v < 0 = short.

Safety layer:
  - AST parse + scan for banned imports / functions
  - Subprocess execution with timeout (cannot kill runaway loops in-process)
  - Wall-clock timeout enforced via asyncio.wait_for
"""

from __future__ import annotations

import ast
import asyncio
import json
import math
import sys

from app.core.errors import DomainError
from app.strategy_editor.schemas import (
    StrategyExecuteResponse,
    StrategyValidateResponse,
    ValidationIssue,
)

BANNED_IMPORTS = {"os", "subprocess", "shutil", "socket", "urllib", "requests", "httpx"}
BANNED_BUILTINS = {"exec", "eval", "compile", "__import__", "open"}

_RUNNER = """
import sys, json
import pandas as pd
import numpy as np

data = json.loads(sys.argv[1])
bars = pd.DataFrame(data['bars'])
params = data.get('params', {})
scope = {'bars': bars, 'pd': pd, 'np': np}
exec(data['code'], scope)
sig = scope['strategy'](bars, **params)
result = pd.Series(sig).fillna(0.0).astype(float).tolist()
out = {'equity_norm': result, 'n': len(bars)}
sys.stdout.write(json.dumps(out))
"""


def validate(code: str) -> StrategyValidateResponse:
    """Parse code with AST + scan for banned operations."""
    issues: list[ValidationIssue] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return StrategyValidateResponse(
            valid=False,
            issues=[ValidationIssue(line=exc.lineno or 0, message=f"SyntaxError: {exc.msg}")],
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BANNED_IMPORTS:
                    issues.append(
                        ValidationIssue(
                            line=node.lineno,
                            message=f"banned import: {alias.name}",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            module_name = (node.module or "").split(".")[0]
            if module_name in BANNED_IMPORTS:
                issues.append(
                    ValidationIssue(line=node.lineno, message=f"banned import: {node.module}")
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_BUILTINS:
                issues.append(
                    ValidationIssue(
                        line=node.lineno,
                        message=f"banned builtin: {node.func.id}",
                    )
                )

    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    has_strategy = any(f.name == "strategy" for f in funcs)
    if not has_strategy:
        issues.append(
            ValidationIssue(line=0, message="missing required function 'strategy(bars, **params)'")
        )

    return StrategyValidateResponse(valid=not issues, issues=issues)


async def execute(code: str, bars_data: list[dict], params: dict | None = None) -> dict:
    """Execute user code in a subprocess with timeout. Returns the signal series."""
    payload = json.dumps({"code": code, "bars": bars_data, "params": params or {}})

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        _RUNNER,
        payload,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    except TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise DomainError("strategy execution timed out (10s)") from exc

    if proc.returncode != 0:
        raise DomainError(f"strategy execution failed: {stderr.decode()[:500]}")

    return json.loads(stdout.decode())


def _bars_to_df(bars: list[dict]) -> list[dict]:
    """Convert Bar-like dicts to JSON-serializable list."""
    return [
        {
            "ts": b["ts"].isoformat() if hasattr(b.get("ts"), "isoformat") else b["ts"],
            "open": b["open"],
            "high": b["high"],
            "low": b["low"],
            "close": b["close"],
            "volume": b.get("volume"),
        }
        for b in bars
    ]


def compute_metrics(signal: list[float], close: list[float]) -> dict:
    """Compute total return and Sharpe from signal + close price series."""
    if len(signal) != len(close) or len(signal) < 2:
        return {"total_return": 0.0, "sharpe": 0.0}

    closes = [c for c in close if isinstance(c, (int, float))]
    if len(closes) < 2:
        return {"total_return": 0.0, "sharpe": 0.0}

    pos = [s if s is not None else 0.0 for s in signal]
    pos = [0.0 if math.isnan(p) else p for p in pos]

    returns = [pos[i] * (closes[i] / closes[i - 1] - 1.0) for i in range(1, len(closes))]
    if not returns:
        return {"total_return": 0.0, "sharpe": 0.0}

    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(var) if var > 0 else 0.0
    sharpe = (mean / std) * math.sqrt(252) if std > 1e-10 else 0.0

    total_return = (closes[-1] - closes[0]) / closes[0]
    return {"total_return": round(total_return, 6), "sharpe": round(sharpe, 4)}


async def run_strategy(req_code: str, bars: list[dict]) -> StrategyExecuteResponse:
    """Validate, execute in subprocess, compute metrics."""
    validation = validate(req_code)
    if not validation.valid:
        return StrategyExecuteResponse(
            equity=[],
            n_bars=0,
            total_return=0.0,
            Sharpe=0.0,
            error=f"validation failed: {validation.issues[0].message}"
            if validation.issues
            else "validation failed",
        )

    bars_data = _bars_to_df(bars)
    closes = [b["close"] for b in bars]

    try:
        result = await execute(req_code, bars_data)
        signal = result["equity_norm"]
    except Exception as exc:
        return StrategyExecuteResponse(
            equity=[],
            n_bars=0,
            total_return=0.0,
            Sharpe=0.0,
            error=str(exc),
        )

    metrics = compute_metrics(signal, closes)
    bars_reversed = list(zip(bars_data, signal, strict=True))
    equity_curve = [{"ts": b["ts"], "equity": sig} for b, sig in bars_reversed]
    return StrategyExecuteResponse(
        equity=equity_curve,
        n_bars=result["n"],
        total_return=metrics["total_return"],
        Sharpe=metrics["sharpe"],
    )
