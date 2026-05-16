---
name: signal-trader
description: "Use when user says '信号交易' or '执行信号买入'. Multi-phase A-share trading: pull Tushare ModelB signals → filter by confidence/moneyflow/risk/positions → generate pre-market plan → check opening auction results → execute BUY orders via QMT → log decisions."
version: 1.0.7
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, a-share, qmt, signal, auction]
    related_skills: [switch-account, daily-morning-check, closing-review, native-mcp, stock-symbol-resolve, buy-single, sell-single, buy-batch, sell-batch, cancel-order, cancel-orders-batch, query-today-orders, query-today-trades, equity-research-pack, prediction-signal-debug, sector-moneyflow-brief, etf-fund-flow-tactical]
    requires_soul: profiles/trade/SOUL.md
---

# signal-trader — A股信号交易系统

## Overview

将 Tushare ModelB 买入信号转化为 QMT 限价委托的四阶段交易流程。核心特色是 **多研究员辩论评估 + 集合竞价修正**双机制：

1. **多研究员辩论（阶段 A）** — 技术研究员 + 基本面研究员采集数据，看涨/看跌研究员辩论，产生综合建议
2. **集合竞价修正（阶段 C）** — 开盘后根据竞价结果动态调整定价和仓位

参考 TradingAgents (arXiv:2412.20138) 多智能体辩论架构。

## 持仓周期配置

核心策略参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **持仓天数** | 3 天 | 买入日=Day1, 卖出日=Day3，持有期间含1个完整交易日 |
| **研究员权重** | 技术70% / 基本面30% | 短期交易技术面优先，基本面仅用于排雷 |

**时间线示例（以周一买入为例）：**
```
周一(Day1) 买入 → 周二(Day2) 持有 → 周三(Day3) 卖出
```

**辩论机制自动适应持仓周期：**

| 持仓周期 | 技术权重 | 基本面权重 | 核心关注 |
|----------|:--------:|:----------:|----------|
| **3 天** | **70%** | 30% | 短期动量/资金流向/支撑压力/均值回归 |
| 1 周 | 60% | 40% | 周线趋势/板块热度/事件驱动 |
| 1 月 | 50% | 50% | 基本面趋势/估值修复/业绩拐点 |
| 1 季 | 40% | 60% | 财报质量/行业景气/护城河 |

> 当前策略默认为 **3 天持仓**，以下所有研究员角色按此周期优化。

