---
name: cancel-order
description: >-
  Cancel one open order via cancel_order for a locked account_id. Use when user gives
  order_id or points to a single resting order to cancel.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, cancel]
    related_skills: [switch-account, signal-trader, query-today-orders]
    requires_soul: profiles/trade/SOUL.md
    token_cost: low
---

# cancel-order — 单笔撤单（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

调用 **`cancel_order(account_id, order_id)`** 撤销单笔委托。不涉及策略阶段。

## When to Use

- 用户给出 **`order_id`**（或已从前一步 `get_today_orders` 唯一确定一笔），且 **`account_id` 已锁定**。

## When NOT to Use

- 批量撤单 → 后续 `cancel-orders-batch`（`cancel_orders_batch`）。
- 未锁定账户或不确定 `order_id` → 先 [`switch-account`](../switch-account/SKILL.md) 与 [`query-today-orders`](../query-today-orders/SKILL.md)。

## Prerequisites

API + MCP；[`signal-trader` 多账户协议](../signal-trader/SKILL.md#多账户执行协议)。

## 合规（硬性）

对用户说明撤单影响时，若上下文可能被理解为写单类操作，**首行**含 `当前操作账户 account_id=<logical_id>` — [`#account-id-user-facing`](../signal-trader/SKILL.md#account-id-user-facing)。

## 执行步骤

1. 确认 `account_id` 与 `order_id`（通常来自 `get_today_orders`）。
2. `cancel_order(account_id='...', order_id='...')`。
3. 可选：再次 `get_today_orders` 核对状态。

## Post-execution（SHOULD）

见 [`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md)。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)

## Verification Checklist

- [ ] 未误用他户 `order_id`
- [ ] 命名参数 `account_id`
