# 主营业务分析 + 供应链定位参考

## 工具链

| 工具 | 用途 | 关键字段 |
|:---|:---|:---|
| `get_fina_mainbiz_latest` | 主营收入构成（最新报告期） | `bz_item`, `bz_sales`, `bz_profit`, `bz_cost` |
| `list_business_tags_snapshots` | AI业务标签 + 供应链角色 | `tags_json.primary_tags`, `tags_json.supply_role` |
| `get_rpt_fina_segment_quality` | 财务质量指标 | `company_quality`(ROIC/ROA/毛利率), `dol_proxy`(经营杠杆) |
| `get_fina_statement_range` | 三张报表原始数据 | `income`(利润表), `balancesheet`(资产负债表), `cashflow`(现金流) |

## 主营业务收入结构分析

### 基本用法

```python
# 最多同时查15只
r = get_fina_mainbiz_latest(ts_codes=["600597.SH", "301632.SZ"])
items = r["data"]["items"]

# 提取产品级业务
product_items = [i for i in items if i["bz_type"] == "P"]
total_sales = sum(i["bz_sales"] for i in product_items)

for i in product_items:
    pct = i["bz_sales"] / total_sales * 100
    margin = i["bz_profit"] / i["bz_sales"] * 100
    print(f"{i['bz_item']}: 收入占比{pct:.1f}%, 毛利率{margin:.1f}%")
```

### 典型输出示例

```
光明乳业 600597:
├ 液态奶            55.3%  毛利率 ?
├ 其他乳制品         35.4%  毛利率 ?
├ 牧业产品            3.8%  毛利率 ?
└ 其他业务            5.5%  毛利率 ?

广东建科 301632:
├ 房建及市政         73.8%  毛利率 49.5%
├ 安全生产            8.3%  毛利率 28.6%
├ 水利                6.7%  毛利率 33.4%
├ 节能环保            5.7%  毛利率 53.9%
├ 交通                3.4%  毛利率 38.9%
└ 其他                2.1%  毛利率 37.1%
```

## 供应链角色定位

使用 `list_business_tags_snapshots` 获取 AI 生成的供应链标签：

```python
r = list_business_tags_snapshots(ts_code="600597.SH")
tags = json.loads(r["data"]["items"][0]["tags_json"])

# 关键字段
primary_tags = tags["primary_tags"]    # 主营标签，如 ["乳制品","液态奶","乳业"]
secondary_tags = tags["secondary_tags"] # 二级标签
supply_role = tags["supply_role"]       # 供应链角色数组
core_products = tags["core_products"]   # 核心产品
confidence = tags["confidence"]         # 标签置信度 0~1
```

### 供应链角色分类

| 角色 | 含义 | 示例 |
|:---|:---|:---|
| `上游原料` | 原材料/初级加工 | 大全能源(多晶硅)、光明乳业(牧业) |
| `上游技术服务` | 技术服务型供应商 | 中机认检(检测认证) |
| `中游制造` | 产品制造 | 隆基绿能(组件)、广东建科(工程) |
| `中游运营` | 服务运营 | 华贸物流(跨境物流)、西部创业(铁路货运) |
| `中游加工` | 加工环节 | 光明乳业(乳品加工) |
| `下游集成` | 系统集成 | 阳光电源(储能系统)、天合光能(系统方案) |
| `下游渠道` | 渠道分销 | 广博股份(办公直销) |
| `下游其他` | 下游服务/运营 | 正泰电器(电站运营) |
| `终端品牌` | 品牌消费端 | 德尔玛(小家电品牌)、光明乳业(品牌乳企) |

### 光伏行业上下游示例（2026-05-07 实盘数据）