依赖两个 MCP 服务：
- `tushare-hermes-remote` (http://172.24.144.1:8001/mcp) — 信号源（本地代理）
- `xtqmt-trading-remote` (http://172.24.144.1:8765/mcp/) — 交易执行

两服务均使用 StreamableHTTP 协议，但实现不同（详见下方 StreamableHTTP 会话管理）。

## When to Use

- 用户说 "信号交易"、"执行信号"、"帮我看信号买入"
- 每日开盘前/后定时执行（与 [`daily-morning-check`](../daily-morning-check/SKILL.md) 编排配合时，**阶段 A–D 以本文为准**）
- 不要用于：非 A 股市场、无 Tushare 信号的标的

## Prerequisites

1. 国金 QMT-投研版或极简版已在 Windows 上运行
2. QMT MCP 服务已启动：`C:\trade\run_mcp.dist\xtqmt_mcp.exe --transport streamable-http --host 0.0.0.0 --port 8765 --path /mcp`
3. Tushare 本地 MCP 服务正常运行 (172.24.144.1:8001)
4. Hermes 的 config.yaml 中已配置上述两个 MCP 服务

## 多账户执行协议

MCP / QMT 口径如下。

**无固定默认逻辑账户 ID**：工具参数中的 **`account_id`**（与库内 **`trading_account_profiles.logical_id`** 一致）须来自 **`list_accounts`** / `GET /api/v1/trading-accounts` 等**事实列表**，或用户**明确指定**的 ID。**禁止**自动挑选、隐式假定，也不得把文档中的示例字符串当作默认值。下文示例里的 **`<logical_id>`** 仅为占位符，执行前必须替换为本次已锁定的真实 ID。

1. **前置**：HTTP API（`scripts/run_api.py` 或 `xtqmt-api`）已启动；每个要交易的逻辑账户已在 API 侧 **connect 成功**（管理台或 **`POST /api/v1/trading-accounts/{logical_id}/connect`**，JSON 体须含 **`password`**）。仅启动 MCP 而未在**同一 API 进程**内连上券商时，按 `account_id` 的读写会失败或空数据 — 与仓库根 `.cursor/skills/hermes-xtqmt-mcp/SKILL.md` 一致。
2. **发现账户**：`health_check` → **`list_trading_accounts`**（主，含每行 **`logical_id`**、**`connection`**）→ **`list_accounts`**（`data.accounts` 为已连接 runtime 的 id 字符串列表，用于交叉核对）。
3. **目标账户锁定**：在买入/卖出/批量读数前，须用第 2 步结果与用户指令对齐，**明确**本次流程使用的 **`account_id` 集合**。若 **`list_accounts` → `data.accounts` 仅 1 个元素**且用户未指定其它 id，可直接对齐为该 id（**仍须在**下文「用户可见文案」中**每段首行**标注 `account_id=`，不得省略）；若 **≥2 个已连接**且用户未口述有效 id，**不得**进入含限价/Y-N 的确认话术，须先完成 [`switch-account`](../switch-account/SKILL.md) 或等价选定。不得凭会话记忆猜 ID。仅切换会话内操作账户、不展开交易阶段 A–D → 使用 [`switch-account`](../switch-account/SKILL.md)。
4. **多账户**：对用户**点名**的每个 `account_id`，**完整重复**阶段 A–D（或用户约定的阶段子集）；资金与持仓互不混用。多账户并行下单同一标的时，优先使用 MCP **`place_limit_order_batch`**（若工具可用）；否则逐账户 `place_limit_order`，且 **`client_order_id` 按 `(account_id, 业务键)` 区分**，避免幂等冲突。
5. **配置注意**：不同逻辑账户通常需不同 **`session_id`**（及必要时不同 `miniqmt_path` / 券商资金账号），以 miniQMT 与券商侧实际能力为准。

## 用户可见文案中的 account_id（硬性）

<a id="account-id-user-facing"></a>

凡将触发或可能触发 **`place_limit_order` / `place_limit_order_batch` / `cancel_order` / `cancel_orders_batch`**，或向用户展示 **Y/N、待确认限价计划**（阶段 C 末、阶段 D 前、阶段 E 卖出确认等）的 **Agent 对外输出**（含微信简报体），须遵守：

1. **首行或第一段首句**必须为：**`当前操作账户 account_id=<logical_id>`**（或等价「本批委托账户：`<logical_id>`」）；`<logical_id>` 为本次已锁定真实 id，**禁止**用占位符应付用户。
2. **并行多账户**（同一回复含多户计划）：先一行 **`以下计划涉及 N 个账户（N=<整数>）`**，再分节；**每节第一行** **`--- 账户：<logical_id> ---`**，其下重复 **`当前操作账户 account_id=<logical_id>`** 再写该户标的与金额。
3. **≥2 已连接且用户未锁定 id**：不得输出含下单含义的 Y/N；须先 [`switch-account`](../switch-account/SKILL.md)。
4. **`get_today_orders` / `get_positions` 等**：调用时使用命名参数 **`account_id='<logical_id>'`**（与 MCP 工具签名一致）。

**示例 A — 单账户（微信体首行）：**

```text
当前操作账户 account_id=<logical_id>
━━ 今日计划 05-07 ━━
…（标的行略）
合计 ¥195,255 | 确认? Y/N
```

**示例 B — 并行两账户：**

```text
以下计划涉及 N 个账户（N=2）
--- 账户：<logical_id_A> ---
当前操作账户 account_id=<logical_id_A>
…（该户计划略）
--- 账户：<logical_id_B> ---
当前操作账户 account_id=<logical_id_B>
…（该户计划略）
```

## StreamableHTTP 会话管理

两个 MCP 服务都是 StreamableHTTP 协议，但实现模式不同：

### tushare-hermes-remote（8001）
- **无 session ID** — 不需要握手，直接 `tools/call` 即可
- 响应返回纯 JSON，非 SSE event 格式
- 支持 `Accept: application/json, text/event-stream` 头，但兼容纯 `application/json`

### xtqmt-trading-remote（8765）
- **强制 session 握手**，每次交易流程需重新创建会话：
  ```
  1. POST /mcp/ → initialize 请求
     → 从响应头 mcp-session-id 拿到会话 ID

  2. POST /mcp/ → notifications/initialized（带 Mcp-Session-Id 头）

  3. 后续所有 tools/call 请求都带 Mcp-Session-Id 头
  ```
- 会话可能过期，建议每次执行时重新初始化
- **URL 尾部斜杠必须**：`/mcp/` 带斜杠，否则返回 307 重定向

> 注意：Hermes 原生 MCP 客户端在启动时自动处理会话，无需手动干预。

## 交易流程（四阶段）

<!-- stage_id: stage_a -->

### 阶段 A：多研究员信号评估 (09:00~09:10)

借鉴 TradingAgents (arXiv:2412.20138) 多智能体辩论机制。基于 **3天持仓策略**，研究员权重为 **技术70% / 基本面30%**，技术面主导判断。

```
                  候选信号列表
       (ModelB 原始输出：ts_code, confidence, date)
                          │
                          ▼
        ┌─────────────────┼─────────────────┐
        │                                  │
   ┌────┴────┐                       ┌────┴────┐
   │ 技术研究员 │ ← 权重 70%        │ 基本面研究员│ ← 权重 30%
   │          │                       │          │
   │ 数据采集：│                       │ 数据采集：│
   │ • 近5日   │                       │ • 公告风险 │
   │   量价变化 │                       │ • 近期事件 │
   │ • 资金流向│                       │ • 基本面排雷│
   │ • 支撑/   │                       │ (不做长期  │
   │   压力位  │                       │  估值分析) │
   │ • 短期动量│                       └────┬────┘
   └────┬────┘                              │
        └─────────────────┬──────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │        研究员辩论层                │
        │                                   │
        │ ③ 看涨研究员（3天视角）              │
        │    "未来3天会涨吗？为什么？"          │
        │                                   │
        │ ④ 看跌研究员（3天视角）              │
        │    "未来3天有什么风险？为什么跌？"     │
        │                                   │
        │ ⑤ 辩论总结                         │
        │    strong_buy / buy / neutral /    │
        │    avoid                           │
        │    + 目标价位 + 止损价位             │
        └──────────────────────────────────┘
                          │
                          ▼
        进入阶段 C（集合竞价修正）+ 阶段 D（执行）
        → 仅保留 strong_buy / buy
        → 输出 target_price + stop_loss 给阶段 D/E
```

#### 步骤 0：信号获取

**`get_prev_trade_day_signals` 可能返回 0 条**（`model_path_like` 与 PostgreSQL `LIKE` 大小写敏感）。**替代调用、过滤字段与完整排障**见专文 **[`references/prediction-signal-troubleshooting.md`](references/prediction-signal-troubleshooting.md)**。Pitfall #14 仅保留索引。

#### 步骤 1：数据采集 — 技术研究员（侧重短期）

**核心原则**：3天持仓的胜负取决于**接下来3个交易日的价格方向**，不是未来3个月的基本面。

```python
# 1a. 短期动量（近5个交易日）
get_stock_snapshot(ts_code, trade_date=信号日期)
  → 提取: close, pre_close, pct_chg, vol_hand, amount
  → 计算: 近3日涨跌幅、量能变化率

# 1b. 资金流向（近5个交易日）
get_moneyflow_summary(ts_code, start_date=5日前, end_date=信号日期)
  → 重点: latest_day 的主力买卖(buy_lg_amount_wan/sell_lg_amount_wan)、特大单买卖(buy_elg_amount_wan/sell_elg_amount_wan)
  → 判断: "最后一天主力在买还是卖？" > "5日汇总"
  → 关键字段: main_net_amount_total_wan (5日主力净额)

# 1c. 实时行情（交易时段）
get_realtime_quotes_latest(ts_codes=[ts_code])
  → 当前价、买一、卖一、涨跌幅
  → 用于: 实时定价、竞价修正

# 1d. 日均数据（用于判断支撑压力）
get_daily_basic_range(ts_code, start_date=20日前, end_date=信号日期)
  → 提取: close, volume_ratio（量比）
  → 计算: 近5日 vs 近20日均价、近期高点/低点
  → ⚠️ items 按 trade_date 倒序排列：items[0]=最新, items[-1]=最旧
  → ✅ 正确取法: closes = [i["close"] for i in items[:20]]  # 最新的20条
  → ❌ 错误取法: closes = [i["close"] for i in items[-20:]]  # 最旧的20条！

# 1e. 特征数据（可选深度分析）
get_features_snapshot(ts_code, mode="latest")
  → 提取: 趋势方向(trend_direction_5/10), 支撑压力距离, 突破概率, K线形态
  → 用于: 论证看涨/看跌论点
  → MA5 = mean(closes[:5]), MA20 = mean(closes[:20])
  → 近20日高位 = max(closes), 近20日低位 = min(closes)
  → 当前位置分位 = (最新close - 低位) / (高位 - 低位) × 100
```

**技术研究员评分模板（3天版）：**

```python
评分维度（满分10）:
  ① 短期方向分 (0~4): 
     - 近3日涨跌幅 > +5% → 追高风险, 扣分
     - 近3日涨跌幅 -3%~+3% → 横盘待变, 加分
     - 近3日涨跌幅 < -5% → 超卖, 均值回归预期加分
     - 近1日收阳且量增 → 加分

  ② 资金分 (0~3):
     - 最新交易日主力净买入 → +1~2
     - 特大单净买入 → +1
     - 连续3日主力净流出 → -1~-2

  ③ 位置分 (0~3):
     - 当前位置分位 < 30% → 支撑附近, 加分
     - 当前位置分位 > 70% → 压力附近, 扣分
     - 价格低于MA20 → 均值回归预期, 加分（超跌反弹逻辑）
     - 价格高于MA20超过10% → 追高风险, 扣分
     - 缩量至近期地量 → 变盘前兆, 加分
```

**技术研究员输出模板：**
```
【技术面结论 — 3天持仓视角 — {ts_code} {name}】
├─ 短期方向: {涨/跌/横}, 近3日 {+X%/-X%}, 近1日 {收阳/收阴/平}
├─ 最后资金日: {主力买卖方向}, 特大单净额 {X万}
├─ 位置: 近20日 {X%}分位, 支撑 {price1} / 压力 {price2}
├─ 量能: 量比 {X}, 近5日量能 {放量/缩量/持平}
├─ 技术评分: {X}/10
└─ 3天研判: {一句话}
```

#### 步骤 2：数据采集 — 基本面研究员（排雷+业务分析）

**核心原则**：3天持仓以排雷为主，但可以附加业务分析判断"持有的公司在产业链中处于什么位置"，为主观看多/看空提供基本面依据。

**可用工具链（基本面版）：**
```python
# ① 排雷（必须）
scan_announcement_risk(ts_code)     # ✅ 已修复可用！直接返回 risk_level
get_risk_digest(ts_codes=[...])     # 批量版，推荐优先使用

# ② 主营构成（收入/利润/毛利率/占比）
get_fina_mainbiz_latest(ts_codes=[...])  # 最多15只同时查
  → bz_item, bz_sales, bz_profit, bz_cost
  → 计算: 业务占比% = bz_sales / total_sales
  → 计算: 毛利率% = bz_profit / bz_sales

# ③ 供应链角色 + AI业务标签
list_business_tags_snapshots(ts_code)
  → supply_role: ['上游原料','中游制造','下游集成','终端品牌',...]
  → primary_tags: 主营标签
  → core_products: 核心产品

# ④ 财务质量指标
get_rpt_fina_segment_quality(ts_code, view='company_quality')
  → ROIC, ROA, 毛利率, 净利率, OCF/OP(经营现金流/营业利润)
get_rpt_fina_segment_quality(ts_code, view='dol_proxy')
  → op_yoy(营业利润同比), tr_yoy(收入同比), dol_proxy(经营杠杆)
```

##### 2a. 排雷（必须）

```python
# 方式一：scan_announcement_risk(单只) — ✅ 2026-05-07已修复，直接可用
scan_announcement_risk(ts_code)
  → risk_level: none/low/medium/high
  → risk_level_cn: 无/低/中/高
  → risk_summary: 风险摘要文本

# 方式二：get_risk_digest(批量) — 推荐，一次查多只
get_risk_digest(ts_codes=["002103.SZ","301632.SZ"])
  → items[].risk_level: none/low/medium/high
  → 支持缓存(from_cache=true/false)
```

##### 2b. 主营业务分析（可选，增强报告质量）

```python
# 主营收入构成（最多15只同时查）
get_fina_mainbiz_latest(ts_codes=["...","..."])
  → items[].bz_item: 业务名称
  → items[].bz_sales: 收入
  → items[].bz_profit: 利润 → 计算毛利率
  → items[].bz_type: "P"=产品

# 业务标签+供应链角色
list_business_tags_snapshots(ts_code)
  → tags_json.supply_role: ["上游原料"/"中游制造"/"下游渠道"]
  → tags_json.primary_tags: 主营标签
  → 可用于判断标的在产业链中的位置

# 财务质量指标
get_rpt_fina_segment_quality(ts_code, view="company_quality", end_date="2025-12-31")
  → total_revenue, grossprofit_margin, netprofit_margin
  → roic, roa, ocf_to_op  # 经营现金流/营业利润
  → 可用于判断企业盈利质量和现金流健康度

get_rpt_fina_segment_quality(ts_code, view="dol_proxy")
  → op_yoy: 营业利润同比
  → tr_yoy: 收入同比
  → dol_proxy: 经营杠杆（正值=固定成本高，弹性大）
```

**基本面研究员评分模板（增强版）：**

```python
评分维度（满分10）:
  ① 排雷分 (0~5): 
     - 公告风险 HIGH → -10（直接 avoid）
     - 公告风险 LOW/MEDIUM → +3~5
     - 无风险 → +5

  ② 流动性分 (0~2):
     - 换手率 > 1% → +2
     - 换手率 0.3%~1% → +1
     - 换手率 < 0.3% → -5（流动性不足，avoid）

  ③ 业务质量分 (0~3, 可选):
     - 主营集中度风险：单一业务>90% → -1
     - 毛利率>30% → +1（高毛利壁垒）
     - ROIC>7% → +1（资本回报优秀）
     - OCF/OP>0.8 → +1（现金流健康）
```

**基本面研究员输出模板（增强版）：**
```
【基本面结论 — {ts_code} {name}】
├─ 公告风险: {无/低/中/高}
├─ 流动性: 换手 {X}%, {充足/不足}
├─ 主营业务: {核心产品}, 毛利率 {X}%
├─ 财务质量: ROIC={X}%, OCF/OP={X}
├─ 供应链角色: {上游/中游/下游}
├─ 基本面评分: {X}/10
└─ 结论: {可交易/需警惕/回避}
```

**供应链角色 → 看多/看空映射表（供看涨/看跌研究员参考）：**

| 角色 | 看多依据 📈 | 看空依据 📉 |
|:---|:---|:---|
| 🟢 上游技术服务 | 检测/认证/设计"卖铲子"，行业好坏都要做 | 天花板有限，依赖下游资本开支 |
| 🟢 下游品牌/集成 | 品牌溢价+渠道控制，利润池最厚 | 库存风险，消费需求波动 |
| 🔵 全链路覆盖 | 利润池最大化，抗周期能力强 | 管理复杂，每环节都可能出问题 |
| 🟡 垄断运营 | 区域/资质垄断，定价权强 | 增长有限，靠量不靠价 |
| 🟡 中游制造(高壁垒) | 技术护城河，客户粘性大 | 毛利率受上下游挤压 |
| 🔴 中游制造(同质化) | — | 毛利率为负，产能过剩亏损 |
| 🔴 纯上游原料 | 景气时弹性最大 | 单一品种，周期底部亏现金流 |

> 该表供看涨/看跌研究员撰写观点时引用，不独立计分。

#### 步骤 3：看涨研究员（3天视角）

**核心问题**：未来3天股价会涨吗？为什么？

**分析角度（按优先级）：**
1. **短期技术面**：是否处于支撑位、是否有反弹信号（锤头/十字星/缩量止跌）
2. **资金面**：最后交易日主力是否在吸筹
3. **催化剂**：近3天有没有可能的事件驱动（公告、板块异动）
4. **均值回归**：近期跌幅是否已过度（>10%），存在修复空间

**看涨论点模板：**
```
【看涨观点 — 3天目标 — {ts_code} {name}】
├─ 核心买入逻辑: {1句话, 说清未来3天为什么涨}
├─ 技术触发: {支撑位反弹/缩量止跌/放量突破}
├─ 资金信号: {主力买方/特大单方向}
├─ 3天目标价: {X.XX~X.XX}
├─ 止损价: {X.XX}
└─ 看涨置信度: {高/中/低}
```

#### 步骤 4：看跌研究员（3天视角）

**核心问题**：未来3天股价会跌吗？主要风险是什么？

**分析角度（按优先级）：**
1. **短期阻力**：上方是否有明显压力位（均线/前高/密集成交区）
2. **资金风险**：主力是否在出货、特大单是否大幅流出
3. **尾部风险**：大盘风险、板块轮动风险、假期风险
4. **流动性风险**：换手极低的标的3天内可能卖不出去

**看跌论点模板：**
```
【看跌观点 — 3天风险 — {ts_code} {name}】
├─ 核心不买理由: {1句话, 说清未来3天为什么不涨}
├─ 技术风险: {阻力位/超买/量价背离}
├─ 资金风险: {主力出货/特大单流出}
├─ 尾部风险: {如果有}
└─ 看跌置信度: {高/中/低}
```

#### 步骤 5：辩论总结

输入：技术评分 + 基本面评分 + 看涨论点 + 看跌论点
输出：最终综合建议（3天持仓版）

**综合评分公式：**
```
综合评分 = 技术评分 × 0.7 + 基本面评分 × 0.3
基础线：综合 ≥ 6.0 → 可进入交易候选
```

**裁决规则（3天版）：**

| 条件 | 建议 |
|------|------|
| 综合分 ≥ 7.5 + 看涨置信度高 + 止损空间 ≤ -5% | **strong_buy** |
| 综合分 ≥ 6.0 + 看涨 > 看跌 | **buy** |
| 综合分 ≥ 5.0 / 涨跌分歧大 | **neutral** |
| 综合分 < 5.0 / 公告风险HIGH / 看跌明显占优 | **avoid** |

**NOT 规则（一票否决，3天版简化）：**
- 公告风险 HIGH → 直接 avoid
- 换手率 < 0.3% → 流动性不足，avoid
- 止损空间 > -5%（即买入后最大可能亏损超5%）→ 3天持仓风险收益比差，降级

**每只标的输出：**
```
【研究员综合报告 — {ts_code} {name}】
┌─ 技术研究员: {评分}/10 — {3天研判}
├─ 基本面研究员: {评分}/10 — {排雷结论}
├─ 😊 看涨: {置信度} — {核心逻辑} → 目标 {price}
├─ 😟 看跌: {置信度} — {核心风险} → 止损 {price}
├─ 持仓设定: 买入 {today} → 卖出 {today+2交易日}
└─ 🏆 建议: {strong_buy/buy/neutral/avoid}
   └─ 理由: {一句话}
```

#### 步骤 6：排名与筛选

按综合评分排序，仅保留 strong_buy + buy：

```
排序优先级（按综合评分降序，同分按 ModelB 置信度）:
1. strong_buy → 主要仓位 (60-70% 预算)
2. buy        → 次要仓位 (30-40% 预算)
3. neutral    → 观察池（不参与当日交易）
4. avoid      → 直接淘汰
```

**排名展示格式：**
```
📋  最终排名
────────────────────────────────────────────────
排名    标的              建议      综合  技术  基本面  ModelB  位置
────────────────────────────────────────────────
1      603366.SH 日出东方  🟢 sb   9.3   9.5    9    0.723   8%
2      002791.SZ 坚朗五金  🟢 sb   7.6   7.0    9    0.752  20%
3      ...                🟡 n    ...   ...    ...   ...     ...
────────────────────────────────────────────────
可交易: 603366.SH 日出东方 (¥8.36, 23,900股≈¥199,804)
        002791.SZ 坚朗五金 (¥18.36, 10,800股≈¥198,288)
```

<!-- stage_id: stage_b -->

### 阶段 B：盘前资金与系统检查 (09:10~09:15)

**步骤：**

1. **确认系统就绪**
   - 调用 `health_check` 确认 `xtqmt_state == READY`
   - 调用 `get_account_assets`（`account_id='<logical_id>'`）查可用资金

2. **持仓去重**
   - 调用 `get_positions`（`account_id='<logical_id>'`）获取当前持仓
   - 已持有的标的：检查是否允许加仓（综合评分 ≥ strong_buy 才允许）
   - 重复的标的从候选列表中移除（除非允许加仓）

3. **资金分配**
   - 总买入上限 = min(可用资金 × 50%, ¥200,000)
   - 单标金额 = 总买入上限 × (该标综合评分 / Σ 各标综合评分)
   - 单标股数 = floor(单标金额 / last_price / 100) × 100

<!-- stage_id: stage_c -->

### 阶段 C：集合竞价修正 (09:25)

1. **获取竞价结果**
   - 调用 `get_realtime_quotes_latest(ts_codes=[...])` 传入所有候选标的
   - 获取每个标的的：open(开盘价)、bid_price(买一)、ask_price(卖一)、vol(成交量)

2. **计算竞价偏离度**
   ```
   偏离度(%) = (开盘价 - 信号基准价) / 信号基准价 × 100
   ```

3. **计算开盘涨幅**
   ```
   开盘涨幅(%) = (开盘价 - 前收盘价) / 前收盘价 × 100
   ```
   前收盘价从 `get_realtime_quotes_latest` 返回的 `pre_close` 字段获取。

4. **修正规则**

   先检测是否跌停：开盘价 ≤ 前收盘价 × 0.9（主板，创业板/科创板为 × 0.8）→ 跌停标的直接取消。

   | 规则 | 条件 | 操作 |
   |:----:|:----:|------|
   | **跌停取消** | 开盘价达到跌停价 | ❌ **取消该标的当日买入计划** |
   | **高开取消** | 开盘涨幅 ≥ **1.5%** | ❌ **取消该标的当日买入计划** |
   | 竞价高开 | 0.5% ≤ 开盘涨幅 < 1.5% | 按计划执行，定价用买一价 |
   | 竞价平稳 | -0.5% ≤ 开盘涨幅 < 0.5% | 按计划执行 |
   | 竞价低开 | -2% ≤ 开盘涨幅 < -0.5% | 按计划执行，定价用最新价-1档 |
   | 跳空低开 | 开盘涨幅 < -2% | 按计划执行，定价用买一价 |

5. **动态定价策略**

   | 开盘涨幅 | 推荐定价 | 
   |:--------:|:--------:|
   | 0.5% ~ 1.5%（高开但未取消） | 买一价（挂单等回调） |
   | -0.5% ~ 0.5%（平稳） | 最新价（开盘价） |
   | -2% ~ -0.5%（低开） | 最新价 - 1档 |
   | 量比异常放大(>3x) | 买一价(分批吃) |

6. **生成当日交易计划 → 提交用户确认**

   **硬性规则（多账户 / 限价确认）：** 输出给用户前须满足 **[用户可见文案中的 account_id（硬性）](#account-id-user-facing)**：首行含 `当前操作账户 account_id=…`；≥2 已连接且未锁定时不得发 Y/N。下方示例块**第一行**均为账号声明（占位 `<logical_id>` 执行时替换）。

   将最终计划输出给用户确认。微信排版：每行不超过25字、无表格、数字简洁。

   **输出格式（微信版）：**
   ```
   当前操作账户 account_id=<logical_id>
   ━━ 今日计划 05-07 ━━
   💰 预算 ¥200,000

   🟢广东建科 1400×20.98
    t21.20 s19.80 | 评分7.9

   🟢通行宝 1800×13.21
    t13.50 s12.60 | 评分6.6

   🟢中机认检 800×29.52
    t30.00 s28.50 | 评分6.5

   🟢光明乳业 3200×7.47
    t7.60 s7.20 | 评分6.5

   🔴已取消: 无
   ━━━━━━━━━━━━━
   合计 ¥195,255 | 确认? Y/N
   ```

   超简版（适合手机小屏）：
   ```
   当前操作账户 account_id=<logical_id>
   ━━ 今日计划 ━━
   1🟢广东建科 1400×20.98
   2🟢通行宝 1800×13.21
   3🟢中机认检 800×29.52
   4🟢光明乳业 3200×7.47
   5🟢西部创业 5200×4.70
   6🟢德尔玛 2500×9.47
   7🟢广博股份 3000×8.05
   8🟢华贸物流 4000×5.58
   ━━━━━━━━━
   ¥195,255 Y/N?
   ```

   **执行流程：**
   - 用户回复 Y / 确认 → 进入阶段 D 执行
   - 用户回复 N / 取消 → 放弃当日所有交易
   - 用户修改（如"只买前2个"）→ 按用户指令调整后执行

<!-- stage_id: stage_d -->

### 阶段 D：盘中执行 (09:30 后)

**硬性规则：** 任何对用户的状态更新或复述下单动作前，首行须含 **`当前操作账户 account_id=<logical_id>`**（见 **[用户可见文案中的 account_id（硬性）](#account-id-user-facing)**）。调用 MCP 时须显式传 **`account_id='<logical_id>'`**。

1. **逐一下单**（按综合评分从高到低）
   - 每单间隔 ≥2 秒（风控约束）
   - 调用 `place_limit_order(account_id='<logical_id>', side='BUY', symbol='XXXXXX.SH/.SZ', price=price, amount=amount)`
   - 每次新委托用新的 UUID 作为 client_order_id
     ⚠️ 若因网络超时重试同一笔委托，必须复用**相同**的 client_order_id（幂等键），否则可能重复下单

2. **订单状态检查 (09:35)**
   - **❌ 不要只依赖 `get_today_orders`（`account_id='<logical_id>'`）的 `status` 字段** — QMT 的委托状态可能永远显示 `SUBMITTED`，即使订单已实际成交。这是 QMT 数据刷新延迟导致的现象。
   - **✅ 必须用 `get_positions`（`account_id='<logical_id>'`）交叉验证成交** — 持仓中出现该标的且 `quantity > 0` = 已成交。这是可靠方案。
   - 未成交的标的（`get_today_orders` 显示 SUBMITTED 但 `get_positions` 没有）：
     - 若开盘后股价上涨超过限价 → 属于正常现象，不追单
     - 若开盘后股价仍在限价附近 → 可以等待，通常后续会成交
   - 成交的：记录成交价和数量，记录 **持仓到期日 = 今日 + 2交易日**
   - 提醒用户未成交情况

3. **记录持仓到期日**
   - 在决策日志中记录：`{标的} 买入 {price} {amount}股 到期日: {today+2交易日}`
   - 示例：周一买入 → 到期日周三

<!-- stage_id: stage_e -->

### 阶段 E：卖出执行（持仓 Day 3）

**硬性规则：** 向用户复述卖出计划或拆单结果前，首行须 **`当前操作账户 account_id=<logical_id>`**（见 **[用户可见文案中的 account_id（硬性）](#account-id-user-facing)**）。

**触发条件：** 持仓到期日，开盘前自动检查。

**时间线：**
```
Day 1 (买入日): 09:30 买入 → 收盘
Day 2 (持有日): 持有观察，不操作
Day 3 (卖出日): 09:25 检查集合竞价 → 09:30 执行卖出
```

#### 步骤

1. **开盘前检查 (09:25)**
   - 调用 `get_positions`（`account_id='<logical_id>'`）确认持仓仍在
   - 调用 `get_realtime_quotes_latest(ts_codes=[标的])` 获取当前价格和竞价情况

2. **卖出定价策略（3天版本）**

   | 持仓盈亏 | 操作 | 定价策略 |
   |:--------:|:----:|:--------:|
   | **盈利** (浮盈>0) | ✅ 必须卖出 | 卖一价挂单，确保成交 |
   | **亏损≤-2%** | ✅ 必须止损卖出 | 卖一价，止损优先 |
   | **亏损-2%~0** | ⚠️ 按竞价情况决定 | 若高开→卖一价卖出；若低开→持有至10:00再决定 |

   ⚠️ **3天策略强制规则**：买入即设定卖出日，Day 3 必须执行卖出，不延长。这是短线交易纪律。

3. **执行卖出**

   ⚠️ **QMT 单笔风控硬限制：单笔金额 ≤ ¥200,000**。大仓位必须拆分成多个子订单，否则全部失败。拆分算法：

   ```python
   MAX_AMOUNT = 200000
   total_shares = position.amount
   price = sell_price
   
   orders = []
   remaining = total_shares
   while remaining > 0:
       max_per_batch = int(MAX_AMOUNT / price / 100) * 100  # 百股取整
       batch = min(max_per_batch, remaining)
       orders.append(batch)
       remaining -= batch
   
   print(f"拆分: {total_shares}股 → {len(orders)}笔")
   for batch in orders:
       place_limit_order(
           account_id='<logical_id>', side='SELL',
           symbol=ts_code, price=price,
           amount=batch, client_order_id=new_uuid
       )
       time.sleep(2)  # 两秒间隔
   ```

   实际案例：本日(2026-05-06) 9笔大仓位需分拆为 21 个子订单才全部通过风控。总回收资金 ¥2,734,556，拆单后全部成功。

4. **确认成交 (09:35)**
   - 调用 `get_today_orders`（`account_id='<logical_id>'`）确认卖出委托状态
   - 调用 `get_positions`（`account_id='<logical_id>'`）确认标的已清仓
   - 记录卖出结果到决策日志

5. **交易反思**
   - 记录本笔盈亏：`卖出价 - 买入价`
   - 记录研究员评估的准确度：看涨/看跌谁对了
   - 写入决策日志反思段落

## MCP 工具快速参考

### Tushare 信号工具

当前服务器（本地 Windows, 172.24.144.1:8001）共有 **40 个工具**（v0.3.0），含 **7 个基金工具**和**9个新增工具**。以下是按角色分类的工具参考：

#### 信号/行情核心工具

| 工具 | 角色 | 用途 |
|------|:----:|------|
| `get_prev_trade_day_signals` | 信号源 | 原始ModelB买入信号获取（⚠️ 可能因model_path_like大小写不匹配返回0条，见下方Pitfalls#14） |
| `get_prediction_active_range` | 信号源 | **v0.3.0新增** — 活跃预测池，比get_prediction_results多了risk_level/risk_type/risk_summary + range_amplitude_pct/limit_up_count 字段，一次调用拿预测+风控 |
| `get_prediction_result_aggregates` | 信号源 | 全库预测统计（涨跌比、平均置信度） |
| `get_prediction_statistics_rows` | 信号源 | 预测统计表行 |
| `get_prediction_ranking_rows` | 信号源 | 预测排名统计 |
| `get_stock_snapshot` | 技术研究员 | 单股行情快照（收盘价、涨跌幅、成交量） |
| `get_moneyflow_summary` | 技术研究员 | 区间资金流向汇总（主力/特大单净额） |
| `get_daily_basic_range` | 技术研究员 | PE/PB/换手率/市值等日线基本面 |
| `get_adj_factor_range` | 技术研究员 | 复权因子查询 |
| `get_adjusted_quote_range` | 技术研究员 | 前/后复权K线（qfq/hfq） |
| `get_features_snapshot` | 技术研究员 | 200+特征：K线形态/趋势/支撑压力/突破概率（❗ 当前 trend_direction_5/10、support_price、resistance_price、breakout_probability 返回全部为 "?"，数据可能未入库） |
| `get_realtime_quotes_latest` | 竞价修正 | 批量实时行情（最多50只） |
| `get_index_basic_list` | 技术研究员 | 指数基础信息（分页） |
| `get_index_daily_range` | 技术研究员 | 指数日线（大盘参考） |
| `get_trade_calendar` | 风控 | 交易日历（确认当天是否开市） |
| `get_trade_calendar_statistics` | 风控 | 全库日历统计 |
| `scan_announcement_risk` | 基本面研究员 | 公告风险快查（✅ **2026-05-07已修复**，服务端已配DeepSeek，返回risk_level+risk_summary） |
| `get_risk_digest` | 基本面研究员 | **✅ 可用替代** —— 返回 risk_level (none/low/medium/high)+risk_summary，无需API Key |
| `get_risk_scan_cache` | 基本面研究员 | 风险扫描缓存读取 |
| `get_announcement_pdf_text_cache` | 基本面研究员 | 公告PDF正文缓存读取 |
| `list_cninfo_announcements_range` | 基本面研究员 | **巨潮公告查询**（替代scan_announcement_risk做排雷！不需要API Key） |
| `list_tushare_announcements_range` | 基本面研究员 | Tushare来源公告查询 |
| `get_fina_statement_range` | 基本面研究员 | **财务三张报表**（income/balancesheet/cashflow/indicator/forecast/express/audit/dividend） |
| `get_rpt_fina_segment_quality` | 基本面研究员 | **财务细分质量**（company_quality/dol_proxy等5视图） |
| `get_fina_mainbiz_latest` | 基本面研究员 | 多只股票最新主营构成（最多15只） |
| `list_business_tags_snapshots` | 基本面研究员 | 业务标签快照 |
| `list_mainbiz_relations_by_run` | 基本面研究员 | 主营业务关系快照 |
| `list_mainbiz_relations_latest` | 基本面研究员 | 最近一次主营业务关系快照（无需run_id） |
| `list_mainbiz_runs` | 基本面研究员 | 主营业务运行记录列表 |
| `get_mainbiz_run_metrics_by_run` | 基本面研究员 | 主营业务流水线运行指标 |
| `get_mainbiz_run_metrics_latest` | 基本面研究员 | 最近一次运行指标（无需run_id） |
| `get_fund_basic_snapshot` | 研究员(基金) | 基金基础信息快照 |
| `get_fund_company_snapshot` | 研究员(基金) | 基金公司快照 |
| `get_fund_portfolio_report` | 研究员(基金) | 单基金季报持仓明细 |
| `get_fund_share_range` | 研究员(基金) | 基金份额日线序列 |
| `get_fund_share_change_range` | 研究员(基金) | 份额日环比变动（由物理表写入，✅ 数据已存在） |
| `get_fund_holdings_diff_stock` | 研究员(基金) | 两期对比—个股维（需物化） |
| `get_fund_holdings_diff_industry` | 研究员(基金) | 两期对比—行业维（需物化） |
| `health_check` | 所有 | 检查数据库与服务器状态 |

### QMT 交易工具

| 工具 | curl 方法 | 说明 |
|------|-----------|------|
| `health_check` | `tools/call` 无参数 | 检查 QMT 状态 |
| `list_accounts` | `tools/call` 无参数 | 列出所有交易账户 |
| `get_account_assets` | `tools/call` params: `account_id` | 资金快照 |
| `get_positions` | `tools/call` params: `account_id` | 持仓列表 |
| `get_today_orders` | `tools/call` params: `account_id` | 当日委托 |
| `get_today_trades` | `tools/call` params: `account_id` | 当日成交 |
| `place_limit_order` | `tools/call` params: `account_id, side, symbol, price, amount` | 限价下单 |
| `cancel_order` | `tools/call` params: `account_id, order_id` | 撤单 |
| `cancel_orders_batch` | `tools/call` params: `account_id, order_ids` | 批量撤单 |
| `get_quote` | `tools/call` params: `symbol` | 行情快照(需QMT客户端) |
| `symbol_suggest` | `tools/call` params: `keyword` | 股票搜索（按中文名） |
| `get_trade_stats` | `tools/call` params: `account_id` | 交易统计汇总 |
| `get_history_orders` | `tools/call` params: `account_id, start_date, end_date` | 历史委托 |
| `get_history_trades` | `tools/call` params: `account_id, start_date, end_date` | 历史成交 |
| `get_history_assets` | `tools/call` params: `account_id, start_date, end_date` | 历史资产 |
| `get_pnl_curve` | `tools/call` params: `account_id` | 盈亏曲线 |

## 集成交互场景

### 完整交易周期（5天示例，周一买入）
```
周一 09:00  阶段A(研究员辩论) → 阶段B(资金检查)
    09:25  阶段C(集合竞价修正) → 提交计划给用户确认
    09:30  阶段D(买入执行) → 记录到期日周三
周二        持有观察，不操作
周三 09:25  阶段E(卖出检查) → 获取竞价/持仓 → 执行卖出
    09:35  确认成交 → 记录反思
```

### 手动信号交易
```
用户: 信号交易
Agent → 阶段A(研究员辩论) → 阶段B(资金检查)
       → 阶段C(竞价修正) → 提交交易计划给用户确认
用户: Y
Agent → 阶段D(买入) → 推送成交 + 到期日提示
```

### 定时执行 (cron) — 买入
```
cron 25 9 * * 1-5
Agent → 阶段A→B→C → 提交交易计划到微信等待确认
       → 不自动执行
```

### 定时执行 (cron) — 卖出（Day 3）
```
cron 25 9 * * 1-5
Agent → 检查是否有今日到期的持仓
       → 阶段E(执行卖出) → 推送卖出结果
```

### 盘中快速查看（不交易）
```
用户: 看看今天信号
Agent → 只执行阶段A(研究员评估) → 输出研究员报告 → 不执行后续
```

## MCP 工具响应结构参考

**关键事实：** 各工具 JSON **结构不一致**，不存在通用 `items[]`。若按统一模板解析，会导致静默丢数、评分全错。**影响：** 阶段 A 采集循环会反复返工；竞价与下单所依赖的资金/价位字段也会错位。

**权威细节与 JSON 样例**见 [`references/mcp-response-structures.md`](references/mcp-response-structures.md)（含 `get_stock_snapshot` / `get_moneyflow_summary` / `get_daily_basic_range` 等）。**其中 `get_daily_basic_range` 的 `items[0]` 为最新日**；若误用切片尾部，会把最旧 20 日当成「最近 20 日」，技术分位与均线全部反向。

**已知局限与信号源陷阱（含 `get_prev_trade_day_signals` 0 条、`probability_up` 筛选等）**见同文件章节 [**MCP 工具已知局限** `references/mcp-response-structures.md#mcp-known-limitations`](references/mcp-response-structures.md#mcp-known-limitations)。**影响：** 信号为空时须切换 `get_prediction_results`；`get_realtime_quotes_latest` 在 09:25 前常失败属预期；`get_features_snapshot` 多字段为 `?` 时不应作为核心否决条件。

## 数据采集工作流（已验证）

当有 20 个候选信号时，推荐的并行/串行混合流程：

```
并行:   get_stock_snapshot(20只)    +  get_daily_basic_range(20只)
       → 两个独立循环，各间隔0.3s，可并行
串行:   get_moneyflow_summary(20只)  +  scan_announcement_risk(20只)
       → 间隔0.3s（moneyflow）     → 间隔1.0s（risk，防限流）
后置:   技术评分计算  → 排名输出 → 持仓去重
```

> 验证脚本见 `scripts/collect-researcher-data.py` — 可直接复制修改使用

## 时间检查

**⚠️ 必须用 `date` 获取实际系统时间，不要靠会话上下文估算。**
交易流程中 09:00~09:30 的每一步都有精确时间窗口，时间错误会导致：
- 集合竞价阶段错过 09:25 窗口
- 下单时机不对
- 用户信任度下降

每次汇报时间相关结论前执行：`date '+%H:%M:%S'`

## Common Pitfalls

1. **QMT MCP 会话过期** — 通过 curl 手动创建的 session（mcp-session-id）会在几分钟后过期。执行阶段 B/C/D 之前必须重新握手：`initialize → 拿 session ID → notifications/initialized → 后续调用都带该 ID`。从创建到执行下单如果间隔超过 5 分钟，**必须重新初始化**。过期表现为：
   - `get_account_assets` 返回 0 / 空数据
   - `get_positions` 返回空列表
   - `place_limit_order` 返回 400 Bad Request Missing Session ID
   - 解决方案：每次执行前重做 session 握手

2. **限价单开盘不成交** — 以开盘价（集合竞价结果）挂的限价买单，如果开盘后股价快速上涨，限价单会留在场外无法成交。这是正常现象，不代表系统异常。未成交检查方法：
   - `get_today_orders` 的 `status` 始终显示 `SUBMITTED` → **不可靠**，QMT 可能不更新此字段
   - `get_positions` 才是可靠方案 → 持仓有该标的 = 已成交
   - **定价改进建议**：盘前将定价设为开盘价 + 1档（约 0.01~0.02），牺牲极小价差换取更高成交率

3. **卖出大仓位必须拆单** — QMT 服务端硬限制单笔 ≤ ¥200,000。大仓位按照 `int(200000/price/100)*100` 计算每批最大股数，循环拆分成多个子订单提交，间隔 2 秒。详见阶段 E 步骤 3。

4. **股票代码后缀错误** — Tushare 返回的 `ts_code` 自带后缀（如 `002103.SZ`），QMT 下单时 `symbol` 参数需要用相同的格式。上海股票是 `.SH`，深圳是 `.SZ`。

5. **日期格式** — Tushare MCP 工具统一要求 `YYYY-MM-DD` 格式，不接受 `YYYYMMDD`。

6. **非交易日下单** — 5/1 劳动节、周末等不开市。下单前先用 `get_trade_calendar` 确认当天是否为交易日。

7. **重复委托幂等键** — `place_limit_order` 的 `client_order_id` 是幂等键。网络重试时必须传**同一个** client_order_id，否则可能重复下单。每次新委托用新的 UUID。

8. **QMT 客户端必须在线** — `get_quote` 和下单操作依赖 QMT 客户端在 Windows 上运行。非交易时段 QMT 可能已断开。

9. **实时行情非交易时段为缓存** — `get_realtime_quotes_latest` 在非交易时段返回的是最近交易日的缓存数据，不能用于定价。

10. **get_trade_calendar 的 trading_only 参数** — 设为 `true` 只返回交易日，设为 `false`（或不传）返回所有日历日。

11. **StreamableHTTP 会话差异** — xtqmt (8765) 强制 session 握手且会话会过期，每次执行需重新初始化。tushare (8001) 无需 session ID，直接调用即可。

12. **URL 尾部斜杠导致 307 重定向** — xtqmt 的 MCP URL 必须带尾部斜杠 `/mcp/`，否则服务器返回 307 重定向，可能导致连接失败。

13. **基金持仓字段名** — `get_fund_portfolio_report` 的字段名与直觉不同：
    - `symbol` = 股票代码（不是 `stock_code`）
    - `stk_mkv_ratio` = 占比%（不是 `percentage`）
    - `mkv` = 持仓市值（不是 `market_value`）
    - `end_date` 必须为季度末日 YYYYMMDD（如 `20251231`），非季度末日返回0条
    - 代码格式支持 `.SH`/`.SZ`/`.OF` 及裸6位码，自动匹配

14. **`get_prev_trade_day_signals` 返回 0 条（model_path / LIKE 大小写）** — 详见 **[`references/prediction-signal-troubleshooting.md`](references/prediction-signal-troubleshooting.md)**；修复路径为 `get_prediction_results` + 手动过滤 `probability_up`。

15. **信号过滤用 `probability_up` 字段** — 用户明确偏好使用 `probability_up` 而非 `confidence` 作为信号筛选字段。虽然当前数据中两者值基本相等（14/500条有微小差异），应始终用 `probability_up`。

16. **`get_features_snapshot` 字段多数返回 `?`** — `trend_direction_5/10`, `support_price`, `resistance_price`, `breakout_probability`, `candle_pattern` 等字段返回空值或 `?`。可能特征数据未入库或字段定义不匹配。不推荐依赖此工具进行核心判断。

17. **`get_risk_digest` 是 `scan_announcement_risk` 的有效替代** — 不需要 DEEPSEEK_API_KEY，直接返回 `risk_level: none/low/medium/high` + `risk_summary` 文本，可用于基本面排雷。

18. **基金公司查询** — `get_fund_company_snapshot` 不传 `company_key` 时分页列出正常工作；按中文名搜索可能返回0条，建议先用分页列出。

19. **fund_holdings_diff 需要物化并注意过滤条件** — `get_fund_holdings_diff_stock` 和 `get_fund_holdings_diff_industry` 的数据不是自动同步的，需要先运行 `services/fund_holdings_diff_service.materialize_holdings_diff()` 写入数据后才能查到。即使 `fund_portfolio` 有 3 期季报数据，diff 表也可能是空的。

    **⚠️ 即使表有数据也可能返回0条：** 两个工具默认用 `ashare_only=True, listed_only=True` 过滤。如果数据是直接通过 SQL INSERT 写入的（未使用 materialize 函数），`ashare_only` 和 `listed_only` 可能是 `NULL` 或 `False`，导致 MCP 查询过滤不命中。排查方法：
    
    ```sql
    -- 在 DB 中确认实际存储的过滤条件值
    SELECT DISTINCT ashare_only, listed_only FROM fund_holdings_diff_stock;
    SELECT DISTINCT old_period, new_period FROM fund_holdings_diff_stock;
    ```
    
    **建议始终用 `materialize_holdings_diff()` 写入数据**，确保 `ashare_only=True, listed_only=True` 正确写入。

20. **小盘股基金持仓反查的局限** — 小盘/次新股（流通市值<50亿）基本不会出现在主流ETF的前30大持仓中，`get_fund_portfolio_report` 的前30条查不到它们的基金持仓。`get_fund_holdings_diff_stock` 因需要物化也通常返回0条。

    **替代方法：** 追踪中小盘ETF份额变动（512100中证1000ETF、510500中证500ETF）作为小盘组合的宏观资金面指标。详见 `references/fund-flow-macro-context.md`。

## Reference Files

| File | Content |
|------|---------|
| `../_shared/qmt-pitfalls.md` | 症状→影响→正确做法（QMT/数据侧）；Cron JSON-RPC 见 `../_shared/mcp-jsonrpc-cron-pattern.md` |
| `../_shared/wechat-brief-output.md` | 微信/私域短文本排版边界（非钉钉/邮件） |
| `references/trading-ecosystem-architecture.md` | Full ecosystem context: xtqmt-user + openclaw bridge + tusharestock pipeline, network topology, StreamableHTTP server variations, business positioning |
| `references/mcp-response-structures.md` | Exact JSON response shapes for each Tushare MCP tool used in Phase A data collection (get_stock_snapshot, get_moneyflow_summary, get_daily_basic_range, etc.) — **read this before coding any data collection loop** to avoid parsing bugs |
| `references/mainbiz-analysis.md` | Main business composition analysis, financial quality metrics, supply chain role positioning (supply_role), and cross-industry comparison techniques — for enhanced fundamental researcher use |
| `references/fund-flow-macro-context.md` | ETF fund flow analysis for macro context: monitoring small/mid-cap ETF share changes, understanding fund coverage limitations for small-cap stocks |
| `references/mcp-data-availability.md` | MCP 数据支持全景审计 — 哪些工具有数据/哪些为空/哪些需跑流水线 |
| `references/feature_fields_whitelist.yml` | `equity-research-pack`；消费 `get_features_snapshot` 时 |
| `references/prediction-signal-troubleshooting.md` | 预测信号 0 条、`get_prediction_results` 回退与 `probability_up` 约定（从主文档抽离） |
| `references/multi-stock-comparison.md` | 多标的横向对比模板 — 行业/上下游/财务指标对比格式及质量排序逻辑 |

## Verification Checklist

- [ ] 信号获取成功，有 items 返回
- [ ] 数据采集完成：技术数据（daily_basic, moneyflow, features_snapshot）+ 基本面数据（mainbiz, risk, company_quality）
- [ ] features_snapshot K线形态已检查（doji/hammer/breakout_probability 等，注意该工具字段多数为空，"?" 表示无数据）
- [ ] 技术研究员完成评分（1-10分）和趋势判断
- [ ] 基本面研究员完成评分（排雷+业务质量，1-10分）
- [ ] 如需上下游分析：主营业务构成、毛利率、供应链角色(supply_role)已检查
- [ ] 看涨/看跌研究员完成辩论，输出最终建议
- [ ] 候选列表按 strong_buy > buy > neutral > avoid 排序
- [ ] NOT 规则已检查（公告风险HIGH → avoid）
- [ ] 过滤后的候选列表 ≥ 1 只
- [ ] QMT health_check 返回 `xtqmt_state: READY`
- [ ] 可用资金 ≥ 最小买入金额
- [ ] 集合竞价结果已获取，按 `pre_close` 计算开盘涨幅
- [ ] 开盘涨幅 ≥ 1.5% 的标的已从计划中移除
- [ ] 开盘价达跌停价的标的已从计划中移除
- [ ] 阶段 C/D/E 对外输出首行含 `account_id=`（见 [#account-id-user-facing](#account-id-user-facing)）
- [ ] 用户确认后下单，`client_order_id` 使用新 UUID
- [ ] 下单后调用 `get_today_orders` 确认委托状态
- [ ] 记录持仓到期日到决策日志
- [ ] Day 3 开盘前检查持仓并执行卖出
- [ ] Day 3 卖出后确认成交和清仓
- [ ] 记录卖出盈亏和研究员命中情况到决策日志
