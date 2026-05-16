---
name: prediction-signal-debug
description: "Use when user reports zero signals from get_prev_trade_day_signals, ModelB path mismatch, or needs get_prediction_results fallback steps. Read-only diagnostics; no trading."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, prediction, debug, read-only]
    related_skills: [signal-trader, equity-research-pack]
    requires_soul: profiles/tech/SOUL.md
---

# prediction-signal-debug — 预测信号排障（只读）

## Overview

收拢 **`get_prev_trade_day_signals` 返回 0 条**、`model_path_like` 大小写及 **`get_prediction_results` 回退** 的操作步骤。权威交易流程仍以 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 为准。

## When to Use

- 「没有信号」「prev_trade_day 是空的」「ModelB 匹配不到」等排障请求。
- 运维/研究员验证预测管道是否对 MCP 可见。

## Prerequisites

- 可读 [`../signal-trader/references/prediction-signal-troubleshooting.md`](../signal-trader/references/prediction-signal-troubleshooting.md)。

## Steps

1. 阅读排障专文（含替代 `get_prediction_results` 与 `probability_up` 约定）。
2. 用 `get_trade_calendar` 确认前一交易日 `trade_date`。
3. 调用 `get_prediction_results(query_type=by_trade_date, trade_date=…, limit=500)`，在应用层按专文过滤。
4. 将结论写入下方 **数据质量声明**（若仅排障无「分析结果」可写「本次为排障，无证券评级」）。

## 数据质量声明（MUST）

```markdown
## 数据质量声明
- 数据源: Tushare Hermes MCP
- 可用性: full | partial | unavailable
- 缺失维度: …
- 数据时点:
  - preflight: …
  - 本次调用: …（列出 `get_prev_trade_day_signals` / `get_prediction_results` 的摘要）
- 降级说明: …
```

## When NOT to Use

- 用户已明确要走完整 **信号交易买入** → 使用 `signal-trader` 阶段 A–D。

<!-- version: 1.0 last_updated: 2026-05-16 -->
