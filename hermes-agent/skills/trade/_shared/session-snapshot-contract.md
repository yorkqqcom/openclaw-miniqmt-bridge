<!--
last_updated: 2026-05-15
summary: 会话 JSON 快照字段约定；供 Hermes 加载器注入与原子 Skill Post-execution 写回引用。
-->

# 会话状态快照（契约草案，Hermes-Agent）

**目的**：Cron 唤醒或多轮对话时，在 **system 顶部**（由加载器或编排第一步）注入一致上下文，避免 `account_id`、挂单与真实柜台漂移。

## 建议 JSON 字段（可扩展）

| 字段 | 类型 | 说明 |
|------|------|------|
| `schema_version` | string | 如 `"1.0"` |
| `updated_at` | string | ISO8601 |
| `active_account_id` | string | 当前逻辑账户 `logical_id` |
| `pending_stages` | string[] | 可选；编排未完成阶段 id，如 `stage_c` |
| `open_orders` | object[] | 可选；`{order_id, symbol, side}` 摘要 |
| `last_signal_batch_id` | string | 可选；晨间批次标识 |

存储介质（KV/DB/文件）由 **运行时** 决定；本文件只约定 **字段语义**。

## Cron 入口（如 `daily-morning-check`）

**SHOULD**：第一步 **读入/校验** 最新快照再进入 `signal-trader` 链；真源仍以 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 为准。

## 原子 Skill 写回（渐进）

`buy-single`、`buy-batch`、`sell-batch`、`cancel-order`、`cancel-orders-batch` 等改变委托事实成功后：**SHOULD** 更新外部存储中的 `open_orders` 或等价字段；首期可仅文档约定，由部署逐步实现。

## 机器可读示例

见 [`morning-run-context.example.json`](morning-run-context.example.json)（可选对齐字段名）。

<!-- version: 1.1 last_updated: 2026-05-15 -->
