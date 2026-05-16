# Tushare MCP Data Field Mapping

Hard-won field names from the `tushare-hermes-mcp` (v0.2.2) service at `172.24.144.1:8001/mcp`.

## version History

| Version | Date | Changes |
|---------|------|---------|
| v0.2.1 | — | Base: ~30 tools |
| v0.2.2 | 2026-05-05 | +4 fund tools → 34 tools total |
| v0.2.2(+3) | 2026-05-05 | +3 fund tools → 37 tools |
| **v0.3.0** | **2026-05-06** | **+1 tool → 38 tools. Added: get_fina_statement_range, list_cninfo_announcements_range, get_prediction_active_range, get_rpt_fina_segment_quality, list_tushare_announcements_range, get_risk_scan_cache |

---

## get_stock_snapshot
```json
{
  "data": {
    "stock": { "ts_code", "symbol", "name", "industry", "market", "list_status" },
    "quote": {
      "trade_date": "2026-04-30",
      "open": 8.4,
      "high": 8.44,
      "low": 8.32,
      "close": 8.36,
      "pre_close": 8.38,
      "pct_chg": -0.2387,
      "vol_hand": 77040,
      "amount_k_cny": 64429.8
    }
  }
}
```

## get_moneyflow_summary

```json
{
  "data": {
    "ts_code": "603399.SH",
    "start_date": "...",
    "end_date": "...",
    "days": 8,
    "summary": {
      "net_mf_amount_total_wan": -23633.56,
      "net_mf_amount_avg_wan": -2954.195,
      "main_buy_amount_total_wan": 211399.11,
      "main_sell_amount_total_wan": 191185.98,
      "main_net_amount_total_wan": 20213.13
    },
    "latest_day": {
      "trade_date": "2026-04-30",
      "net_mf_amount_wan": -16850.43,
      "buy_lg_amount_wan": 2590.7,
      "buy_elg_amount_wan": 8404.15,
      "sell_lg_amount_wan": 4535.89,
      "sell_elg_amount_wan": 1371.65
    }
  }
}
```

**主力当日净额计算：**
```python
latest_main_net = (buy_lg + buy_elg) - (sell_lg + sell_elg)
```

## get_daily_basic_range

**⚠️ items 按 trade_date 倒序排列！** `items[0]` = 最新。`items[-1]` = 最旧。切勿用 `items[-20:]` 算MA！

```json
{
  "data": {
    "items": [
      {
        "trade_date": "2026-04-30",
        "close": 19.39,
        "turnover_rate": 1.6964,
        "turnover_rate_f": 2.1181,
        "volume_ratio": 0.14,
        "pe": null,
        "pe_ttm": null,
        "pb": 6.1339,
        "ps": 1.8324,
        "total_share": 51229.06,
        "float_share": 51229.06,
        "free_share": 41029.06,
        "total_mv": 993331.57,
        "circ_mv": 993331.57
      }
    ]
  }
}
```

**正确闭包：**
```python
items = data["items"]
closes = [i["close"] for i in items[:20]]   # 最近20日
latest = items[0]
hi_20 = max(closes); lo_20 = min(closes)
pos_pct = (latest["close"] - lo_20) / (hi_20 - lo_20) * 100
total_mv_yi = items[0]["total_mv"] / 10000
```

## get_fina_statement_range

### statement=income
```json
{
  "items": [{ "end_date": "2026-03-31", "revenue": 812446075.83, "net_profit": null }]
}
```
### statement=indicator
```json
{
  "items": [{ "end_date": "2026-03-31", "roe": -0.9233, "eps": -0.0489, "gross_profit_margin": null, "net_profit_margin": null }]
}
```
### statement=balancesheet
Fields: `total_assets`, `total_liabilities`, `current_assets`, `current_liabilities`

## get_fina_mainbiz_latest
```json
{
  "data": { "items": [{ "bz_name": "太阳能热水器", "revenue_percent": 45.2, "profit_margin": 32.1 }] }
}
```

## get_trade_calendar
```json
{
  "data": { "items": [{ "cal_date": "2026-05-01", "is_open": "0", "pretrade_date": "2026-04-30" }] }
}
```

## get_prev_trade_day_signals
```json
{
  "data": {
    "base_date": "2026-05-05", "trade_date": "2026-04-30", "count": 15,
    "items": [{ "ts_code": "603399.SH", "name": "永杉锂业", "confidence": 0.772146, "model_path": "models/ModelB_hfq_main.pkl" }]
  }
}
```

## get_realtime_quotes_latest
```json
{
  "data": {
    "items": [{ "ts_code": "600000.SH", "trade_date": "2026-04-30", "open": null, "pre_close": 9.38, "bid_price": null, "ask_price": null, "volume": null }]
  }
}
```

## Common Pitfalls (跨工具)

