---
name: closing-review
description: "每日15:00后收盘盘点：确认成交→统计盈亏→检查持仓到期→记录决策日志→准备次日卖出清单"
version: 1.1.1
author: Hermes Agent
tags: [trading, a-share, closing, daily-review, positions]
metadata:
  hermes:
    related_skills: [signal-trader, daily-morning-check, switch-account, query-today-orders, query-today-trades]
    requires_soul: profiles/trade/SOUL.md
---

# 收盘盘点 — 每日15:00后执行

## Overview

每日收盘后对当日交易进行全量盘点：成交、浮动盈亏、持仓到期、资产变化与决策日志。

## When to Use

- 用户说「收盘盘点」「盘后复盘」「看看今天成交」「今日盈亏」
- 定时 cron：每天 **15:00~15:30**（晨间 08:00/09:00/09:27 等 **不得与此混淆**；权威时间表见 [`daily-morning-check` 的 `morning_cron_authority`](../daily-morning-check/SKILL.md)，本 skill **不重复粘贴**）
- 卖出日（Day 3）盘后确认卖出结果

## 依赖

- [`signal-trader`](../signal-trader/SKILL.md) — 持仓周期 Day1/Day3、交易与拆单约定、决策日志字段语义  
- [`../_shared/wechat-brief-output.md`](../_shared/wechat-brief-output.md) — 下文微信样式边界  
- [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md) — **成交以 `get_positions` 为准**；session 续期  
- **不依赖**通读 [`daily-morning-check`](../daily-morning-check/SKILL.md)；若需晨间流水线上下文，优先读可选 JSON：[`../_shared/morning-run-context.example.json`](../_shared/morning-run-context.example.json)（实现后由 cron 写入；未实现则无此文件亦可运行本 skill）

### 若需晨间上下文字段（短期清单）

| 字段 | 含义 |
|------|------|
| `run_date` | 业务日 |
| `windows.preflight_09:00.candidate_count` | 早盘候选数量（可选） |
| `windows.auction_09:27.canceled_symbols` | 竞价阶段取消标的（可选） |
| `notes` | 自由文本，供「决策日志」引用 |

长期可将上表迁入 `signal-trader` 的「上下文定义」小节。

## 执行步骤

### Step 0: 获取真实时间

执行 `date`，确认时间 **≥ 15:00**（或用户明确已收盘）。时间相关结论勿凭会话猜测 — 见 [`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)。

### Step 1: 检查QMT通路

初始化 QMT session + `health_check`（StreamableHTTP 见 `signal-trader`）。

### Step 2: 获取交易数据

**`account_id` 约定：** **无仓库级默认账户**；须用 **`list_accounts`** / **`list_trading_accounts`**（或等价列表）并结合**用户指定**得到每个目标 `account_id`，**不得**写死或猜测某一逻辑 ID。对每个已锁定 ID **分别**执行下列四项；**若本节输出拆成多账户多段**，**每段第一行**须 **`当前操作账户 account_id=<该段 id>`**（与 [`signal-trader` 用户可见文案硬性](../signal-trader/SKILL.md#account-id-user-facing) 一致）；单账户仍须在首行写明。详见 [`signal-trader` 的「多账户执行协议」](../signal-trader/SKILL.md#多账户执行协议)。仅切换会话操作账户 → [`switch-account`](../switch-account/SKILL.md)。

- `get_today_orders(<account_id>)` — 当日委托  
- `get_today_trades(<account_id>)` — 成交明细  
- `get_positions(<account_id>)` — **最终持仓（权威）**  
- `get_account_assets(<account_id>)` — 资产快照  

### Step 3: 成交确认

对比委托与持仓，**以 `get_positions` 为准**（`get_today_orders` 的 `status` 不可靠）。

**输出格式（微信版，每行不超过25字）** — 样式约束见 [`../_shared/wechat-brief-output.md`](../_shared/wechat-brief-output.md)：

```
━━ 成交确认 ━━
✅ 广东建科   1400股 @20.97
✅ 中机认检    800股 @29.52
⏳ 华贸物流   4000股 限价低开
━━━━━━━━━━━━
成交 7/8笔 | 87.5%
```

### Step 4: 浮动盈亏统计

盈亏 = (最新价 - 成本价) × 数量；收益率 = 盈亏 / (成本价×数量)。

**输出格式（微信版）：**

```
━━ 持仓盈亏 ━━
广东建科   1400  20.97   -126  -0.4%
中机认检    800  29.53   +211  +0.9%
广博股份   3000   8.05   +835  +3.5% ⭐
━━━━━━━━━━━━━━
合计15只  市值32.8万  浮盈+7,805
```

### Step 5: 持仓到期日历

今日买入=Day1 → Day3 = 今日 + **2 个交易日**（用 `get_trade_calendar`，勿简单日历 +2）。

**输出格式（微信版）：**

```
━━ 到期日历 ━━
广东建科  买入05-07  到期05-11
中机认检  买入05-07  到期05-11
广博股份  买入05-07  到期05-11
━━━━━━━━━━
共7只到期日 05-11(周一)
```

### Step 6: 账户资产变化

**输出格式（微信版）：**

```
━━ 资产变化 ━━
开盘: 现金990万  市值15.4万
收盘: 现金970万  市值32.8万
变动: 现金-19.5万  市值+17.4万
浮盈: +536
```

### Step 7: 决策日志

**输出格式（微信版）：**

```
━━ 收盘日志 2026-05-07 ━━
【成交】
买入 广东建科  1400股 @20.97
买入 通行宝    1800股 @13.21

【统计】
委托8笔 | 成交7笔 | 87.5%
未成交: 华贸物流 限价低于开盘

【研究员】
✅看涨命中 广博+3.5% 中机+0.9%
❌看涨误判 光明-1.2% 德尔玛-0.1%
✅看跌误判 华贸物流风险未现

【明日】
持有观察(Day2) | 关注华贸物流
```

### Step 8: 输出完整报告

汇总 Step 3~7。

## 卖出日特别处理（Day 3）

当天有持仓到期时追加：

- S1: 检查到期持仓是否已清仓  
- S2: 计算卖出盈亏  
- S3: 交易反思（研究员准确度 / 执行纪律）

## 定时配置

`schedule: "0 15 * * 1-5"`（与晨间表分离定义，避免重复维护 — 晨间唯一表见 `daily-morning-check` 的 `morning_cron_authority`）

## Common Pitfalls

1. `get_today_orders` 的 `status` 不可靠 — 必须以 `get_positions` 交叉验证（[`../_shared/qmt-pitfalls.md`](../_shared/qmt-pitfalls.md)）。  
2. 交易日计算用 `get_trade_calendar`，不能简单 `date +2`。  
3. 卖出大仓位须拆单（单笔 ≤ ¥200,000），确认子单全部成交 — 见 `signal-trader` 阶段 E。

## Verification Checklist

- [ ] QMT session 正常连接  
- [ ] 持仓与成交已交叉验证  
- [ ] 浮动盈亏已计算  
- [ ] 持仓到期日历已更新  
- [ ] 账户资产变化已记录  
- [ ] 决策日志已记录  
- [ ] 如有到期持仓，卖出已确认  

<!-- version: 1.1.1 last_updated: 2026-05-13 -->
