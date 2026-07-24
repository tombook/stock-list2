# ROADMAP v2 — 基于 US 量化专家经验的功能设计

> 参照平台：QuantConnect/LEAN · Alpaca · Quantopian(Pyfolio/Alphalens) · Interactive Brokers
> · TradingView 社区（1216 Pine 指标） · GitHub AI 美股项目（TradingAgents / FinGPT / QuantAgent）
>
> 核心原则：**不追求 feature parity**，只取每个平台被实战验证过的高杠杆功能，按「解锁后续能力的优先级」排序。

---

## 知识来源

### 量化平台（Phase 1-7）
| 平台 | 参照价值 |
|------|---------|
| QuantConnect/LEAN | 事件驱动引擎 · Algorithm Framework · 参数优化 · 多资产组合 |
| Alpaca | Paper trading · 订单类型 · WebSocket 实时流 |
| Quantopian/Pyfolio | Tear sheet 标准 · 因子分析 · 回撤分析 |
| Interactive Brokers | 专业 broker 集成 |

### TradingView 社区（Phase 8）
- `/root/stock-list/pine_sources/`：**1216 个** TradingView 社区 Pine 脚本（原始下载）
- `/root/stock-list/scripts/import_indicator_registry.py`：**47 个核心指标**的完整分类体系（10 类，含信号逻辑 + 参数定义 + 中文说明）
- `/root/stock-list/agent/src/skills/tradingview-analysis/indicators_batch*.py`：8 批已实现的 Python 计算代码
- `/root/stock-list/pine_output/`：14 个精选复合指标（factor / pattern / donchian 等）

### GitHub AI 美股项目（Phase 9）
| 项目 | Stars | 核心能力 | 借鉴点 |
|------|-------|---------|--------|
| TradingAgents | 94K | 多 Agent LLM 交易框架 | 6 专业 Agent + 辩论机制 + 风险否决 |
| Vibe-Trading | 27K | 全栈交易 Agent | 460 Alpha Zoo 因子 · 分层归因 · 蒙特卡洛 |
| FinGPT | 21K | 金融大语言模型 | 情绪分析 · RAG · FinBERT |
| QuantAgent | 2.8K | 多模态图表分析 | LLM 看图识别形态 · 趋势通道 |
| stock-ai-terminal | — | AdaBoost ML 预测 | 特征重要性排名 · 自动重训 · 可解释性 |
| StockPilotX | 83 | 8 Agent 辩论系统 | RAG · 规则引擎降级 · 99.55% 可用性 |
| SentXStock | — | 情绪驱动交易 | 3 级情绪管线（FinBERT→LLM→VADER） |

---

## 当前能力基线（2026-07-24）

| 域 | 已有 | 缺口 |
|----|------|------|
| 数据 | yfinance quote/bars/fundamentals | 无调整后价格、无公司行动、无另类数据 |
| 引擎 | 单标的·long-only·0/1 仓位·固定 bps 成本 | 无滑点、无组合、无空头、无 sizing |
| 指标 | return·CAGR·Sharpe·MaxDD·win_rate·n_trades | 无 Sortino·Calmar·rolling Sharpe·tear sheet |
| Agent | 4 工具（quote/bars/backtest/fundamentals） | 无 compare·无 screener·无 portfolio 分析 |
| 持久化 | runs + watchlist 两表 | 无 positions·orders·transactions |
| 执行 | 无 | 无 paper trading·无 broker 集成 |
| 前端 | 7 页（Home/Markets/Analyze/Backtest/Runs/Watchlist） | 无 portfolio 视图·无 tear sheet |

---

## Phase 1 — 回测引擎升级（核心生产力跃升）

> **专家共识**：一个不建模交易成本的回测引擎是"玩具"。QuantConnect 的核心卖点就是
> "point-in-time, fee, slippage, and spread-adjusted backtesting"。这是从"能跑"到"可信"的分水岭。

### 1.1 现实交易成本模型（Transaction Cost Modeling）

当前：`cost = cost_bps * turnover`。一个标量，不含滑点、不含买卖价差。

**设计**：

```
Total Cost = Commission + Slippage + Spread Impact
```

| 组件 | 模型 | 实现 |
|------|------|------|
| Commission | 固定 per-share 或 per-trade（如 $0.005/share, Alpaca 模式） | `CostModel.commission(qty, price)` |
| Slippage | 线性模型 `slippage_bps * sqrt(trade_volume / adv)` — 大单影响更大 | 基于 bars 的 volume 近似 ADV |
| Spread | 买卖价差固定 bps（如 1-5bps 美股大盘股） | `CostModel.spread_bps` |

