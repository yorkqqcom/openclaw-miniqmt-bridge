# MCP 工具响应结构参考 (v0.2.2)

Tushare 本地 MCP 服务器 (172.24.144.1:8001, 本地Windows PostgreSQL)
每个工具的响应 JSON 结构不同，以下为实测确认的精确结构。

---

## get_stock_snapshot

```python
# 响应结构 (实测 2026-04-30)
{
    "success": True,
    "data": {
        "stock": {
            "ts_code": "603399.SH",
            "symbol": "603399",
            "name": "永杉锂业",
            "industry": "小金属",
            "market": "主板",
            "list_status": "L"
        },
        "quote": {
            "trade_date": "2026-04-30",
            "open": 19.39,
            "high": 19.39,
            "low": 19.39,
            "close": 19.39,
            "pre_close": 17.63,
            "pct_chg": 9.983,
            "vol_hand": 86903,
            "amount_k_cny": 168504.32
        }
    }
}
# 不是 data.items[] !!
# 用 data.stock / data.quote 访问
```

**关键字段:**
- `stock.name` — 股票名称
- `stock.industry` — 所属行业
- `stock.market` — 板块 (主板/创业板/科创板)
- `quote.close` — 收盘价 (当日无交易则返回前收盘价)
- `quote.pct_chg` — 涨跌幅 (%)
- `quote.vol_hand` — 成交量 (手)
- `quote.pre_close` — 前收盘价

---

## get_moneyflow_summary

```python
# 响应结构 (实测 2026-04-13~2026-04-30)
{
    "success": True,
    "data": {
        "ts_code": "603399.SH",
        "start_date": "2026-04-13",
        "end_date": "2026-04-30",
        "days": 21,
        "summary": {
            "net_mf_amount_total_wan": -24503.89,
            "net_mf_amount_avg_wan": -1166.85,
            "main_buy_amount_total_wan": 360689.0,
            "main_sell_amount_total_wan": 330785.03,
            "main_net_amount_total_wan": 29903.97,  # ← 关键字段
            "elg_buy_amount_total_wan": ...,  # 特大单买入总计
            "elg_sell_amount_total_wan": ...
        },
        "latest_day": {
            "trade_date": "2026-04-30",
            "net_mf_amount_wan": -16850.43,    # ← 当日净额
            "buy_lg_amount_wan": 2590.7,        # 大单买入
            "sell_lg_amount_wan": 4535.89,      # 大单卖出
            "buy_elg_amount_wan": 8404.15,      # 特大单买入
            "sell_elg_amount_wan": 1371.65,     # 特大单卖出
            "buy_md_amount_wan": ...,
            "sell_md_amount_wan": ...
        },
        "tl_detail": ...
    }
}
# 不是 data.items[] !!
# 用 data.summary / data.latest_day 访问
```

**评分用字段:**
- `summary.main_net_amount_total_wan` — 区间主力净额 (万)，正值=主力净买入
- `latest_day.net_mf_amount_wan` — 最后交易日净额
- `latest_day.buy_elg_amount_wan` / `sell_elg_amount_wan` — 特大单买卖
- `latest_day.buy_lg_amount_wan` / `sell_lg_amount_wan` — 大单买卖

---

## get_daily_basic_range

```python
# 响应结构 (实测 2026-04-01~2026-04-30)
{
    "success": True,
    "data": {
        "ts_code": "603399.SH",
        "start_date": "2026-04-01",
        "end_date": "2026-04-30",
        "items": [
            {
                "trade_date": "2026-04-30",  # items[0] = 最新
                "close": 19.39,
                "turnover_rate": 3.2152,
                "volume_ratio": 2.35,
                "pe": 205.234,
                "pe_ttm": 97.811,
                "pb": 35.897,
                "total_mv": 1082251.0,
                "circ_mv": 892412.0,
                "vol": 86903000,
                "amount": 1685043200.0
            },
            {   # items[1] = 前一日
                "trade_date": "2026-04-29",
                ...
            },
            ...  # items[-1] = 最旧
        ]
    }
}
# items 是倒序排列! items[0]=最新, items[-1]=最旧
# ✅ closes = [i["close"] for i in items[:20]]  # 最近20日
# ❌ closes = [i["close"] for i in items[-20:]]  # 最旧20日!
```