1. **daily_basic 排序**：`items[0]` = 最新，`items[-1]` = 最旧。切勿用 `items[-20:]` 算MA！
2. **market value 单位**：`total_mv` 单位是 **万元**，转亿元需 ÷10000
3. **moneyflow 主力净额**：5日汇总用 `summary.main_net_amount_total_wan`，最后一日需自算
4. **PE 可能为 null**：亏损股的 PE 是 null 而不是 0
5. **daily_basic 可能有数据缺口**：最新日期可能晚于实际最新交易日
6. **stock_snapshot 校验**：`quote.close` 应与 daily_basic `items[0].close` 一致

## get_features_snapshot（200+特征）

### K线形态
| 特征 | 说明 |
|------|------|
| `price_action_doji/hammer/shooting_star/engulfing/harami` | 形态识别(0/1) |
| `price_action_body_direction` | 实体方向(-1阴/1阳) |
| `price_action_buying/selling_pressure` | 买卖压(0~1) |

### 趋势
| 特征 | 说明 |
|------|------|
| `price_action_trend_direction_5/10/20/50` | 趋势方向(-1/0/1) |
| `price_action_trend_strength_5/10/20/50` | 趋势强度(0~1) |
| `price_action_trend_slope_5/10/20/50` | 趋势斜率 |

### 支撑压力
| 特征 | 说明 |
|------|------|
| `price_action_distance_to_support/resistance` | 距支撑/压力位距离 |
| `price_action_support/resistance_strength` | 支撑/压力强度 |
| `price_action_breakout_probability` | 突破概率 |
| `price_action_price_position` | 价格在区间位置(0~1) |

### 用法
- 短期方向：`trend_direction_5/10` + `breakout_probability`
- 位置评分：`price_position`（0=低位,1=高位）
- K线形态：`doji`/`hammer`/`engulfing` 作为看涨/看跌论据

---

## get_rpt_fina_segment_quality

| view | 状态 |
|------|:----:|
| `company_quality` | ✅ 有数据 |
| `dol_proxy` | ✅ 有数据 |
| `segment_line/concentration/mainbiz_vs_income` | ⚠️ 0条 |

**company_quality 字段：** `total_revenue`, `operate_profit`, `n_cashflow_act`, `ocf_to_op`, `wc_simplified`, `wc_to_revenue`, `contract_liab`, `profit_dedt`, `roic`, `roa`, `grossprofit_margin`, `netprofit_margin`

**dol_proxy 字段：** `op_yoy`, `tr_yoy`, `dol_proxy`(>1高杠杆, ~1适中, <1低杠杆)

---

## get_prediction_results

| 模型 | 状态 |
|------|:----:|
| `models/ModelB_hfq_main.pkl` | ✅ 有信号 |
| `models/ModelB_hfq_Second.pkl` | ⚠️ 0条 |

**全库统计：** `up_ratio=0.5457` (偏多), `avg_confidence=0.5591`

---

## list_cninfo_announcements_range (巨潮公告查询 v0.3.0)

**替代 `scan_announcement_risk` 做排雷！** 不需要API Key，直接查巨潮公告原文。

```json
{
  "data": { "items": [
    {
      "announcement_id": "1224944449",
      "sec_code": "600860",
      "sec_name": "京城股份",
      "announcement_time": "2026-01-21T16:00:00",
      "title": "京城股份2025年年度业绩预亏的公告",
      "adjunct_url": "finalpage/2026-01-22/..."
    }
  ]}
}
```

**参数：** `ts_code`, `start_date`, `end_date`
**排雷规则：** 过滤标题含"预亏/减持/立案/调查/退市/ST/*ST/亏损"的公告
**日出东方示例：** 6条公告，含"董事及高级管理人员减持股份计划公告" → ⚠️ 减持风险

---

## list_tushare_announcements_range (Tushare公告)

类似 `list_cninfo_announcements_range`，数据来源不同（Tushare vs 巨潮信息网）。
参数：`ts_code`, `start_date`, `end_date`

---

## get_prediction_active_range

**用途：** 查询指定股票的活跃预测区间（哪些日期范围有预测结果）

| 参数 | 说明 |
|:----:|:------|
| `ts_code` | 股票代码(必填) |
| `start_date` | 起始日期 YYYY-MM-DD(必填) |
| `end_date` | 截止日期 YYYY-MM-DD(必填) |

---

## get_risk_scan_cache

**用途：** 读取风险扫描的缓存结果

| 参数 | 说明 |
|:----:|:------|
| `cache_key` | 缓存键(必填) |

---

## get_fina_statement_range (补充字段)

`get_fina_mainbiz_latest` 之外的财报数据补充：
- `statement=balancesheet` → `total_assets`, `total_liabilities`, `current_assets`, `current_liabilities`
- `statement=cashflow` → `n_cashflow_act`, `n_cashflow_inv`, `n_cashflow_fin`
- `statement=forecast` → 业绩预告
- `statement=express` → 业绩快报
- `statement=audit` → 审计意见
- `statement=dividend` → 分红方案
- `statement=disclosure_date` → 披露日期
