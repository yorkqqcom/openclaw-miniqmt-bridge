#!/usr/bin/env python3
"""
信号交易 Phase A 数据采集+技术评分脚本
======================================
从 Tushare MCP 拉取20只候选信号的技术数据，输出评分排名。

用法:
  1. 修改 signal_codes 列表为当天的候选信号
  2. python3 collect-researcher-data.py

已知的 JSON 结构差异（重要!）:
  - get_stock_snapshot → data.stock + data.quote (不是 items[])
  - get_moneyflow_summary → data.summary + data.latest_day (不是 items[])
  - get_daily_basic_range → data.items[] (其中 items[0]=最新, 倒序排列!)
  - scan_announcement_risk → data.items[] (但需要 DEEPSEEK_API_KEY)
"""

import json
import subprocess
import time
import sys

# ============ 配置 ============
TUSHARE_URL = "http://172.24.144.1:8001/mcp"

# 当日候选信号（从 get_prev_trade_day_signals 获取后填入）
SIGNAL_CODES = [
    "603399.SH", "002791.SZ", "603366.SH", "603918.SH", "603344.SH",
    "603313.SH", "002623.SZ", "601599.SH", "002777.SZ", "001202.SZ",
    "001376.SZ", "600981.SH", "601595.SH", "600860.SH", "002451.SZ",
    "603712.SH", "000536.SZ", "002800.SZ", "001206.SZ", "603992.SH"
]

# 已经持有的仓位代码（需填实际值）
HELD_CODES = []

# 资金配置
BUDGET = 200000  # 总买入预算

# ============ MCP 调用 ============

def mcp_call(method, params=None):
    """调 Tushare MCP 工具，返回解析后的 JSON dict"""
    body = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": method, "arguments": params or {}}
    }
    resp = subprocess.run(
        ["curl", "-s", "--connect-timeout", "15", "--max-time", "20",
         "-X", "POST", TUSHARE_URL,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body)],
        capture_output=True, text=True, timeout=25)
    try:
        data = json.loads(resp.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] JSON parse failed for {method}: {resp.stdout[:200]}")
        return {"data": {}}
    if "result" in data:
        for c in data["result"].get("content", []):
            if c.get("type") == "text":
                return json.loads(c["text"])
    return {"data": {}}


# ============ 数据采集 ============

def collect_data(codes):
    """采集所有信号的技术数据"""
    snaps, basics, moneys, risks = {}, {}, {}, {}

    print(f"采集 {len(codes)} 只股票数据...\n")

    # 1. Snapshot
    print("--- 1/4 个股快照 ---")
    for i, code in enumerate(codes):
        resp = mcp_call("get_stock_snapshot", {"ts_code": code})
        snaps[code] = {
            "stock": resp.get("data", {}).get("stock", {}),
            "quote": resp.get("data", {}).get("quote", {}),
        }
        q = snaps[code]["quote"]
        print(f"  [{i+1:2d}] {code} close={q.get('close','?'):>6} pct={q.get('pct_chg','?'):>6}%")
        time.sleep(0.3)

    # 2. Daily basic
    print("\n--- 2/4 日均基本面(20日) ---")
    for i, code in enumerate(codes):
        resp = mcp_call("get_daily_basic_range",
                         {"ts_code": code, "start_date": "2026-04-01", "end_date": "2026-04-30"})
        basics[code] = resp.get("data", {}).get("items", [])
        print(f"  [{i+1:2d}] {code} -> {len(basics[code])}条")
        time.sleep(0.3)

    # 3. Moneyflow
    print("\n--- 3/4 资金流向(15日) ---")
    for i, code in enumerate(codes):
        resp = mcp_call("get_moneyflow_summary",
                         {"ts_code": code, "start_date": "2026-04-13", "end_date": "2026-04-30"})
        data = resp.get("data", {})
        moneys[code] = {
            "summary": data.get("summary", {}),
            "latest_day": data.get("latest_day", {}),
            "days": data.get("days", 0),
        }
        mn = moneys[code]["summary"].get("main_net_amount_total_wan", 0) or 0
        print(f"  [{i+1:2d}] {code} 主力净额 {mn:>+8.0f}万")
        time.sleep(0.3)

    # 4. Risk (可选)
    print("\n--- 4/4 公告风险(间隔1s) ---")
    for i, code in enumerate(codes):
        resp = mcp_call("scan_announcement_risk", {"ts_code": code})
        items = resp.get("data", {}).get("items", [])
        risks[code] = items[0] if items else {}
        rl = risks[code].get("risk_level", resp.get("message", "N/A"))
        print(f"  [{i+1:2d}] {code} -> risk={rl}")
        time.sleep(1.0)

    return snaps, basics, moneys, risks


