# MCP 数据支持全景（2026-05-07审计）

## 与《数据资源目录》的关系（真源分层）

- **能力全集（表级 + 工具签名 + 缺口说明）**：以仓库内 **[`docs/DATA_AND_MCP_RESOURCE_CATALOG.md`](../../../../../docs/DATA_AND_MCP_RESOURCE_CATALOG.md)** 为准（对齐远端 `tushare-hermes-mcp` 的 `TOOL_SCHEMAS`；当前文档记述为 **42** 项工具）。该目录描述的是 **数据 MCP 所在工程** 的主库与网关，**非**本仓库 `mcp_server/` 路径。
- **本文档**：**本部署 / 本环境实测** 的快照（哪些工具有返回、哪些表为空、哪些依赖物化任务）。工具 **数量与版本** 可能随远端发布与本地审计日期与目录略有差异；**以远端 `tools/list` 与目录 §4 为准**做能力核对，以本文及 **preflight 产物**（见 [`../../scripts/preflight_data_readiness.py`](../../scripts/preflight_data_readiness.py)）做运行前可用性判断。
- **冲突时**：目录定义「有没有这个工具」；本文 + `data_readiness.json` 回答「当前连上 MCP 后能不能拿到非空业务数据」。

Tushare MCP（本文审计时 **40** 工具；目录对齐版本为 **42**，以远端为准）+ QMT MCP（16 工具）数据可用性审计。

## Tushare MCP 数据状态

### 🟢 信号/预测 — 有数据

| 工具 | 参数 | 数据量 |
|------|------|:------:|
| `get_prediction_results` | query_type=by_trade_date, trade_date=最新交易日 | 500+条 |
| `get_prediction_active_range` | ts_code + start_date/end_date | 按标的有数据 |
| `get_prediction_result_aggregates` | 无参 | 全库9856条 |

### 🟡 信号/预测 — 空/不稳定

| 工具 | 原因 | 替代方案 |
|------|------|----------|
| `get_prev_trade_day_signals` | model_path_like 大小写敏感，新管道路径用小写 | `get_prediction_results` 手动过滤 |
| `get_prediction_statistics_rows` | 表无记录 | — |
| `get_prediction_ranking_rows` | 表无记录 | — |

### 🟢 行情 — 有数据

| 工具 | 说明 |
|------|------|
| `get_stock_snapshot` | 个股快照，响应在 data.stock / data.quote（不是 items[]） |
| `get_daily_basic_range` | 日线数据完整，⚠️ items[0]=最新（倒序） |
| `get_moneyflow_summary` | 资金流向，响应在 data.summary / data.latest_day（不是 items[]） |
| `get_index_daily_range` | 指数日线（000001.SH 上证综指等） |
| `get_adj_factor_range` | 复权因子 |

### 🟡 行情 — 有条件

| 工具 | 条件 |
|------|------|
| `get_realtime_quotes_latest` | 仅交易时段09:25-15:00有数据，非交易时段返回空 |
| `get_features_snapshot` | 返回数据量大，但 trend/support/resistance 等字段多返回 `?` |

### 🟢 基本面-排雷 — 有数据

| 工具 | 说明 |
|------|------|
| `scan_announcement_risk` | ✅ 2026-05-07修复，DeepSeek已配好，可用 |
| `get_risk_digest` | 批量版，支持 ts_codes=[...] 多只同时查 |
| `list_cninfo_announcements_range` | 巨潮公告原文，无需API Key |

### 🟢 基本面-主营/财务 — 有数据

| 工具 | 字段 |
|------|------|
| `get_fina_mainbiz_latest` | bz_item(业务名), bz_sales(收入), bz_profit(利润), bz_cost(成本) |
| `get_rpt_fina_segment_quality(company_quality)` | ROIC, ROA, 毛利率, 净利率, OCF/OP, 合同负债 |
| `get_rpt_fina_segment_quality(dol_proxy)` | op_yoy, tr_yoy, dol_proxy(经营杠杆) |
| `get_rpt_fina_segment_quality(segment_line)` | ⚠️ 0条（未物化） |
| `get_rpt_fina_segment_quality(segment_concentration)` | ⚠️ 0条（未物化） |
| `get_rpt_fina_segment_quality(mainbz_vs_income)` | ⚠️ 0条（未物化） |
| `get_fina_statement_range(income/balancesheet/cashflow)` | 三张报表数据完整 |
| `list_business_tags_snapshots` | AI标签 + supply_role（供应链角色） |

### 🟡 主营业务链路 — 无数据（需跑流水线）

| 工具 | 状态 |
|------|:----:|
| `list_mainbiz_runs` | 0条运行记录 |
| `get_mainbiz_run_metrics_latest` | 无记录 |
| `list_mainbiz_relations_latest` | 无数据 |
| `list_mainbiz_relations_by_run` | 需要run_id |

