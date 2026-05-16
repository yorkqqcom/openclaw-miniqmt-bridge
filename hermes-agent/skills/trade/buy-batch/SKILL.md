---
name: buy-batch
description: >-
  Multi-leg A-share limit BUY via place_limit_order_batch when MCP supports it; otherwise
  fall back to sequential place_limit_order per leg. Each symbol must be canonical or
  resolved via stock-symbol-resolve; account_id locked per signal-trader multi-account rules.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, a-share, limit-order, batch]
    related_skills: [stock-symbol-resolve, switch-account, signal-trader, buy-single]
    requires_soul: profiles/trade/SOUL.md
    token_cost: high
---

# buy-batch — 多笔/多标的限价买入（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

一次提交 **多笔限价买入**。优先 **`place_limit_order_batch`**；若工具不可用，则 **逐笔** [`buy-single`](../buy-single/SKILL.md) 并遵守间隔与幂等。策略与资金分配阈值 **不在本文维护** — 见 [`signal-trader`](../signal-trader/SKILL.md)。

## When to Use

- 用户已确认 **多标的** 各自的 `symbol`、价格、数量，且 `account_id` 已锁定。
- 多账户并行同标的：须按 [`signal-trader` 多账户执行协议](../signal-trader/SKILL.md#多账户执行协议) 逐户重复或 batch 工具支持时分节输出。

## When NOT to Use

- 完整信号/竞价/阶段流程 → [`signal-trader`](../signal-trader/SKILL.md)。
- 仅一单 → [`buy-single`](../buy-single/SKILL.md)。

## Prerequisites

1. API + MCP；每腿 **`symbol`** 均须 `^\d{6}\.(SH|SZ)$` 或经 [`stock-symbol-resolve`](../stock-symbol-resolve/SKILL.md)。
2. **`client_order_id`**：每笔唯一；多账户时按 `(account_id, 业务键)` 区分（链真源多账户节）。
3. 批量间隔、单笔金额上限等 **链真源** 阶段 D/E 与 Common Pitfalls，**不在此重复数值**。

## 合规（硬性）

对用户展示 **批量限价计划或 Y/N**：[`#account-id-user-facing`](../signal-trader/SKILL.md#account-id-user-facing) — 多账户时先 **`以下计划涉及 N 个账户`** 再分节，每节首行 `当前操作账户 account_id=…`。

## 执行步骤

1. `health_check`；确认 `place_limit_order_batch` 是否可用（以 MCP 工具列表为准）。
2. **若可用**：构造 batch 载荷（字段名以 MCP / [`hermes-xtqmt-mcp`](../../../../.cursor/skills/hermes-xtqmt-mcp/SKILL.md) 为准）。
3. **若不可用**：按评分或用户指定顺序，对每笔调用 `place_limit_order`，**间隔 ≥2 秒**（链真源）。
4. 成交核对：逐标的 `get_positions`，勿仅信 `get_today_orders.status` — [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

## Post-execution（SHOULD）

[`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md)。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- [`../buy-single/SKILL.md`](../buy-single/SKILL.md)（回退路径）

## Verification Checklist

- [ ] 每腿 `symbol` 来源合规
- [ ] 多账户话术与 `client_order_id` 不冲突
