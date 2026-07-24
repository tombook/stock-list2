"""交易成本模型——commission + slippage + spread 三组件。

支持两种使用方式：
  1. 简单模式（向后兼容）：CostModel.from_bps(cost_bps) — 单一 bps 值
  2. 专业模式：CostModel(commission_bps=1, slippage_bps=2, spread_bps=1) — 分组件配置

在向量化引擎中，成本 = total_bps × 1e-4 × |仓位变化|。
未来可扩展为基于成交量的非线性滑点模型。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    """三组件交易成本模型。各组件以 bps（万分之一）计。"""

    commission_bps: float = 0.0
    slippage_bps: float = 0.0
    spread_bps: float = 0.0

    @property
    def total_bps(self) -> float:
        return self.commission_bps + self.slippage_bps + self.spread_bps

    @staticmethod
    def from_bps(cost_bps: float) -> CostModel:
        """从单一 bps 值创建（向后兼容旧 cost_bps 参数）。"""
        return CostModel(commission_bps=cost_bps)
