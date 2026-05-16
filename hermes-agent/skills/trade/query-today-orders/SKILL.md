---
name: query-today-orders
description: >-
  Read today's orders for a locked account_id via get_today_orders. Use for order list
  or status review; do not infer fill solely from order status field.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, query]
    related_skills: [switch-account, signal-trader, cancel-order]
    requires_soul: profiles/trade/SOUL.md
    token_cost: low
---

# query-today-orders — 当日委托查询（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

调用 **`get_today_orders(account_id='...')`** 列出当日委托。**不**替代成交确认逻辑。

## When to Use

- 用户要「今日委托、挂单列表、某单状态」等只读查询。

## When NOT to Use

- 判断 **是否已成交** 勿**仅**依赖本接口返回的 `status`（可能长期 `SUBMITTED`）— 须 **`get_positions` 交叉验证**；见 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md) 与 [`../_shared/qmt-pitfalls-checklist.md`](../_shared/qmt-pitfalls-checklist.md)。

## Prerequisites

`account_id` 已锁定；API + MCP。

## 执行步骤

1. `get_today_orders(account_id='<logical_id>')`。
2. 若需判断是否成交 → 继续 `get_positions`（链真源与 `_shared`）。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)

## Verification Checklist

- [ ] 已向用户说明 `status` 字段局限性（或链到 pitfall 文档）