### 🟢 基金 — 有数据

| 工具 | 说明 |
|------|------|
| `get_fund_basic_snapshot` | 基金列表（market=E=ETF） |
| `get_fund_company_snapshot` | 基金公司信息 |
| `get_fund_portfolio_report` | 单基金季报持仓，返回前N大持仓 |
| `get_fund_share_range` | 基金份额日线 |
| `get_fund_share_change_range` | 份额日环比变动（delta_pct） |

### 🟡 基金 — 需物化

| 工具 | 状态 | 解决 |
|------|:----:|------|
| `get_fund_holdings_diff_stock` | 0条 | 需 materialize_holdings_diff() |
| `get_fund_holdings_diff_industry` | 0条 | 同上 |

## QMT MCP 数据状态

| 工具 | 状态 | 说明 |
|------|:----:|------|
| `health_check` | 🟢 | 返回 xtqmt_state: READY |
| `list_accounts` | 🟢 | 列出各 logical_id（须据此选择，无固定默认） |
| `get_account_assets` | 🟢 | total_asset/cash/market_value |
| `get_positions` | 🟢 | symbol/quantity/cost_price/market_value/unrealized_pnl |
| `get_today_orders` | 🟢 | ⚠️ status 字段可能不更新，始终显示 SUBMITTED |
| `get_today_trades` | 🟢 | 实际成交明细 |
| `get_quote` | 🟡 | 需 QMT 客户端在线 |
| `get_trade_stats` | 🟢 | 交易统计 |
| `place_limit_order` | 🟢 | 支持 client_order_id 幂等键 |
| `get_history_orders` | 🟢 | 历史委托 |
| `get_history_trades` | 🟢 | 历史成交 |
| `get_history_assets` | 🟢 | 历史资产 |
| `get_pnl_curve` | 🟢 | 盈亏曲线 |

## 实际分析能力覆盖

| 分析维度 | 支持情况 | 关键依赖 |
|----------|:--------:|----------|
| 信号识别+过滤 | ✅ 全量 | get_prediction_results |
| 技术评分(量价/资金/位置) | ✅ 全量 | stock_snapshot + daily_basic + moneyflow |
| 基本面排雷 | ✅ 全量 | scan_announcement_risk / get_risk_digest |
| 主营构成+毛利率 | ✅ 全量 | get_fina_mainbiz_latest |
| 财务质量(ROIC/OCF) | ✅ 全量 | company_quality + dol_proxy |
| 供应链角色定位 | ✅ 全量 | business_tags_snapshots (supply_role) |
| 基金持仓查询 | ✅ 有数据 | fund_portfolio_report (仅大中盘股在top持仓) |
| 基金份额变动 | ✅ 有数据 | fund_share_change_range |
| 供应链关系图谱 | ❌ 需流水线 | mainbiz_relations (0条) |
| 两期基金重仓对比 | ❌ 需物化 | fund_holdings_diff (0条) |
| 深度特征分析 | ⚠️ 字段多空 | features_snapshot (trend 等返回?) |

## 目录 §4.1 工具名交叉索引（与 `docs/DATA_AND_MCP_RESOURCE_CATALOG.md` 对齐）

以下 **MCP 工具名** 与目录 **§4.1 工具总表** 一致；若上文某小节未逐行展开，仍视为本文已「提及」，供 `scripts/check_catalog_tool_mentions.py` 弱校验对齐。

`health_check` `get_stock_snapshot` `get_moneyflow_summary` `get_daily_basic_range` `get_adj_factor_range` `get_adjusted_quote_range` `get_trade_calendar` `get_trade_calendar_statistics` `get_index_basic_list` `get_index_daily_range` `get_prev_trade_day_signals` `get_prediction_results` `get_prediction_result_aggregates` `get_prediction_statistics_rows` `get_prediction_ranking_rows` `get_features_snapshot` `get_prediction_active_range` `scan_announcement_risk` `get_risk_digest` `get_announcement_pdf_text_cache` `list_cninfo_announcements_range` `list_tushare_announcements_range` `get_risk_scan_cache` `get_fina_mainbiz_latest` `get_fina_statement_range` `get_rpt_fina_segment_quality` `list_business_tags_snapshots` `get_industry_moneyflow_aggregate` `list_mainbiz_runs` `list_mainbiz_relations_by_run` `get_mainbiz_run_metrics_by_run` `list_mainbiz_relations_latest` `get_mainbiz_run_metrics_latest` `get_realtime_quotes_latest` `get_fund_basic_snapshot` `get_fund_company_snapshot` `get_fund_portfolio_report` `get_fund_share_range` `get_fund_holdings_diff_stock` `get_fund_holdings_diff_industry` `get_fund_share_change_range` `get_fund_share_change_daily_summary_range`