- `app/backtest/cost_model.py`（新）— `CostModel` dataclass，可注入引擎
- 引擎 `engine.run()` 接受 `cost_model: CostModel` 替代 `cost_bps: float`
- 向后兼容：`cost_bps` 参数自动包装为简单 `CostModel`

### 1.2 仓位管理升级（Position Sizing）

当前：`signal → position ∈ {0, 1}`。

**设计**：信号扩展为连续权重 `-1.0 ~ +1.0`：

| 维度 | 当前 | 升级后 |
|------|------|--------|
| 方向 | long-only | long + short |
| 权重 | binary 0/1 | continuous -1.0~1.0 |
| Sizing | 固定满仓 | fixed_fractional · kelly_fraction · vol_target |

- `app/backtest/position_sizing.py`（新）— sizing 策略函数
- 策略函数签名从 `→ pd.Series[int]` 改为 `→ pd.Series[float]`
- 引擎支持做空：负仓位 × 下跌 = 正收益

### 1.3 组合回测（Multi-Asset Portfolio Backtesting）

当前：单标的。QuantConnect 核心能力之一是"thousands of securities portfolio"。

**设计**：

| 概念 | 说明 |
|------|------|
| Universe | 股票池（如 watchlist 中的全部标的、或 SPY 成分股） |
| 组合信号 | `Dict[symbol, weight]` 每根 bar |
| 组合收益 | `Σ(weight_i * return_i) - cost` |
| 再平衡 | 按时间频率（每日/每周/每月）或阈值触发 |

- `app/backtest/portfolio_engine.py`（新）— 多标的向量化引擎
- `PortfolioBacktestRequest` schema：`symbols: list[str]`, `rebalance: str`, `weights: dict | strategy`
- `POST /api/backtest/portfolio`（新端点）

### 1.4 参数优化（Parameter Optimization）

QuantConnect："run thousands of full backtests, visualize on heatmaps"。

**设计**：

| 功能 | 说明 |
|------|------|
| Grid Search | 网格化参数空间，并行跑 N 次回测 |
| 结果 | 参数 → metrics 矩阵 |
| 可视化 | 热力图（参数二维 × Sharpe/Return 着色） |
| 持久化 | `optimization_runs` 表 |

- `app/backtest/optimizer.py`（新）— 参数空间定义 + 并行执行
- `POST /api/backtest/optimize`（新端点）— 接受参数范围，返回结果矩阵
- 前端：热力图组件（参数网格 × 指标着色）

---

## Phase 2 — 分析能力深化（Tear Sheet 标准）

> **专家共识**：Pyfolio 的 tear sheet 是美国量化圈的事实标准。没有它，策略评估就只是
> "看个总收益"。6 个指标 → 全景分析报告。

### 2.1 扩展指标（Extended Metrics）

当前 6 个 → 补齐到专业级：

| 指标 | 公式 | 为什么 |
|------|------|--------|
| Sortino Ratio | `mean(downside_returns) / downside_std * √ppy` | 只惩罚下行波动，比 Sharpe 更合理 |
| Calmar Ratio | `CAGR / |MaxDD|` | 收益/回撤比，风险调整收益 |
| Volatility | `std(returns) * √ppy` | 年化波动率 |
| Value at Risk (VaR) | 收益分布的 5% 分位数 | "最坏情况下亏多少" |
| Beta | `cov(strategy, market) / var(market)` | 对市场的敏感度 |
| Alpha | `strategy_return - beta * market_return` | 超额收益 |
| Profit Factor | `gross_profit / gross_loss` | 盈亏比 |
| Avg Trade Duration | 平均持仓天数 | 交易频率特征 |
| Max Consecutive Losses | 连续亏损笔数 | 心理压力测试 |

- `app/backtest/metrics.py` 扩展（增量函数，不重写现有）

### 2.2 Tear Sheet 可视化（Pyfolio-style Charts）

| 图表 | 说明 |
|------|------|
| 滚动 Sharpe | 126 日窗口滚动计算，看策略稳定性 |
| 水下曲线（Underwater） | 回撤深度随时间变化，直观看到"套了多久" |
| 月度收益热力图 | 年×月矩阵，绿色盈利红色亏损 |
| 回撤期 Top 5 | 最深 5 次回撤的起止日期和持续时间 |
| 滚动 Beta | 对 benchmark（SPY）的动态 Beta |
| 收益分布 | 直方图 + QQ Plot |

