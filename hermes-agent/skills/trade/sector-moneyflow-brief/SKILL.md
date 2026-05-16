---
name: sector-moneyflow-brief
description: "Use when user asks for industry or thematic money flow summary using get_industry_moneyflow_aggregate within calendar bounds (≤92 days). Read-only; mandatory data quality declaration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, sector, moneyflow, read-only, sent]
    related_skills: [signal-trader]
    requires_soul: profiles/sent/SOUL.md
---

# sector-moneyflow-brief — 行业/主题资金流简报（只读）

## Overview

使用 `get_industry_moneyflow_aggregate`（`scheme` a 或 b 按需求）+ `get_trade_calendar` 对齐 **交易日区间**（工具要求区间 **≤92 天**）。**只读**，无交易话术。

## When to Use

- 「行业资金」「主题资金流」「北向/主力在行业层面」等（以 MCP 实际字段为准）。

## Steps

1. `get_trade_calendar` 确认 `start_date` / `end_date` 为有效交易日窗口且长度 ≤92 日。
2. `get_industry_moneyflow_aggregate(start_date, end_date, scheme=a|b, …)`。
3. 输出行业排序表 + **数据质量声明**（格式见 [`../equity-research-pack/SKILL.md`](../equity-research-pack/SKILL.md)「数据质量声明」节）。

## Pitfalls

- 超过 92 日 MUST 拆段多次调用并在声明中说明合并方式，或缩小窗口。
- 若返回空：**区分**「工具错误/未配置」（unavailable）与「区间内真实无成交/无聚合行」（partial 或 full + 说明）。

<!-- version: 1.0 last_updated: 2026-05-16 -->
