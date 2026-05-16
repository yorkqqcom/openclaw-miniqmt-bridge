---
name: sell-batch
description: >-
  Multi-leg A-share limit SELL via place_limit_order_batch or sequential place_limit_order;
  symbols canonical or resolved; large positions may require chunked sells per signal-trader.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading-ops, xtqmt, a-share, limit-order, batch]
    related_skills: [stock-symbol-resolve, switch-account, signal-trader, sell-single]
    requires_soul: profiles/trade/SOUL.md
    token_cost: high
---

# sell-batch — 多笔/多标的限价卖出（原子）

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)。

## Overview

一次提交 **多笔限价卖出**。优先 **`place_limit_order_batch`**；否则逐笔 [`sell-single`](../sell-single/SKILL.md)。**大额拆单、单笔上限** 等以 [`signal-trader` 阶段 E](../signal-trader/SKILL.md) 与真源 Common Pitfalls 为准。

## When to Use

- 用户明确多标的卖出委托；`account_id` 已锁定；各 `symbol` 已规范或已解析。

## When NOT to Use

- Day3 编排内自动卖出逻辑 → 主读 `signal-trader` 阶段 E。
- 单笔 → [`sell-single`](../sell-single/SKILL.md)。

## Prerequisites

同 [`buy-batch`](../buy-batch/SKILL.md)：`symbol` 守卫、`client_order_id`、多账户、`get_positions` 校验可卖数量。

## 合规（硬性）

[`#account-id-user-facing`](../signal-trader/SKILL.md#account-id-user-facing)。

## 执行步骤

1. `health_check`；确认 batch 工具可用性。
2. 可用则 `place_limit_order_batch`（`side=SELL`…）；否则逐笔 `place_limit_order`，**大仓位拆单**链真源。
3. 成交与持仓核对链 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

## Post-execution（SHOULD）

[`../_shared/session-snapshot-contract.md`](../_shared/session-snapshot-contract.md)。

## Dependencies

- [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- [`../sell-single/SKILL.md`](../sell-single/SKILL.md)

## Verification Checklist

- [ ] 拆单与单笔金额上限已对照真源
- [ ] 账户首行话术合规
