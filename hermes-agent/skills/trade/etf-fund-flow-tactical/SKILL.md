---
name: etf-fund-flow-tactical
description: "Use when user asks for ETF or mutual fund share changes, share change daily summary, holdings diff, or tactical fund flow beyond the morning cron. Read-only; distinguishes unavailable vs empty result."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, etf, fund, read-only]
    related_skills: [daily-morning-check, signal-trader]
    requires_soul: profiles/sent/SOUL.md
---

# etf-fund-flow-tactical — 公募/ETF 份额与持仓战术（只读）

## Overview

按需拉取 `get_fund_share_range`、`get_fund_share_change_range`、`get_fund_share_change_daily_summary_range`、`get_fund_portfolio_report`、`get_fund_holdings_diff_stock` / `get_fund_holdings_diff_industry`。与 **08:00 晨间编排** 的关系：固定 ETF 清单与 cron JSON-RPC 见 [`../daily-morning-check/SKILL.md`](../daily-morning-check/SKILL.md) 与 [`../_shared/mcp-jsonrpc-cron-pattern.md`](../_shared/mcp-jsonrpc-cron-pattern.md)；本 Skill **不重复** 编排时间表。

## 基金 diff / 物化（MUST 语义）

- **`get_fund_holdings_diff_*` 返回空**：**MUST** 判断是否 **未物化 / 过滤列为 NULL**（工具仍成功） versus **两期对比结果确实为零**。前者在「缺失维度」写 **基金重仓对比不可用（未物化或过滤列未命中）**；后者写 **对比结果为空（数据可用）**。**禁止**将两者混为一谈让用户误以为「无资金变化」。

- 物化与排查线索见 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) Pitfall #19 及 [`../signal-trader/references/fund-flow-macro-context.md`](../signal-trader/references/fund-flow-macro-context.md)。

## Steps

1. 选定 `ts_code`（ETF）与日期窗；`get_fund_share_change_range` 看 `delta_pct` 等字段（以 MCP 响应为准）。
2. 全市场日汇总：`get_fund_share_change_daily_summary_range`（若部署启用）。
3. 季报持仓：`get_fund_portfolio_report`（`end_date` 须季度末日，见 signal-trader Pitfall #13）。
4. **数据质量声明**（格式见 [`../equity-research-pack/SKILL.md`](../equity-research-pack/SKILL.md)「数据质量声明」节）**MUST** 显式写出 diff 维度属于「不可用」还是「空结果」。

## When NOT to Use

- 需要 **下单** → `signal-trader` / `buy-single` 等。

<!-- version: 1.0 last_updated: 2026-05-16 -->
