---
name: cancel-orders-batch
description: >-
  Cancel multiple open orders via cancel_orders_batch for a locked account_id; fallback
  to sequential cancel_order if batch tool unavailable.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, cancel, batch]
    related_skills: [switch-account, signal-trader, cancel-order, query-today-orders]
    requires_soul: profiles/trade/SOUL.md
    token_cost: medium
---

# cancel-orders-batch — 批量撤单（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

对同一 `account_id` 一次撤销 **多笔** 委托：优先 **`cancel_orders_batch`**；否则循环 [`cancel-order`](../cancel-order/SKILL.md)。

## When to Use

- 用户给出 **`order_ids` 列表**（或从前序 `get_today_orders` 明确多笔待撤），且账户已锁定。

## When NOT to Use

- 仅撤一单 → [`cancel-order`](../cancel-order/SKILL.md)。

## Prerequisites

API + MCP；[`signal-trader` 多账户协议](../signal-trader/SKILL.md#多账户执行协议)；`order_ids` 均属当前 `account_id`。

## 合规（硬性）

对用户说明批量撤单影响时，遵循 [`#account-id-user-facing`](../signal-trader/SKILL.md#account-id-user-facing)。

## 执行步骤

1. 确认 `cancel_orders_batch` 可用及参数名（见 MCP / [`hermes-xtqmt-mcp`](../../../../.cursor/skills/hermes-xtqmt-mcp/SKILL.md)）。
2. 可用：`cancel_orders_batch(account_id='...', order_ids=[...])`。
3. 不可用：对 `order_ids` 逐个 `cancel_order`，注意节奏与错误处理。

## Post-execution（SHOULD）

[`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md)。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- [`../cancel-order/SKILL.md`](../cancel-order/SKILL.md)

## Verification Checklist

- [ ] 无跨账户混用 `order_id`
- [ ] 撤单后可选 `get_today_orders` 复核
