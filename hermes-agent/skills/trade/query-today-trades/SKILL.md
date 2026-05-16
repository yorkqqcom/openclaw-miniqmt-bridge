---
name: query-today-trades
description: >-
  Read today's fills/trades for a locked account_id via get_today_trades. Use for PnL
  attribution and reconciliation; pair with get_positions when needed.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, query]
    related_skills: [switch-account, signal-trader, query-today-orders, closing-review]
    requires_soul: profiles/trade/SOUL.md
    token_cost: low
---

# query-today-trades — 当日成交查询（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

调用 **`get_today_trades(account_id='...')`** 获取当日成交记录，用于 **归因、对账、复盘** 输入。与 [`query-today-orders`](../query-today-orders/SKILL.md) 互补。

## When to Use

- 用户要「今日成交、成交明细、盈亏核对数据」等。
- [`closing-review`](../closing-review/SKILL.md) 需成交侧事实时的 **只读** 步骤。

## When NOT to Use

- 仅查挂单状态 → [`query-today-orders`](../query-today-orders/SKILL.md)。
- 判断是否 **当前持仓** 仍以 **`get_positions`** 为准；成交列表与持仓不一致时以柜台逻辑排查，链 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

## Prerequisites

`account_id` 已锁定；API + MCP。

## 执行步骤

1. `get_today_trades(account_id='<logical_id>')`。
2. 若与委托/持仓对账 → 可交叉 `get_today_orders`、`get_positions`（不重复解释坑点，链 `_shared`）。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)（工具表 `get_today_trades`）
- [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)

## Verification Checklist

- [ ] 命名参数 `account_id`
- [ ] 已向用户说明与 `query-today-orders` 的分工（若易混淆）