---

## get_realtime_quotes_latest

```python
# 非交易时段 (实测 09:02 预开市)
{
    "success": False,
    "message": "无实时行情数据",
    "data": {"ts_codes": ["603399.SH", "002791.SZ"]}
}
# isError: true — 正常行为，非bug

# 交易时段 (预计结构，待开盘验证)
# {"success":true,"data":{"items":[{"ts_code":"...","price":...,"bid_price":...,"ask_price":...,"pre_close":...,"open":...,"vol":...}]}}
```

---

## scan_announcement_risk

**当前（2026-05-07 起）：** 服务端已配置推理密钥，正常返回 `data.risk_level` + `data.risk_summary`（与 `signal-trader` / `_shared` 描述一致）。

```python
# 成功时 (结构示例)
{
    "success": True,
    "data": {
        "ts_code": "002103.SZ",
        "risk_level": "none",
        "risk_level_cn": "无",
        "risk_ann_date": None,
        "risk_type": "N/A",
        "risk_summary": "近30个自然日内无相关公告记录",
    },
}
```

**历史故障形态（归档）：** 未配置服务端密钥时曾返回 `success: False` + `message: 未配置 DEEPSEEK_API_KEY`；若再出现，改用 `get_risk_digest`（批量）排雷。

---

## get_prev_trade_day_signals

```python
{
    "success": True,
    "data": {
        "trade_date": "2026-04-30",
        "model_path_like": "%ModelB_%",
        "items": [
            {
                "ts_code": "603399.SH",
                "name": "永杉锂业",
                "confidence": 0.772146,
                "trade_date": "2026-04-30",
                "risk_level": None,  # 未评估
                "model_path": "..."
            },
            ...
        ]
    }
}
# min_confidence 参数控制最低置信度过滤
# 默认 model_path_like=%ModelB_%
# 可用 model_path_like=%ModelA_% 切换模型
```

---

## get_trade_calendar

```python
# 交易日查询 (仅返回 SSE 交易所日历)
{
    "success": True,
    "data": {
        "exchange": "SSE",           # 固定
        "trading_only": True,
        "count": 4,
        "items": [
            {"cal_date": "2026-04-27", "is_open": 1, "pretrade_date": "20260426"},
            {"cal_date": "2026-04-28", "is_open": 1, "pretrade_date": "20260427"},
            {"cal_date": "2026-04-29", "is_open": 1, "pretrade_date": "20260428"},
            {"cal_date": "2026-04-30", "is_open": 1, "pretrade_date": "20260429"}
        ]
    }
}
# 日期参数用 YYYY-MM-DD 格式
# ⚠️ 数据库可能未包含未来月份，当前截止 2026-04-30
```

---

## health_check (Tushare MCP)

```python
{
    "success": True,
    "data": {
        "status": "connected",
        "server_time": "2026-05-06T09:02:08+08:00"
    }
}
```

---

## MCP 工具已知局限（与信号源） {#mcp-known-limitations}

以下与 `signal-trader/SKILL.md` 中业务逻辑一致；**编写采集/筛选代码前**请对照本表，避免误解析或误用时段。

| 工具 | 局限 | 影响 |
|------|------|------|
| `scan_announcement_risk` | 依赖服务端推理配置 | ✅ **2026-05-07 起**服务端已配置，可直接用；备选 `get_risk_digest` |
| `get_prev_trade_day_signals` | `model_path_like` 大小写敏感，新管线路径为小写 | ❌ 可能 **0 条**，须改用 `get_prediction_results` + 手动过滤 |
| `get_features_snapshot` | 部分字段为 `?` 或未入库 | ❌ **勿作为核心判断** |
| `get_realtime_quotes_latest` | 非交易时段 / 09:15 前常无数据 | ⚠️ **仅竞价后可靠**（如 09:25 后） |
| `get_moneyflow_summary` | 依赖已同步交易日 | ✅ 通常最后交易日可用 |
| 全工具 | 调用过快 | ⚠️ 间隔建议 ≥0.3s；风险类 ≥1s |

**信号过滤：** 阈值与排序以 **`probability_up`** 为准（与 `confidence` 勿混用）。详见 `signal-trader` Common Pitfalls 条目。

<!-- version: 1.1 last_updated: 2026-05-12 -->
