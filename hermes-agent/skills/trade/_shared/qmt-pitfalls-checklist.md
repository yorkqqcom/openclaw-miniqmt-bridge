<!--
last_updated: 2026-05-15
summary: 新增 QMT 坑点单行 checklist，供 Hermes 默认注入；详表见 qmt-pitfalls.md。
-->

# QMT 坑点速查（单行 checklist）

详版与表格：[`qmt-pitfalls.md`](qmt-pitfalls.md)。

1. **时间敏感**：结论前执行真实 `date` / 时钟，勿凭会话猜当前时刻。
2. **成交判定**：勿仅以 `get_today_orders.status` 为准；**以 `get_positions` 是否有仓交叉验证**。
3. **Session**：StreamableHTTP 会话易过期；长流程前重新 initialize（见 `signal-trader`）。
4. **限价不成交**：开盘后价离限价远属预期；用持仓与行情核对，勿盲目重复下单。
5. **解析**：`get_stock_snapshot` 用 `data.stock` + `data.quote`，勿盲用 `items[]`（见详版表）。

<!-- version: 1.0 last_updated: 2026-05-15 -->