- 前端 `components/charts/`（新组件）：
  - `RollingSharpeChart.tsx`
  - `UnderwaterChart.tsx`
  - `MonthlyHeatmap.tsx`
  - `DrawdownTable.tsx`
- 组合为 `TearSheet.tsx` 组件，嵌入 RunDetailPage

### 2.3 Benchmark 对比

当前无基准对比。

**设计**：
- 回测请求支持 `benchmark: str`（如 "SPY"）
- 引擎同时跑 benchmark 的 buy_hold
- 返回 `benchmark_equity` 和 `alpha`（超额收益曲线）
- 前端：双线 equity 图（策略 vs benchmark）

---

## Phase 3 — 数据层深化（从免费到专业）

> **专家共识**：QuantConnect 的核心壁垒是 400TB 数据。
> 数据质量决定策略质量——garbage in, garbage out。

### 3.1 调整后价格（Adjusted Prices）

当前 yfinance `history()` 返回原始价格。分拆/分红会导致虚假跳价。

**设计**：
- `bars` 模型加 `adj_close` 字段
- 数据源统一返回 `auto_adjust=True` 的调整后价格
- 回测引擎默认使用调整后价格

### 3.2 公司行动追踪（Corporate Actions）

| 事件 | 影响 |
|------|------|
| Stock Split | 股价减半，股数翻倍 |
| Dividend | 除权日股价下跌 |
| Spin-off | 拆分出新公司 |

**设计**：
- `app/marketdata/actions.py`（新）— `get_actions(symbol) → list[CorporateAction]`
- yfinance `Ticker.actions` / `Ticker.splits` / `Ticker.dividends`
- 前端：MarketsPage 增加公司行动历史卡片

### 3.3 第三方数据源接入

| 数据源 | 类型 | 接入方式 |
|--------|------|----------|
| Alpaca Market Data | 实时 + 历史 OHLCV | REST API + WebSocket |
| akshare | A股数据 | Python lib → asyncio.to_thread |
| FRED | 宏观经济数据（利率/GDP/CPI） | REST API |
| Stooq | 免费历史数据 | CSV 下载 |

**设计**：
- 每个 source 实现 `DataSource` protocol（已有抽象）
- 注册到 `registry._SOURCES` fallback chain
- Settings 加各 source 的 API key 配置

### 3.4 数据本地化缓存（Historical Data Store）

yfinance 每次调用都走网络。回测参数优化跑 1000 次会请求 1000 次。

**设计**：
- `app/marketdata/store.py`（新）— 本地 PG 存储历史 bars
- `bars_cache` 表：`(symbol, timeframe, ts, ohlcv)` 唯一索引
- 首次请求写入 PG，后续直接读库
- 定时同步任务（Celery/APScheduler 或简单 cron）

---

## Phase 4 — 执行层（Paper Trading）

> **专家共识**：Alpaca 的 paper trading 是"从回测到实盘的桥梁"。
> 没有执行层的回测平台永远只是研究工具，不是交易平台。

### 4.1 Paper Trading Engine

**设计**：

| 组件 | 说明 |
|------|------|
| 虚拟账户 | $100k 初始（Alpaca 模式），`accounts` 表 |
| 订单管理 | 创建/取消/查询订单，`orders` 表 |
| 持仓管理 | 自动更新持仓和 PnL，`positions` 表 |
| 成交模拟 | 基于实时 quote 判断是否可成交（NBBO 模式） |
| 现金管理 | 买入扣款/卖出入账，margin 计算 |

- `app/trading/`（新域）— paper trading 核心逻辑
- `POST /api/trading/orders` — 下单
- `GET /api/trading/positions` — 查持仓
- `GET /api/trading/account` — 查账户

### 4.2 订单类型

| 类型 | 说明 |
|------|------|
| Market | 按当前价成交 |
| Limit | 达到限价才成交 |
| Stop | 触发价后变市价单 |
| Stop Limit | 触发价后变限价单 |
| Trailing Stop | 动态跟踪止损 |

### 4.3 实时数据流（WebSocket）

- `app/api/stream.py`（新）— WebSocket endpoint
- 推送：实时报价、订单状态更新、持仓 PnL 变化
- 前端：WebSocket hook，实时更新 Dashboard