# ============ 技术评分 ============

def score_technical(snaps, basics, moneys, codes):
    """给每个信号打技术分，返回排序后的结果"""
    results = []
    for code in codes:
        s = snaps.get(code, {})
        q = s.get("quote", {})
        st = s.get("stock", {})
        items = basics.get(code, [])
        mf = moneys.get(code, {})
        summary = mf.get("summary", {})
        latest = mf.get("latest_day", {})

        name = st.get("name", "?")
        close = q.get("close", 0)
        pct = q.get("pct_chg", 0)
        pre_close = q.get("pre_close", 0)
        vol = q.get("vol_hand", 0)

        # MA calculation (items[0]=latest)
        closes = [i["close"] for i in items[:20] if i.get("close")] if items else []
        vols = [i.get("vol", 0) for i in items[:20]] if items else []

        ma5 = sum(closes[:5]) / 5 if len(closes) >= 5 else 0
        ma20 = sum(closes) / len(closes) if closes else 0
        hi = max(closes) if closes else 0
        lo = min(closes) if closes else 0
        pos_pct = (close - lo) / (hi - lo) * 100 if hi != lo else 50

        # 3-day / 1-day change
        chg_3d = ((closes[0] - closes[2]) / closes[2] * 100) if len(closes) >= 3 else 0
        chg_1d = ((closes[0] - closes[1]) / closes[1] * 100) if len(closes) >= 2 else 0

        # ① Direction score (0-4)
        dir_score = 2.0
        if chg_1d > 0:
            dir_score += 1.0
        elif chg_1d < -2:
            dir_score += 0.5
        if -4 < chg_3d < 4:
            dir_score += 1.0
        elif chg_3d >= 4:
            dir_score -= 0.5
        elif chg_3d <= -8:
            dir_score += 1.0
        dir_score = max(0, min(4, dir_score))

        # ② Money score (0-3)
        main_net = summary.get("main_net_amount_total_wan", 0) or 0
        latest_net = latest.get("net_mf_amount_wan", 0) or 0
        buy_elg = latest.get("buy_elg_amount_wan", 0) or 0
        sell_elg = latest.get("sell_elg_amount_wan", 0) or 0

        money_score = 1.5
        if main_net > 5000:
            money_score += 1.0
        elif main_net > 1000:
            money_score += 0.5
        elif main_net < -5000:
            money_score -= 0.5
        elif main_net < -10000:
            money_score -= 1.0
        if latest_net > 0:
            money_score += 0.5
        elif latest_net < -3000:
            money_score -= 0.5
        if buy_elg > sell_elg and (buy_elg - sell_elg) > 1000:
            money_score += 0.5
        elif sell_elg > buy_elg and (sell_elg - buy_elg) > 1000:
            money_score -= 0.5
        money_score = max(0, min(3, money_score))

        # ③ Position score (0-3)
        pos_score = 1.5
        if pos_pct < 20:
            pos_score += 1.0
        elif pos_pct < 40:
            pos_score += 0.5
        elif pos_pct > 80:
            pos_score -= 0.5
        elif pos_pct > 95:
            pos_score -= 1.0
        if close < ma20 and ma20 > 0:
            pos_score += 0.5
        elif close > ma20 * 1.15 and ma20 > 0:
            pos_score -= 0.5
        # Volume contraction = reversal signal
        if len(vols) >= 5:
            avg5 = sum(vols[:5]) / 5
            avg20 = sum(vols[:20]) / len(vols[:20]) if len(vols) >= 20 else avg5
            vol_ratio = avg5 / avg20 if avg20 > 0 else 1
            if vol_ratio < 0.7:
                pos_score += 0.5
        pos_score = max(0, min(3, pos_score))

        tech_score = dir_score + money_score + pos_score

        results.append({
            "code": code, "name": name, "close": close, "pct": pct,
            "dir_score": dir_score, "money_score": money_score,
            "pos_score": pos_score, "tech_score": tech_score,
            "chg_3d": chg_3d, "chg_1d": chg_1d, "pos_pct": pos_pct,
            "main_net": main_net, "ma5": ma5, "ma20": ma20,
        })

    results.sort(key=lambda r: r["tech_score"], reverse=True)
    return results


