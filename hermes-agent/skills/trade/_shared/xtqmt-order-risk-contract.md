<!--
last_updated: 2026-05-15
summary: xtqmt 写单硬风控与错误码约定（目标态）；Skill 与 Agent 行为说明。
-->

# xtqmt 下单风控（目标契约，Hermes-Agent）

## 目标态（MCP / API 服务端）

以下校验 **应在** `place_limit_order`、`place_limit_order_batch` **服务端**执行，Agent **不得**仅靠自身上下文「心算」替代：

- 黑名单标的
- 单账户当日累计亏损上限（需服务端可读历史成交）
- 单标的 / 板块仓位上限

拒绝时返回 **可解析错误**，建议统一业务码：**`RISK_REJECTED`**（或 HTTP 4xx 载荷中带同名字段），并附 **人类可读原因**。

## Agent 行为（Skill 层）

若工具返回 `RISK_REJECTED`（或等价）：**终止流程、告知用户、不得自动重试或绕过**。

若团队 **暂无法控制** xtqmt 实现：在运行手册中标注 **软校验 + 人工确认** 降级，并继续推动服务端硬化。

## 与文档关系

策略阈值真源仍为 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)；本文仅约束 **写单风控边界**。

<!-- version: 1.0 last_updated: 2026-05-15 -->
