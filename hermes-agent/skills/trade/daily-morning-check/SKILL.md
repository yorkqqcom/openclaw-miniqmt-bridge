---
name: daily-morning-check
description: "Cron 薄编排：08:00 基金份额晨报；09:00/09:27/09:30 通路检查与交易流程须严格遵循 signal-trader 阶段 A–D。含真实时间与 JSON-RPC 注意。"
version: 1.2.1
author: Hermes Agent
tags: [trading, a-share, morning, daily-routine, cron]
metadata:
  hermes:
    related_skills: [signal-trader, closing-review, switch-account, stock-symbol-resolve, buy-single, sell-single]
    requires_soul: profiles/trade/SOUL.md
    morning_cron_authority:
      - { schedule: "0 8 * * 1-5", label: "08:00 基金份额晨间分析", deliver: "资金流向晨报" }
      - { schedule: "0 9 * * 1-5", label: "09:00 系统自检和信号识别", deliver: "候选报告" }
      - { schedule: "27 9 * * 1-5", label: "09:27 竞价修正+交易计划", deliver: "交易计划待确认" }
      - { schedule: "user Y after 09:27", label: "09:30 起执行", deliver: "下单与成交核对" }
---

# Daily Morning Check — 晨间 Cron 编排

## Overview

本 skill 为 **薄编排层**：**权威交易逻辑**在 [`signal-trader/SKILL.md`](../signal-trader/SKILL.md)（阶段 A–D/E）；共享运维说明在 [`../_shared/`](../_shared/) 与 [`../TRUTH_SOURCE.md`](../TRUTH_SOURCE.md)。首次实盘复盘摘要已收敛到 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。若部署侧注入 **JSON 会话快照**，入口读入约定见 [`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md)（渐进）。

## When to Use

- 用户说「检查今天的交易计划」「早盘」「morning check」、或 **交易日早晨** 的自动化任务。
- 定时 cron：见下方 **权威时间表**（与 `metadata.hermes.morning_cron_authority` 一致）。
- **不要使用本 skill**：用户明确要做 **收盘盘点、盘后复盘、今日盈亏、成交核对** — 请使用 [`closing-review`](../closing-review/SKILL.md)。**优先级建议：** 用户声明时段 / 当前系统时间（先 `date`）优于模糊关键词。

## 权威时间表（唯一）

以下时间为本包内 **唯一权威** 晨间分段定义；`closing-review` 使用 **15:00** 段，不在此重复。

| 时间 | 内容 |
|:----:|------|
| **08:00** | 宽基+行业 ETF 份额 → 资金流向晨报（本节独有） |
| **09:00** | 通路、交易日历，并进入 `signal-trader` **阶段 A** 直至候选输出 |
| **09:27** | 取 09:00 候选 → `signal-trader` **阶段 C** 竞价修正 → 资金分配与计划 |
| **09:30~** | 用户回复 `Y` 后 → `signal-trader` **阶段 D** 执行；间隔、UUID 以该文档为准 |

更完整的场景→Skill 对照见仓库根 [`readme.md`](../../../../readme.md) §5.3。

## 复盘与运维要点（摘要）

- **时间：** 禁止凭会话猜时间；先 `date '+%H:%M:%S'`。详见 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。  
- **Cron 调 MCP：** 勿用 shell 直打内网 IP；用 `execute_code` + `httpx`，JSON-RPC 须为 `tools/call`。详见 [`../_shared/mcp-jsonrpc-cron-pattern.md`](../_shared/mcp-jsonrpc-cron-pattern.md)。  
- **微信排版：** [`../_shared/wechat-brief-output.md`](../_shared/wechat-brief-output.md)。

## 阶段 A–D 执行协议（默认）

1. **打开** [`signal-trader/SKILL.md`](../signal-trader/SKILL.md)，**按文档内顺序**执行阶段 **A → B → C → D**（工具、阈值、`probability_up`、排雷与竞价规则 **仅以该文为准**）。  
2. 本 skill **仅追加**：Step 0 真实时钟；§「08:00 基金份额」；cron 分段输出与链式 `context_from`（见文末 YAML）；不得在本文件另写一套冲突的过滤/定价规则。  
3. **多账户**：与 `signal-trader` 中 [「多账户执行协议」](../signal-trader/SKILL.md#多账户执行协议) 及 [「用户可见文案 account_id 硬性」](../signal-trader/SKILL.md#account-id-user-facing) 一致；进入阶段 **D** 等含 **`place_limit_order`** 前若存在多已连接账户且未锁定 id，须先 [`switch-account`](../switch-account/SKILL.md)。本 skill 不另写迭代规则。  
4. **阶段边界命名**须能对照 `signal-trader` 小节标题（阶段 A：多研究员信号评估；阶段 B：盘前资金与系统检查；阶段 C：集合竞价修正；阶段 D：盘中执行）。

```text
R0 = shell_date_or_equivalent()
IF cron_window == 08:00:
    run_etf_fund_share_only(); EMIT report; STOP
ASSERT trade_day else EMIT "非交易日" STOP
IF cron_window >= 09:00:
    follow_signal_trader(SKILL_path, phases=[A,B,C,D])
    // 不在此重复工具列表；子步骤标题以 signal-trader 为准
```

## 执行步骤

### Step 0: 获取真实时间

```bash
date '+%H:%M:%S'
```

必须先执行；详见 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

### 08:00 基金份额晨间分析（本 skill 独有）

**数据源：** Tushare `get_fund_share_range`。Cron 下 HTTP 须按 [`../_shared/mcp-jsonrpc-cron-pattern.md`](../_shared/mcp-jsonrpc-cron-pattern.md) 使用 `httpx` + `tools/call`（勿照抄过时 `curl`）。`call_tool` 最小实现见该附录；此处从 **`health_check` 之后** 接份额拉取。

**ETF 清单（示例，可按部署调整）：**

```python
broad_etfs = {
    "510300.SH": "沪深300", "510500.SH": "中证500", "512100.SH": "中证1000",
    "588000.SH": "科创50", "159915.SZ": "创业板", "510050.SH": "上证50",
}
sector_etfs = {
    "512880.SH": "证券ETF", "512690.SH": "食品饮料", "159766.SZ": "旅游ETF",
    "515790.SH": "光伏ETF", "159949.SZ": "创业板50", "512010.SH": "医药ETF",
}
```

**区间份额与环比（注意字段名与排序）：**

```python
resp = call_tool("get_fund_share_range", {
    "ts_code": ts_code,
    "start_date": "<30 交易日前 YYYY-MM-DD>",
    "end_date": "<今天 YYYY-MM-DD>",
})
items = resp["data"]["items"]   # 字段含 fd_share（非 fund_share）
# items 按 trade_date 升序: items[0] 最旧, items[-1] 最新 — 与 get_daily_basic_range 相反
old_share = float(items[0]["fd_share"])
new_share = float(items[-1]["fd_share"])
change_pct = (new_share - old_share) / old_share * 100
```

**数据延迟：** fund_share 常滞后数日；SH（510xxx）往往慢于 SZ（159xxx）。报告中份额可用万单位：`fd_share / 10000`。

**输出样式**遵守 [`../_shared/wechat-brief-output.md`](../_shared/wechat-brief-output.md)；晨报标题示例：`━━ 基金份额晨报 YYYY-MM-DD ━━`，正文含宽基/行业变化与趋势判断段落。

### Step 1: 检查系统通路（09:00 及以后窗口）

- **Tushare MCP：** `health_check`，必要时 `tools/list`。  
- **QMT MCP：** `initialize` session → `health_check`（StreamableHTTP 规则见 `signal-trader` §StreamableHTTP）。  
- **Cron 环境** JSON-RPC 与 httpx 模板：[`../_shared/mcp-jsonrpc-cron-pattern.md`](../_shared/mcp-jsonrpc-cron-pattern.md)。

### Step 2–10: 交易日历、信号、研究员、竞价、下单

自本版本起 **不在此重复** 信号拉取、技术评分维度、集合竞价阈值、资金拆单等 — 一律执行 **`signal-trader` 阶段 A–D** 对应小节。  
**成交核对**仍以 **`get_positions`** 为准（`get_today_orders.status` 不可靠），见 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

**可选结构化衔接（给 `closing-review`）：** 若流水线能写 JSON，推荐格式见 [`../_shared/morning-run-context.example.json`](../_shared/morning-run-context.example.json)；未实现前收盘 skill **不依赖**该文件。

## Dependencies

- [`signal-trader`](../signal-trader/SKILL.md)（阶段 A–D/E 唯一事实来源）  
- [`../_shared/`](../_shared/)（Cron、微信、QMT 陷阱）  
- Tushare MCP、QMT MCP 可用

## Cron 配置参考（部署示例）

三个定时任务链式联动；**执行下单**仍须在 09:27 计划后由用户 **`Y`** 确认。

**任务0：基金份额晨间分析 (08:00)**

```yaml
schedule: "0 8 * * 1-5"
name: "基金份额晨间分析 08:00"
skills: [daily-morning-check]
deliver: origin
```

**任务1：系统自检和信号识别 (09:00)**

```yaml
schedule: "0 9 * * 1-5"
name: "系统自检和信号识别 09:00"
skills: [daily-morning-check, signal-trader]
deliver: origin
```

**任务2：竞价修正+交易计划 (09:27)**

```yaml
schedule: "27 9 * * 1-5"
name: "竞价修正+交易计划 09:27"
skills: [daily-morning-check, signal-trader]
context_from: ["任务1的job_id"]
deliver: origin
```

**非交易日：** `get_trade_calendar`；`is_open=0` 则直接结束。09:00 无候选时 09:27 应快速结束。

## Pitfalls

完整表见 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。**补充：** `get_fund_share_range` 字段为 `fd_share`；SH/SZ ETF 更新延迟不同；Cron 创建时刻晚于当日触发点会跳到下一交易日，见原运维备注。

<!-- version: 1.2.1 last_updated: 2026-05-13 -->
