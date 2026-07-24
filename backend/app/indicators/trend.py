"""趋势类指标：Parabolic SAR。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sar(
    bars: pd.DataFrame, af_step: float = 0.02, af_max: float = 0.2
) -> pd.Series:
    """Parabolic SAR——止损反转点。

    逐 bar 追踪趋势：上升趋势中 SAR 上移，下降趋势中 SAR 下移。
    加速因子 af 从 af_step 递增到 af_max。
    """
    high = bars["high"].values
    low = bars["low"].values
    n = len(high)

    if n == 0:
        return pd.Series([], dtype=float)

    sar_arr = np.zeros(n)
    ep = np.zeros(n)
    af = np.zeros(n)
    trend = np.ones(n)

    sar_arr[0] = low[0]
    ep[0] = high[0]
    af[0] = af_step

    for i in range(1, n):
        if trend[i - 1] == 1:
            sar_arr[i] = sar_arr[i - 1] + af[i - 1] * (ep[i - 1] - sar_arr[i - 1])
            sar_arr[i] = min(sar_arr[i], low[i - 1])
            if i > 1:
                sar_arr[i] = min(sar_arr[i], low[i - 2])
            if low[i] < sar_arr[i]:
                trend[i] = -1
                sar_arr[i] = ep[i - 1]
                ep[i] = low[i]
                af[i] = af_step
            else:
                trend[i] = 1
                if high[i] > ep[i - 1]:
                    ep[i] = high[i]
                    af[i] = min(af[i - 1] + af_step, af_max)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]
        else:
            sar_arr[i] = sar_arr[i - 1] + af[i - 1] * (ep[i - 1] - sar_arr[i - 1])
            sar_arr[i] = max(sar_arr[i], high[i - 1])
            if i > 1:
                sar_arr[i] = max(sar_arr[i], high[i - 2])
            if high[i] > sar_arr[i]:
                trend[i] = 1
                sar_arr[i] = ep[i - 1]
                ep[i] = high[i]
                af[i] = af_step
            else:
                trend[i] = -1
                if low[i] < ep[i - 1]:
                    ep[i] = low[i]
                    af[i] = min(af[i - 1] + af_step, af_max)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]

    return pd.Series(sar_arr, index=bars.index, name="sar")