### 4.4 Broker 集成

| Broker | API | 优先级 |
|--------|-----|--------|
| Alpaca | REST + WS，免费 paper | P0 |
| Interactive Brokers | TWS API / IB Gateway | P1 |
| (其他) | — | P2 |

- `app/trading/brokers/`（新）— broker 适配层
- `Broker` protocol：`place_order / cancel_order / get_positions / stream_quotes`

---

## Phase 5 — 风险管理（Risk Management）

> **专家共识**：LEAN 的 Algorithm Framework 把 Risk Management 作为独立层。
> "Adjust position sizes and manage post-trade risk with plug-in risk models."

### 5.1 事前风险控制（Pre-trade Risk）

| 规则 | 说明 |
|------|------|
| Max Position Size | 单标的最大仓位占比（如 25%） |
| Max Sector Exposure | 单行业最大暴露（如 40%） |
| Max Portfolio Beta | 组合 Beta 上限（如 1.2） |
| Max Drawdown Stop | 回撤超阈值自动停止（如 -15%） |
| Concentration Limit | 持仓数下限（如至少 10 只） |

- `app/risk/`（新域）— 风险规则引擎
- 在 paper trading 下单前校验

### 5.2 事后风险分析（Post-trade Risk Analytics）

| 指标 | 说明 |
|------|------|
| VaR (95%/99%) | 在 95%/99% 置信下最大亏损 |
| CVaR / Expected Shortfall | 超过 VaR 时的平均亏损 |
| Stress Test | 历史极端场景回测（2008、2020-COVID） |
| Correlation Matrix | 持仓间相关性矩阵 |
| Factor Exposure | 对 Fama-French 因子的暴露度 |

---

## Phase 6 — Agent 智能升级

### 6.1 工具扩展

| 工具 | 用途 |
|------|------|
| `compare_stocks` | 多股并排指标对比 |
| `screen_stocks` | 按条件筛选（PE<20, sector=tech, ...） |
| `get_portfolio_analysis` | 分析当前持仓的风险/收益 |
| `optimize_strategy` | 自动参数寻优 |
| `get_news` | 新闻情绪（接入新闻 API） |
| `get_macro` | 宏观数据（利率/CPI/GDP via FRED） |

### 6.2 Agent 多轮推理增强

| 能力 | 说明 |
|------|------|
| Streaming final answer | 最终回答流式输出（当前一次性返回） |
| Tool parallelism | 多工具并行调用（当前串行） |
| Context memory | 对话记忆（跨轮上下文） |
| Strategy suggestion | 根据基本面自动建议策略 |

---

## Phase 7 — 前端体验升级

### 7.1 组合管理面板

| 页面 | 功能 |
|------|------|
| Portfolio Dashboard | 持仓总览、当日 PnL、资产配置饼图 |
| Positions Table | 持仓明细、实时 PnL、快速下单 |
| Order History | 订单历史、成交记录 |

### 7.2 高级图表

| 图表 | 说明 |
|------|------|
| Candlestick + Indicator overlay | RSI / MACD / Bollinger Bands 叠加 |
| Volume Profile | 价格-成交量分布 |
| Factor Attribution | 收益归因分解 |
| Efficient Frontier | 马科维茨有效前沿可视化 |

### 7.3 策略编辑器

- 在线编辑策略 Python 代码（CodeMirror）
- 回测 → 优化 → paper trade 一键流程
- 版本管理（git-integrated）

---

## 优先级矩阵（专家排序）

