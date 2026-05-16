---
name: sell-single
description: >-
  Single-symbol A-share limit SELL via place_limit_order when user has price/amount and
  locked account_id; requires canonical symbol or prior stock-symbol-resolve. Not for full
  signal-trader Day3 pipeline alone.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, a-share, limit-order]
    related_skills: [stock-symbol-resolve, switch-account, signal-trader, sell-batch]
    requires_soul: profiles/trade/SOUL.md
    token_cost: medium
---

# sell-single — 单标的限价卖出（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

对单标的发起 **`place_limit_order`（SELL）**，不包含 `signal-trader` 阶段 E 的完整竞价与拆单策略细节 — **复杂卖出逻辑仍以真源为准**。

## When to Use

- 用户明确卖出 **数量、限价**，`account_id` 已锁定，`symbol` 已规范或由 [`stock-symbol-resolve`](../stock-symbol-resolve/SKILL.md) 解析。

## When NOT to Use

- Day3 自动卖出编排、大仓位拆单阈值 → 主读 [`signal-trader` 阶段 E](../signal-trader/SKILL.md)。
- 多标的同时卖出 → [`sell-batch`](../sell-batch/SKILL.md)。
- 用户仅自然语言名称 → **先** `stock-symbol-resolve`。

## Prerequisites

同 [`buy-single`](../buy-single/SKILL.md)：`symbol` 守卫、`switch-account`、API+MCP、多账户协议链真源。

## 合规（硬性）

首行 `当前操作账户 account_id=<logical_id>` — [`signal-trader` #account-id-user-facing](../signal-trader/SKILL.md#account-id-user-facing)。

## 执行步骤

1. `health_check`。
2. 校验 `symbol` 与持仓是否足够（`get_positions`，`account_id` 命名参数）。
3. `place_limit_order(..., side='SELL', ...)`；`client_order_id` 与重试规则同真源。
4. 成交核对链 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

## Post-execution（SHOULD）

见 [`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md)。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- [`../../../../.cursor/skills/hermes-xtqmt-mcp/SKILL.md`](../../../../.cursor/skills/hermes-xtqmt-mcp/SKILL.md)

## Verification Checklist

- [ ] `account_id=` 话术合规
- [ ] 大卖单是否需拆单 — 对照真源阶段 E 与单笔上限