```
上游(硅料)                        中游(硅片/组件)                    下游(逆变器/电站)
┌─────────────┐              ┌──────────────────┐             ┌──────────────────┐
│ 大全能源     │              │ TCL中环(硅片42%) │             │ 阳光电源          │
│ 多晶硅 98.7% │   ──→       │ 毛利率 -19.4%    │             │ 逆变器35%+储能42% │
│ 毛利率 -3.2% │              │                  │             │ 毛利率 35%/37%    │
│              │              │ 隆基绿能(组件85%)│             │ ROIC 25% ⭐      │
│ 通威股份     │              │ 毛利率 0.2%      │             │                  │
│ 多晶硅19%    │              │                  │             │ 正泰电器          │
│ 电池组件47%  │              │ 晶澳/天合/晶科    │             │ 光伏工程34%+运营19%│
│              │              │ 毛利率 -4%~-1%   │             │ 电器设备保底      │
└─────────────┘              └──────────────────┘             └──────────────────┘
```

**关键发现（2026-05-07实盘）：**
- 硅料到组件全线亏损，只有下游逆变器/储能环节盈利
- 阳光电源是唯一ROIC>20%、OCF/OP>1的光伏股
- TCL中环最惨（硅片毛利率-19.4%），靠半导体材料(19%)输血

## 财务质量对比（横向分析）

```python
# 批量对比多家公司
codes = ["300274.SZ","600438.SH","601012.SH","688599.SH"]
for code in codes:
    r = get_rpt_fina_segment_quality(ts_code=code, view="company_quality", end_date="2025-12-31")
    i = r["data"]["items"][0]
    print(f"{code} | 毛利率{i['grossprofit_margin']:.1f}% | "
          f"ROIC={i['roic']:.2f}% | OCF/OP={i['ocf_to_op']:+.2f}")
```

### 指标解读

| 指标 | 正常值 | 预警线 | 含义 |
|:---|:---:|:---:|:---|
| `grossprofit_margin` | >20% | <10% | 定价权/壁垒 |
| `netprofit_margin` | >5% | <0% | 实际盈利 |
| `roic` | >7% | <3% | 资本回报效率 |
| `ocf_to_op` | >0.5 | <0 | 经营现金流覆盖利润的程度 |
| `dol_proxy` | 10~30 | >50 | 经营杠杆（越高对收入波动越敏感） |

**OCF/OP 异常警示：** `ocf_to_op` 若为 **负值且绝对值很大**（如 光明乳业2025年报 OCF/OP = -44.56），说明经营利润远不能转换为现金流，存在财务质量隐患。

## 上下游分析技巧

### 1. 产业链定位
```
使用方法：get_fina_mainbiz_latest + list_business_tags_snapshots
目的：判断一个公司在产业链中的位置
应用：选股时偏好"微笑曲线"两端（上游技术壁垒 / 下游品牌渠道）
```

### 2. 毛利率断面
```
使用方法：get_fina_mainbiz_latest 计算各业务毛利率
目的：同一产业链中，毛利率最高的环节往往有定价权
应用：横向对比同链不同环节的毛利率差异
```

### 3. 财务健康度
```
使用方法：get_rpt_fina_segment_quality(company_quality)
目的：排除虽然毛利率高但现金流差的公司
应用：OCF/OP < 0 且 ROIC < 3% → 谨慎
```

### 4. 行业标签聚类
```
使用方法：list_business_tags_snapshots 的 primary_tags
目的：发现同标签的板块标的
应用：判断当前买入组合是否有板块过度集中风险
```

## Pitfalls

1. **`get_fina_mainbiz_latest` 最多15只** — `ts_codes` 参数不要超过15只
2. **`get_rpt_fina_segment_quality` 部分view无数据** — `segment_line`, `segment_concentration`, `mainbz_vs_income` 当前返回0条，需先跑流水线物化
3. **`list_mainbiz_runs` 返回0条** — 主营业务流水线从未运行过，`list_mainbiz_relations_by_run` 因此也无数据。需要先在服务端触发 `mainbiz_chain`
4. **`bz_profit` 可能是 None** — 部分产品利润数据未披露，需用 `i.get('bz_profit', 0) or 0` 防御
5. **毛利率计算分母为0** — `bz_sales` 可能为0或者None，除前需要检查
