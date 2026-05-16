# Multi-Stock Comparison Template

When asked to analyze multiple stocks (行业/上下游/财务对比), use this standardized format.

## Data Collection

For each stock, collect in this order:
1. `get_stock_snapshot` → name, industry, market, close, pct_chg
2. `get_fina_mainbiz_latest(ts_codes=[code])` → business lines with sales + margin
3. `list_business_tags_snapshots` → primary_tags, supply_role, core_products
4. `get_rpt_fina_segment_quality(view='company_quality', end_date='latest年报')` → ROIC/ROA/grossmargin/netmargin/OCF/OP
5. `scan_announcement_risk` → risk_level + risk_summary

## Output Format (WeChat-friendly, ≤25 chars/line)

```
━━ {股票名} {代码} ━━
行业: {industry} | {market}
股价: {close} | 涨幅 {pct}%

主营业务
{业务1}     {占比}%  毛利率{毛利率}%
{业务2}     {占比}%  毛利率{毛利率}%

角色: {supply_role}
标签: {primary_tags}

财务(年报)
收入{rev}亿 | 毛利率{gm}%
净利率{npm}% | ROIC{roic}%
OCF/OP{ocf} | 风险: {risk}
```

For upstream/downstream visualization:
```
上游({上游描述}) → {公司名} → 下游({下游描述})
  {上游企业}      {产品}       {下游客户}
```

## Cross-Company Comparison Table

When comparing 3+ stocks, output a comparison table:

```
━━ 横向对比 ━━
               股票A       股票B       股票C
角色         上游设备🟢  中游制造🔴  下游服务🟡
毛利率       33.3% ✅    3.6% ❌     25.3%
净利率       7.0% ✅     0.9%         -2.3% ❌
ROIC         5.2% ✅     1.5% ❌      -3.1% ❌
OCF/OP       0.95 ✅     -3.15 ❌     -6.59 ❌
━━━━━━━━━━━━━━━━━━━━━━
质量排序: A > C > B
```

## Supply Chain Role Mapping

| Role | Business Quality | Example |
|------|:-:|---------|
| 🟢 上游设备/技术服务 | High margin, strong pricing power | 大族激光(毛利率33%, ROIC5.2%) |
| 🟡 中游制造(高壁垒) | Moderate margin, technology moat | 东方电缆(毛利率22%, ROIC14.8%) |
| 🟡 中游制造(差异化) | Moderate margin, multi-product | 新亚电子(毛利率15%, ROIC8.9%) |
| 🔴 中游制造(同质化) | Thin margin, commodity-like | 铜冠铜箔(毛利率3.6%, OCF/OP-3.15) |
| 🟡 下游服务 | Low-to-mid margin, scale matters | 天娱数科(毛利率25%但净利率-2.3%) |

## Common Findings Pattern

High-quality stocks typically show:
- ROIC > 7% + OCF/OP > 0.8
- Gross margin > 25% + multiple business lines
- Supply role: upstream equipment/service or differentiated manufacturing

Low-quality stocks typically show:
- ROIC < 2% or negative
- OCF/OP < 0 (negative cash flow)
- Single business concentration > 90%
- Gross margin < 5% (commodity trap)
