# 预测信号与 `get_prev_trade_day_signals` 排障

**权威交易流程仍以** [`../SKILL.md`](../SKILL.md) **阶段 A 为准**；本文仅收拢 **信号源为 0 条** 时的根因与替代调用，避免在 `signal-trader` 主文档重复长段代码块。

## 现象：`get_prev_trade_day_signals` 返回 0 条

**根因**：该工具使用 `model_path_like='%ModelB_%'` 过滤。PostgreSQL 的 `LIKE` 对 `text` 列 **大小写敏感**。若库里模型路径为 `modelB_hfq_Second.pkl`（小写 `b`），则 `%ModelB_%`（大写 `B`）**不匹配**。

## 替代方案：使用 `get_prediction_results`

在确认前一交易日 `trade_date`（可用 `get_trade_calendar`）后：

```python
get_prediction_results(
    query_type="by_trade_date",
    trade_date="<YYYY-MM-DD 前一交易日>",
    limit=500,
)
# 在应用层手动过滤，例如：
# - prediction == 1 表示上涨/买入类信号（以远端字段语义为准）
# - probability_up > 0.62（阈值以 signal-trader 真源为准）
```

## `probability_up` 与 `confidence`

用户偏好以 **`probability_up`** 作为筛选字段（而非 `confidence`）。两者在多数行可能相等，但 **MUST** 在过滤与排序中统一使用 `probability_up`，与主 SKILL Pitfall #15 一致。

## 与 Pitfall 索引的对应关系

- 主文档 **Pitfall #14**：本问题的单行摘要 + 链至本文。
- 主文档 **步骤 0（信号获取）**：仅保留摘要句 + 链至本文。

## 相关参考

- [`mcp-data-availability.md`](mcp-data-availability.md) — 预测类工具数据量与空表说明
- [`mcp-response-structures.md`](mcp-response-structures.md) — 响应 JSON 形状与 **MCP 工具已知局限** 锚点

<!-- version: 1.0 last_updated: 2026-05-16 — 从 signal-trader 主 SKILL 抽离排障长文 -->