| Phase | 域 | 杠杆 | 复杂度 | 建议优先级 |
|-------|-----|------|--------|-----------|
| **1.1** | 交易成本模型 | 🔴 极高 | 低 | **立即** |
| **1.2** | 仓位管理升级 | 🔴 极高 | 中 | **立即** |
| **2.1** | 扩展指标（Sortino/Calmar/VaR） | 🟡 高 | 低 | **立即** |
| **3.1** | 调整后价格 | 🟡 高 | 低 | **立即** |
| **8.1** | 47 指标计算引擎 | 🔴 极高 | 中 | **立即** |
| **8.2** | 指标→信号生成器 | 🟡 高 | 低 | **立即** |
| **2.2** | Tear Sheet 可视化 | 🟡 高 | 中 | 紧接 |
| **2.3** | Benchmark 对比 | 🟡 高 | 低 | 紧接 |
| **3.4** | 数据本地化缓存 | 🟡 高 | 中 | 紧接 |
| **8.3** | 前端指标叠加系统 | 🟡 高 | 中 | 紧接 |
| **9.2** | 情绪分析流水线 | 🟡 高 | 中 | 紧接 |
| **9.1** | 多 Agent 分析框架 | 🔴 极高 | 高 | 中期 |
| **1.3** | 组合回测 | 🟠 中高 | 高 | 中期 |
| **1.4** | 参数优化 | 🟠 中高 | 中 | 中期 |
| **9.4** | 多 Agent 辩论机制 | 🟠 中高 | 中 | 中期 |
| **8.4** | 指标组合扫描器 | 🟠 中 | 中 | 中期 |
| **4.1** | Paper Trading | 🟠 中 | 高 | 中期 |
| **3.2** | 公司行动 | 🟢 中 | 低 | 中期 |
| **3.3** | 第三方数据源 | 🟢 中 | 中 | 中期 |
| **7.1** | 组合管理面板 | 🟢 中 | 中 | 中期 |
| **9.3** | ML 预测引擎 | 🟡 高 | 中 | 中期 |
| **5.1** | 事前风险控制 | 🟢 中 | 中 | 后期 |
| **5.2** | 事后风险分析 | 🟢 中 | 中 | 后期 |
| **4.2** | 订单类型 | 🟡 高 | 中 | 后期 |
| **4.3** | 实时数据流 | 🟡 高 | 中 | 后期 |
| **9.5** | RAG 知识库 | 🟡 高 | 高 | 后期 |
| **7.2** | 高级图表 | 🟢 低 | 中 | 后期 |
| **9.6** | LLM 图表形态识别 | 🟢 中 | 中 | 后期 |
| **7.3** | 策略编辑器 | 🟢 低 | 高 | 远期 |
| **6.2** | Agent 推理增强 | 🟢 低 | 中 | 远期 |
| **4.4** | Broker 集成 | 🟢 低 | 高 | 远期 |

---

## Phase 8 — 技术指标库（TradingView 社区精华）

> **来源**：`/root/stock-list/pine_sources/`（1216 个社区 Pine 脚本）+ `/root/stock-list/scripts/import_indicator_registry.py`
> （47 个指标完整分类体系）+ `agent/src/skills/tradingview-analysis/indicators_batch*.py`（8 批已实现计算）
>
> **专家共识**：TradingView 社区有数十万指标，但 90% 是变体。原项目已筛选出 47 个核心指标并
> 建立了分类体系（Moving Averages / Momentum / Volatility / Volume / Channel / Directional 等 10 类）。
> 我们移植这个分类体系，不搬 1216 个 Pine 脚本（那是膨胀源）。

### 8.1 核心指标计算引擎（47 指标 → Python 向量化）

将原项目的指标分类体系移植为纯 pandas/numpy 向量化计算，分 10 类：

| 类别 | 指标 | 当前状态 |
|------|------|---------|
| **Moving Averages** | SMA, EMA, WMA, RMA, HMA, ALMA, SWMA, TEMA, DEMA, LinReg | 仅 PriceChart 有 SMA 叠加 |
| **Momentum** | RSI, MACD, Stoch, ROC, CCI, MOM, WPR, TSI, Change, Rising, Falling | 无 |
| **Volatility** | ATR, Stdev, TR, SuperTrend, Bollinger Bands, Variance | 无 |
| **Volume** | VWAP, VWMA, MFI, OBV | 无 |
| **Channel** | Donchian, Highest, Lowest | 无 |
| **Directional** | ADX, DMI | 无 |
| **Pivot Points** | PivotHigh, PivotLow | 无 |
| **Signal** | Crossover, Crossunder, Cross | 无 |
| **Statistical** | PercentRank, Correlation | 无 |
| **Trend** | SAR (Parabolic SAR) | 无 |

**设计**：

```
app/indicators/
  __init__.py
  ma.py          # 移动平均线类（10 种）
  momentum.py    # 动量类（11 种）
  volatility.py  # 波动率类（6 种）
  volume.py      # 成交量类（4 种）
  channel.py     # 通道类（3 种）
  directional.py # 方向运动类（2 种）
  pivot.py       # 枢轴点类（2 种）
  signal.py      # 交叉信号类（3 种）
  statistical.py # 统计类（2 种）
  trend.py       # 趋势类（1 种：SAR）
  registry.py    # 统一注册表（指标名 → 函数）
```

