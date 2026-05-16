---
name: equity-research-pack
description: "Use when user asks for deep A-share fundamental research, financial quality, main business, segment reports, or announcement risk without placing orders. Read-only MCP chain with mandatory data quality declaration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, fundamental, a-share, read-only, ana]
    related_skills: [signal-trader]
    requires_soul: profiles/ana/SOUL.md
---

# equity-research-pack — 只读基本面深度包（标杆）

## Overview

本 Skill 为 **只读投研编排**：按固定顺序调用 **Tushare Hermes 数据 MCP**，产出符合 ANA 壳的分析，**不包含**下单、撤单、限价 Y/N 或 `account_id` 交易话术。

**交易与信号阈值真源**：[`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 阶段 A；若用户后续要求执行买入，**MUST** 切换加载 `signal-trader`，不得在本文内自行定义阶段或阈值。

## When to Use

- 用户要求：深度基本面、财报质量、主营构成、分部/质量物化报表、公告排雷、同业对比（小集合）等 **纯研究** 任务。
- 与 `signal-trader` 阶段 A「基本面研究员」重叠时：可 **单独** 用本包做加长报告；执行交易仍以 `signal-trader` 为准。

## When NOT to Use

- 任何需要 **QMT 下单、持仓查询、资金分配、Y/N 确认** 的场景 → 使用 `signal-trader` 与相关交易 Skill。
- 无有效 `ts_code`（未解析证券代码）→ 先 [`../stock-symbol-resolve/SKILL.md`](../stock-symbol-resolve/SKILL.md)。

## Prerequisites

- Tushare 数据 MCP 已配置且可 `tools/call`（见 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 前置）。
- 可选：已运行 [`../scripts/preflight_data_readiness.py`](../scripts/preflight_data_readiness.py)，存在 `hermes-agent/.cache/data_readiness.json` 时 **SHOULD** 先读缓存并在声明节引用。

## 推荐工具链（顺序）

对每只标的 `ts_code`（最多 **5** 只并行深度，避免超限）：

1. **排雷（先）**  
   - `scan_announcement_risk(ts_code)` 或批量 `get_risk_digest(ts_codes=[...])`  
   - 可选元数据：`list_cninfo_announcements_range(ts_code, start_date, end_date)`（控制 `limit`）

2. **三张表与指标**  
   - `get_fina_statement_range(statement=income|balancesheet|cashflow|indicator, ts_code, start_date, end_date, limit≤120)`  
   - 报告期与 `limit` 须与用户需求对齐；**禁止**编造缺失报告期。

3. **主营构成**  
   - `get_fina_mainbiz_latest(ts_codes=[ts_code])`（单次最多 15 码；多标拆批）

4. **物化质量视图（非实时）**  
   - `get_rpt_fina_segment_quality(ts_code, view=company_quality|dol_proxy|segment_line|...)`  
   - 若 preflight 或返回提示无物化数据 → 声明 **partial**，不得当实时行情使用。

5. **标签与供应链叙事（可选）**  
   - `list_business_tags_snapshots(ts_code)`

6. **多标的横向格式**  
   - 输出结构见 [`../signal-trader/references/multi-stock-comparison.md`](../signal-trader/references/multi-stock-comparison.md)。

## 输出骨架（复制用）

```markdown
<基本面分析报告 [ts_code]>

【核心结论】…（仅基于已取到的数据；无数据则写「数据不足无法结论」）

【估值与规模】…（来自 `daily_basic` / `get_stock_snapshot` 若已调用）

【成长与主营】…

【财务与质量】…（`company_quality` / `dol_proxy` 等）

【风险与公告】…

## 数据质量声明
- 数据源: Tushare Hermes MCP（列出本次实际调用的工具名）
- 可用性: full | partial | unavailable
- 缺失维度: …
- 数据时点:
  - preflight: <ISO8601 或「未运行」>（status: …）
  - 本次调用: <ISO8601>（例如 `get_rpt_fina_segment_quality` → 空 / 错误摘要）
- 降级说明: …
```

## Pitfalls

- **`get_fina_mainbiz_latest` 上限 15 码**；超出须分批。
- **`get_rpt_fina_segment_quality` 非实时**；与 preflight 不一致时以 **本次调用** 为准并写在「数据时点」。
- **特征 `get_features_snapshot`**：若使用，**MUST** 仅展示 [`../signal-trader/references/feature_fields_whitelist.yml`](../signal-trader/references/feature_fields_whitelist.yml) 中列出的字段（其余忽略并在声明中说明）。

## Verification Checklist

- [ ] 输出含 **数据质量声明** 全节（含数据时点）。
- [ ] 未出现下单/撤单/Y·N/「确认执行」类话术。
- [ ] 无数据维度未编造数字。
- [ ] 相对链接在本包内可解析（或已跑 `check_skill_pack_links.py`）。

<!-- version: 1.0 last_updated: 2026-05-16 — 标杆只读投研 Skill -->
