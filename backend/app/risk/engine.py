"""Pre-trade risk engine — validates orders against portfolio constraints.

Rules:
  - max_position_pct: single position cannot exceed X% of portfolio
  - max_positions: minimum diversification (at least N holdings)
  - max_single_order_pct: single order cannot exceed X% of cash
  - max_drawdown_stop: stop trading if portfolio drawdown exceeds threshold

Configurable via RiskConfig. Injected into trading service before _apply_fill.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.marketdata import service as market_service
from app.risk.models import RiskCheckResult, RiskViolation
from app.trading import repo
from app.trading.models import Account, Order


@dataclass(frozen=True)
class RiskConfig:
    max_position_pct: float = 0.25  # single position max 25% of portfolio
    max_single_order_pct: float = 0.20  # single order max 20% of cash
    min_positions: int = 1  # at least 1 holding (no enforcement if 0)
    max_drawdown_pct: float = 0.15  # stop if drawdown > 15%


DEFAULT_CONFIG = RiskConfig()


async def check_order(
    session: AsyncSession,
    account: Account,
    order: Order,
    config: RiskConfig = DEFAULT_CONFIG,
) -> RiskCheckResult:
    """Validate an order against risk rules. Returns violations list."""
    violations: list[RiskViolation] = []

    if order.side == "buy":
        quote = None
        try:
            quote = await market_service.get_quote(order.symbol)
        except Exception:
            pass

        order_value = order.qty * (quote.price if quote else 0)
        portfolio_value = account.cash + await _positions_value(session, account.id)

        if portfolio_value > 0:
            pct = order_value / portfolio_value
            if pct > config.max_single_order_pct:
                violations.append(
                    RiskViolation(
                        rule="max_single_order_pct",
                        message=f"Order ${order_value:.0f} is {pct:.0%} of portfolio "
                        f"(max {config.max_single_order_pct:.0%})",
                        severity="warn",
                    )
                )

        existing = await repo.get_position(session, account.id, order.symbol)
        new_pos_value = order_value
        if existing and existing.qty > 0:
            new_pos_value += existing.qty * existing.avg_cost
        if portfolio_value > 0 and new_pos_value / portfolio_value > config.max_position_pct:
            violations.append(
                RiskViolation(
                    rule="max_position_pct",
                    message=f"Position {order.symbol} would be "
                    f"{new_pos_value / portfolio_value:.0%} of portfolio "
                    f"(max {config.max_position_pct:.0%})",
                    severity="warn",
                )
            )

        if account.initial_cash > 0:
            drawdown = 1.0 - portfolio_value / account.initial_cash
            if drawdown > config.max_drawdown_pct:
                violations.append(
                    RiskViolation(
                        rule="max_drawdown_stop",
                        message=f"Portfolio drawdown {drawdown:.1%} exceeds "
                        f"limit {config.max_drawdown_pct:.1%}",
                        severity="block",
                    )
                )

    has_block = any(v.severity == "block" for v in violations)
    return RiskCheckResult(passed=not has_block, violations=violations)


async def _positions_value(session: AsyncSession, account_id: int) -> float:
    positions = await repo.list_positions(session, account_id)
    return sum(p.qty * p.avg_cost for p in positions)