每个函数签名统一：`def indicator_name(bars: pd.DataFrame, **params) -> pd.Series`
注册表模式与 `strategies.py` 的 `STRATEGIES` 一致。

### 8.2 指标 → 信号生成器

每个指标附带信号逻辑（原项目 `import_indicator_registry.py` 已有完整定义）：

| 指标 | 信号逻辑（来自原项目） |
|------|----------------------|
| RSI | `<30 超卖反弹=买入；>70 超买回落=卖出；背离=强信号` |
| MACD | `线上穿信号线=买入；下穿=卖出；零轴上方=多头` |
| Bollinger | `触及下轨=超卖买入；触及上轨=超买卖出；收口=变盘前兆` |
| SuperTrend | `价格在 SuperTrend 上方=多头；下方=空头` |
| VWAP | `价格>VWAP=多头偏向；<VWAP=空头偏向` |
| ADX | `>25=强趋势；<20=无趋势（震荡）；配合 DI+/DI- 判方向` |

- `app/indicators/signals.py`（新）— 每个指标 → `SignalSpec(buy_condition, sell_condition, strength)`

### 8.3 前端指标叠加系统

当前 PriceChart 仅支持 SMA 叠加。扩展为多指标叠加：

| 功能 | 说明 |
|------|------|
| 指标选择器 | 下拉选择指标 + 参数配置（如 RSI length=14） |
| 主图叠加 | SMA/EMA/Bollinger/SuperTrend/VWAP 叠加在蜡烛图上 |
| 副图面板 | RSI/MACD/Stoch/ADX 独立副图（PriceChart 下方） |
| 信号标记 | 在图上标记买卖信号点（▲买入 ▼卖出） |

- 前端 `components/charts/`：
  - `IndicatorPanel.tsx`（新）— 副图容器
  - `RSIPanel.tsx`, `MACDPanel.tsx`（新）— 独立副图
  - 扩展 `PriceChart.tsx` 支持多 overlay 线

### 8.4 指标组合扫描器

原项目有 `backtest_indicator_combos.py`——回测指标组合。

**设计**：
- `POST /api/scan`（新端点）— 给定指标条件组合，扫描全市场匹配标的
- 例：`RSI < 30 AND MACD 金叉 AND 价格 > VWAP` → 返回匹配股票列表
- 前端：扫描器页面（条件构建器 + 结果表）

---

## Phase 9 — AI 分析能力（GitHub AI 美股项目精华）

> **来源**：TradingAgents (94K⭐) · FinGPT (21K⭐) · Vibe-Trading (27K⭐) · QuantAgent (2.8K⭐) ·
> stock-ai-terminal · StockPilotX · SentXStock
>
> **专家共识**：AI 在交易中的价值不在"预测涨跌"（准确率仅 ~57%），而在**多维度分析
> + 可解释性 + 情绪量化**。TradingAgents 的多 Agent 辩论模式是当前最佳实践。

### 9.1 多 Agent 分析框架（TradingAgents 模式）

当前 `/api/analyze` 是单 Agent + 工具调用。升级为**专业化多 Agent 协作**：

| Agent | 职责 | 数据源 |
|-------|------|--------|
| **Technical Analyst** | 技术面：指标信号 + 图表形态 | Phase 8 指标库 |
| **Fundamental Analyst** | 基本面：估值 + 财务健康 | Fundamentals API |
| **Sentiment Analyst** | 情绪面：新闻 + 社交媒体 | News API + Reddit |
| **News Analyst** | 新闻面：宏观事件 + 公司动态 | News API |
| **Risk Analyst** | 风险面：波动率 + 回撤 + 相关性 | bars 数据计算 |
| **Portfolio Manager** | 仲裁者：综合各 Agent 意见做决策 | 所有 Agent 输出 |

**设计**：

```
app/agent/analysts/
  __init__.py
  base.py           # AnalystAgent 基类
  technical.py      # 技术分析 Agent
  fundamental.py    # 基本面分析 Agent
  sentiment.py      # 情绪分析 Agent
  news.py           # 新闻分析 Agent
  risk.py           # 风险分析 Agent
  portfolio_manager.py  # 仲裁 Agent
```

- 每个 Agent 有专属 system prompt + 专属工具子集
- `POST /api/analyze` 升级为多 Agent 流水线（并行分析 → 仲裁汇总）
- SSE 流式输出每个 Agent 的分析过程