# ============ 输出 ============

def print_rankings(results, held_codes):
    """打印技术评分排名"""
    print(f"\n{'='*90}")
    print(f"🏆  技术研究员排名 ({len(results)}只)")
    print(f"{'='*90}")
    print(f"{'排名':>4} {'标的':16s} {'名称':8s} {'收盘':>6} {'涨跌':>7} {'方向':>4} {'资金':>4} {'位置':>4} {'总分':>5} {'建议':>12} {'持仓':>4}")
    print(f"{'-'*90}")

    strong_buy, buy, neutral, avoid = [], [], [], []
    for i, r in enumerate(results, 1):
        ts = r["tech_score"]
        if ts >= 7.5:
            rec = "🟢strong_buy"
            strong_buy.append(r)
        elif ts >= 6.0:
            rec = "🟢buy"
            buy.append(r)
        elif ts >= 5.0:
            rec = "🟡neutral"
            neutral.append(r)
        else:
            rec = "🔴avoid"
            avoid.append(r)

        held = "✅" if r["code"] in held_codes else ""
        print(f"{i:>4} {r['code']:16s} {r['name']:8s} {r['close']:>6.2f} {r['pct']:>+7.3f}% "
              f"{r['dir_score']:>4.1f} {r['money_score']:>4.1f} {r['pos_score']:>4.1f} "
              f"{ts:>5.1f} {rec:>12} {held:>4}")

    print(f"\n{'='*90}")
    print(f"📊 分布: strong_buy={len(strong_buy)}  buy={len(buy)}  neutral={len(neutral)}  avoid={len(avoid)}")
    print(f"{'='*90}")

    # 候选池（去掉已持仓且不是strong_buy的）
    candidates = [r for r in results
                  if r["tech_score"] >= 6.0
                  and (r["code"] not in held_codes or r["tech_score"] >= 7.5)]
    print(f"\n📋 候选买入池 (去重后): {len(candidates)} 只")
    if candidates:
        total_score = sum(c["tech_score"] for c in candidates)
        print(f"{'标的':16s} {'名称':8s} {'价格':>6} {'评分':>4} {'权重':>6} {'分配金额':>10} {'股数':>6}")
        print(f"{'-'*60}")
        for c in candidates:
            weight = c["tech_score"] / total_score
            amount = BUDGET * weight
            shares = int(amount / c["close"] / 100) * 100
            print(f"{c['code']:16s} {c['name']:8s} {c['close']:>6.2f} {c['tech_score']:>4.1f} "
                  f"{weight:>6.1%} ¥{amount:>7,.0f} {shares:>5}股")
        total_shares_cost = sum(
            int(BUDGET * (c["tech_score"] / total_score) / c["close"] / 100) * 100 * c["close"]
            for c in candidates)
        print(f"\n预算: ¥{BUDGET:>10,.2f}")
        print(f"实际: ¥{total_shares_cost:>10,.2f}")


# ============ 主流程 ============

def main():
    print(f"当前时间: {time.strftime('%H:%M:%S')}")
    print(f"候选信号: {len(SIGNAL_CODES)} 只")
    print(f"已持仓位: {len(HELD_CODES)} 只")

    snaps, basics, moneys, risks = collect_data(SIGNAL_CODES)
    results = score_technical(snaps, basics, moneys, SIGNAL_CODES)
    print_rankings(results, HELD_CODES)

    print(f"\n✅ 采集完成 ({time.strftime('%H:%M:%S')})")
    print("下一步: 等待 09:25 集合竞价 → get_realtime_quotes_latest 修正")


if __name__ == "__main__":
    main()
