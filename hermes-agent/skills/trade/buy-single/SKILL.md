---
name: buy-single
description: >-
  Single-symbol A-share limit BUY via place_limit_order when user already has price/amount
  and locked account_id; requires canonical symbol or prior stock-symbol-resolve. Not for
  full signal-trader pipeline.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, a-share, limit-order]
    related_skills: [stock-symbol-resolve, switch-account, signal-trader, buy-batch]
    requires_soul: profiles/trade/SOUL.md
    token_cost: medium
---

# buy-single — 单标的限价买入（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

在 **不跑** `signal-trader` 完整阶段 A–D 的前提下，对 **单标的** 发起 **`place_limit_order`（BUY）**。策略阈值与阶段定义 **不在本文维护**。

## When to Use

- 用户已确认 **数量、限价**，且 **`account_id` 已锁定**（见 [`switch-account`](../switch-account/SKILL.md)）。
- 标的代码已由 [`stock-symbol-resolve`](../stock-symbol-resolve/SKILL.md) 解析，或用户给出 **规范** `symbol`（`^\d{6}\.(SH|SZ)$`）。

## When NOT to Use

- 用户要「信号交易 / 研究员流程 / 早盘全套」→ 主读 [`signal-trader`](../signal-trader/SKILL.md)。
- 多标的并行买入 → [`buy-batch`](../buy-batch/SKILL.md)（或 MCP `place_limit_order_batch` 回退见该文）。

## Prerequisites

1. HTTP API + MCP；目标账户已在 API 侧 **connect**（联调顺序见仓库根 [`readme.md`](../../../../readme.md) §5.4；多账户见 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)）。
2. **`symbol` 守卫**：若 `symbol` **不符合** `^\d{6}\.(SH|SZ)$`，或用户仅提供中文名/无后缀码，**必须先**完成 [`stock-symbol-resolve`](../stock-symbol-resolve/SKILL.md)；**不得**编造代码后继续下单。
3. 多账户：须满足 [`signal-trader` 多账户执行协议](../signal-trader/SKILL.md#多账户执行协议)；含 Y/N 或限价确认前须 [`switch-account`](../switch-account/SKILL.md) 或等价锁定。

## 合规（硬性）

凡展示限价计划或 Y/N：**首行** `当前操作账户 account_id=<logical_id>` — 见 [`signal-trader` #account-id-user-facing](../signal-trader/SKILL.md#account-id-user-facing)。

## 执行步骤

1. `health_check` → 确认 `account_id` 与连接。
2. 校验 `symbol` 与上节 **Prerequisites**。
3. `place_limit_order(account_id='<logical_id>', side='BUY', symbol=..., price=..., amount=...)`；**新单**使用新 UUID 作 `client_order_id`；**重试同一笔**须复用同一 `client_order_id`（见真源 Common Pitfalls）。
4. 成交核对：勿仅信 `get_today_orders` 的 `status`；以 **`get_positions`** 交叉验证（链 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md) 与真源）。

## Post-execution（SHOULD）

若运行时使用 JSON 会话快照：下单或撤单改变柜台事实后，按 [`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md) 更新或通知外部存储（渐进收紧）。

## Dependencies

- 真源：[`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- MCP 工具签名：仓库 [`.cursor/skills/hermes-xtqmt-mcp/SKILL.md`](../../../../.cursor/skills/hermes-xtqmt-mcp/SKILL.md)

## Verification Checklist

- [ ] 首行含 `account_id=`（若对用户输出确认或结果）
- [ ] `symbol` 来源合规（suggest 或用户规范输入）
- [ ] 已读真源幂等与持仓校验段落