### 9.2 情绪分析流水线（SentXStock / FinGPT 模式）

3 级情绪分析管线（SentXStock 的核心创新）：

| 层级 | 模型 | 覆盖率 | 成本 |
|------|------|--------|------|
| Tier 1 | **FinBERT**（本地 BERT） | ~90% 高置信度标题 | 免费 |
| Tier 2 | **LLM**（GLM/GPT） | ~10% 模糊文本 | 有成本 |
| Tier 3 | **VADER**（规则兜底） | 永远可用 | 免费 |

**数据源**：
- 新闻：Finnhub API / NewsAPI（免费额度）
- 社交：Reddit JSON API（r/wallstreetbets, r/stocks, r/investing）
- StockTwits（如可接入）

- `app/sentiment/`（新域）— 情绪分析引擎
- Agent 工具 `get_sentiment(symbol)` — 返回综合情绪分数 + 置信度

### 9.3 ML 预测引擎（stock-ai-terminal 模式）

AdaBoost 分类器预测 30 日涨跌方向 + 特征重要性排名：

| 组件 | 说明 |
|------|------|
| 特征工程 | 10+ 技术指标作为特征（RSI/MACD/ATR/Volatility/...） |
| 模型 | AdaBoost / XGBoost（walk-forward 时序验证，无 lookahead） |
| 输出 | 涨跌概率 + 特征重要性排名（哪些因子最重要） |
| 自动重训 | 定时拉取新数据重训（避免模型老化） |

**关键教训**（来自 stock-ai-terminal）：
- 诚实报告准确率（~57%，略好于随机）
- 真正价值在**可解释性**：告诉你"为什么"，而非"买还是卖"
- Volatility(42%) + MACD(21%) 是主导因子；RSI 对 30 日预测几乎无用

- `app/ml/`（新域）— 预测引擎
- Agent 工具 `predict_direction(symbol)` — 返回概率 + 因子排名

### 9.4 多 Agent 辩论机制（TradingAgents / StockPilotX 模式）

TradingAgents 的核心创新——Agent 间**辩论+投票**：

```
Round 1: 各 Agent 独立分析 → 给出观点 + 信心度
Round 2: 看到他人观点后 → 调整 / 反驳 / 支持
Round 3: Portfolio Manager 仲裁 → 最终决策
```

| 机制 | 说明 |
|------|------|
| 辩论轮次 | 可配置（默认 2 轮） |
| 冲突检测 | 信号分歧 > 50% 时标记高分歧 |
| 风险否决 | Risk Agent 看空时可一票否决 |
| 加权融合 | 各 Agent 按置信度加权 |

- `app/agent/debate.py`（新）— 辩论编排器
- `POST /api/analyze/deep`（新端点）— 深度多 Agent 分析

### 9.5 RAG 知识库（StockPilotX / FinGPT-RAG 模式）

检索增强：从历史分析/研报中检索上下文。

| 组件 | 说明 |
|------|------|
| 向量存储 | pgvector（PostgreSQL 扩展）或 ChromaDB |
| 文档源 | 历史分析结果 + 财报数据 + 新闻存档 |
| 检索 | 语义相似检索 → 为 Agent 提供历史上下文 |
| 可靠度加权 | 高质量来源（如 SEC filing）权重更高 |

- `app/knowledge/`（新域）— RAG 检索引擎
- Agent 分析时自动注入历史上下文

### 9.6 LLM 驱动的图表形态识别（QuantAgent 模式）

QuantAgent 的创新——用多模态 LLM **看图识别形态**：

| 形态 | 说明 |
|------|------|
| 头肩顶/底 | 经典反转形态 |
| 双顶/双底 | 反转形态 |
| 三角形收敛 | 变盘前兆 |
| 旗形/楔形 | 趋势延续 |
| VCP（波动率收缩） | Minervini 模式 |

**设计**：
- 将 K 线图渲染为图片 → 传给多模态 LLM → 识别形态
- Agent 工具 `detect_pattern(symbol)` — 返回检测到的图表形态 + 置信度
- 前端：在 PriceChart 上标注检测到的形态区域

---

- 每文件 < 300 LOC，单一职责
- 全异步，类型安全，无 `Any`/`as any`/`type:ignore`
- `api → domains → core` 分层，api 不碰 DB/HTTP
- 每层有测试，外部调用全 mock
- `uv` + `ruff` + `pytest`（后端）；`bun` + `biome` + `vitest`（前端）
