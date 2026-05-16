<!--
last_updated: 2026-05-15
summary: 消费方增加 query-today-trades；session 写回列批量原子 skill。
-->

# QMT 与数据侧常见陷阱（症状 → 影响 → 正确做法）

**速查（单行）**：[`qmt-pitfalls-checklist.md`](qmt-pitfalls-checklist.md)。

**消费方：** `signal-trader`、`daily-morning-check`、`closing-review`、[`query-today-orders`](../query-today-orders/SKILL.md)、[`query-today-trades`](../query-today-trades/SKILL.md)。修改任一条后请检查消费方 skill 是否仍硬编码相反做法。

| 症状 | 影响 | 正确做法 | 出处 |
|------|------|----------|------|
| 凭对话上下文报「现在 09:02」 | 错过 09:25 竞价等窗口 | 任何时间敏感结论前先执行 `date`（或等价真实时钟） | daily-morning-check 复盘 |
| QMT `get_today_orders` 的 `status` 长期 `SUBMITTED` | 误判未成交/已成交 | **成交以 `get_positions` 为准**；有持仓即视为成交 | daily-morning / signal-trader / closing-review |
| QMT session 数分钟后失效 | 下单返回 400 / 资产为 0 | 重要操作前 **重新 initialize**；见 `signal-trader` StreamableHTTP 小节 | signal-trader |
| 集合竞价后股价快速高于限价 | 买单挂场外不成交 | 预期内现象；可评估加价一档；未成交用持仓核对 | daily-morning 复盘 |
| `get_stock_snapshot` 用 `items[]` 解析 | 取不到数据 | 使用 `data.stock` + `data.quote` | daily-morning 数据表 |
| `get_moneyflow_summary` 用 `items[]` | 取不到汇总 | 使用 `data.summary` + `data.latest_day` | daily-morning 数据表 |
| `get_realtime_quotes_latest` 在 09:25 前调用 | 返回无实时数据 | **09:25 后**再拉竞价/开盘价相关字段 | daily-morning 数据表 |
| `get_prev_trade_day_signals` 返回 0 条 | 无候选信号 | 用 `get_prediction_results(by_trade_date)` 并手动筛 `prediction==1`、`probability_up` | signal-trader / daily-morning |
| `get_daily_basic_range` 的 `items` 方向搞反 | MA/分位算错 | **`items[0]` 为最新**，勿用 `items[-20:]` 当最近 20 日 | mcp-response-structures |
| `get_trade_calendar` 缺未来月份 | 非交易日误判 | 结合 `get_trade_calendar_statistics` 或库内实际覆盖说明 | daily-morning 数据表 |

**信号筛选：** 用户偏好使用 **`probability_up`** 而非 `confidence` 作为主要阈值字段（两者多数相等但不应混用）。

<!-- version: 1.2 last_updated: 2026-05-15 -->
