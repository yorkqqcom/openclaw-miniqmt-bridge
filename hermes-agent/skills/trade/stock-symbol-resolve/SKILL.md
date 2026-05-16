---
name: stock-symbol-resolve
description: >-
  Resolves Chinese stock name or fuzzy keyword to canonical ts_code / QMT symbol via MCP
  symbol_suggest; disambiguates multiple hits. Use when user gives company name or short name
  without .SH/.SZ suffix before trading or research tools need a precise symbol.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [symbol-resolution, a-share, xtqmt, trading-ops]
    related_skills: [signal-trader, buy-single, sell-single, buy-batch, sell-batch, switch-account]
    requires_soul: profiles/trade/SOUL.md
    token_cost: low
---

# stock-symbol-resolve — 中文名称 → 规范代码

语气与用户可见报告壳：见 [`profiles/trade/SOUL.md`](../../../profiles/trade/SOUL.md)（或研究向 [`profiles/ana/SOUL.md`](../../../profiles/ana/SOUL.md)）。

## Overview

只读 **证券标识解析**：将用户口述的 **公司名、简称、无后缀六位码** 转为可下单 / 可拉行情的 **`symbol`（如 `601398.SH`）** 或等价 `ts_code`。**本 Skill 不下单**。

## When to Use

- 用户未提供 `XXXXXX.SH` / `XXXXXX.SZ` 形式，且后续要调用 `place_limit_order`、`get_quote` 等需精确代码的工具。
- `signal-trader` 或其它编排内，在写单前标识未锁定。

## When NOT to Use

- 用户已给出完整带交易所后缀代码且与账户市场一致。
- 非 A 股或未部署 xtqmt `symbol_suggest` 的环境。

## Prerequisites

与 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 多账户协议及仓库根 [`readme.md`](../../../../readme.md) §5.4 一致：API、connect、MCP 可用。

## 执行步骤

1. 取用户关键字 `keyword`（公司全称、简称或片段）。
2. 调用 xtqmt MCP **`symbol_suggest`**，`keyword` = 上述关键字（见 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 工具表 `symbol_suggest` 行）。
3. **禁止**在未调用 `symbol_suggest`（及约定回退）前，凭模型记忆输出六位码或后缀。
4. **多命中**：列出每条 **名称 + 完整代码 + 交易所**，请用户 **明确选一** 或补充字号。
5. **单命中**：仍建议回显「将使用 `ts_code` / `symbol`，是否确认」再交给下游（与 Soul 对齐）。
6. **回退（SHOULD）**：`symbol_suggest` 无合理结果时，再使用环境中已配置的 Tushare MCP（如 `stock_basic` 等）检索；**禁止**无工具调用编造代码。
7. **后缀与格式**：与 [`signal-trader` 中 A 股代码与 QMT `symbol` 约定](../signal-trader/SKILL.md) 保持一致；细则 **只引用真源**，不在本文另写冲突规则。

## Dependencies

- 策略真源与工具顺序：[`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)
- 下单前账户锁定：[`../switch-account/SKILL.md`](../switch-account/SKILL.md)

## Pitfalls

- 名称重名、AH 同名：必须用户确认，不得默认选第一条。

## Verification Checklist

- [ ] 输出代码均来自 `symbol_suggest` 或已声明的回退工具响应字段
- [ ] 多候选时已得用户明确选择
