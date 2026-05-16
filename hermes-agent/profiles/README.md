# `profiles/` 目录说明

本目录存放 **按投研角色划分的 Hermes / Agent 人设**：每个子目录以角色名为单位，核心契约在 **`SOUL.md`**。

与 **自研 A 股交易 Skill** 的关系：交易阶段、MCP、多账户等 **业务真源** 在 [`../skills/trade/signal-trader/SKILL.md`](../skills/trade/signal-trader/SKILL.md) 及 [`../skills/trade/_shared/`](../skills/trade/_shared/)；`profiles` 只约束 **「谁、如何说话、如何汇总」**，不替代 `skills/trade/` 里的工具与阈值说明。

**编写约定**：人设与输出壳集中在各 `SOUL.md`；交易阶段、阈值与 MCP 顺序以 [`../skills/trade/signal-trader/SKILL.md`](../skills/trade/signal-trader/SKILL.md) 为真源，不在 Soul 与 Skill 间重复粘贴。

---

## 1. 本仓库当前内容（与完整部署的差异）

| 现状 | 说明 |
|------|------|
| **六个子目录** | [`admin/`](admin/)、[`ana/`](ana/)、[`sent/`](sent/)、[`tech/`](tech/)、[`risk/`](risk/)、[`trade/`](trade/)，各含 **`SOUL.md`**。 |
| **SENT / RISK** | 与 `admin` 简报中「情绪面」「风控」栏目一一对应；[`admin/SOUL.md`](admin/SOUL.md) 在可 delegate 时优先调用子 agent，否则仍可由 ADMIN 单对话模拟四路。 |
| **本快照未包含** | 常见完整 Hermes 部署中还有 `config.yaml`、`.env`、大型 `skills/` 树（`.bundled_manifest`）、`admin` 下 `logs/` 与网关状态文件等；**出现后即按下面「完整布局」维护**，本节仅说明当前 Git 树中可见范围。 |

---

## 2. 完整布局参考（在完整克隆或本机同步技能包后）

每个 profile 目录典型包含：

| 文件/目录 | 作用 |
|-----------|------|
| **`SOUL.md`** | 身份、流程、输出模板、禁止事项 |
| **`config.yaml`** | Hermes：模型、provider、网关、`toolsets`、`terminal` 等 |
| **`.env`** | 本地密钥与端点；勿将真实密钥提交公共仓库 |
| **`skills/`** | 嵌套 `SKILL.md` 扩展技能；根下常见 **`.bundled_manifest`** |

**`admin/`** 在跑网关时可能额外出现：`logs/`、`gateway_state.json`、`gateway.lock` 等运行痕迹，用于排障。

**`skills/` 第一层分类**（多 profile 同步时常见）：如 `software-development`、`devops`、`github`、`creative`、`mlops`、`trading`、`yuanbao`、`.archive` 等；与 [`../skills/trade/`](../skills/trade/) **不是同一目录**：后者为本项目 **自研** 交易编排包根，前者为 Hermes **挂载的生态技能池**。`profiles/.../skills/trading` 与 `../skills/trade/signal-trader` **无自动等价**，以各自 `SKILL.md` 为准。

---

## 3. 当前六个 profile 与 `SOUL.md` 链接

| Profile | 职责摘要 |
|---------|----------|
| [admin](admin/SOUL.md) | 用户入口；拆解任务；协调或模拟 ANA、SENT、TECH、RISK；输出《综合投资简报》；禁止跳过角色、禁止自造分析。 |
| [ana](ana/SOUL.md) | 基本面分析；数据与定量；禁止编造与模糊表述。 |
| [sent](sent/SOUL.md) | 情绪与资金面观察；简报体例与行为金融边界；禁止用未证实数字与单一传闻定调。 |
| [tech](tech/SOUL.md) | 技术分析；关键价位与周期。 |
| [risk](risk/SOUL.md) | 风控意见；损失边界与集中度；与交易计划及 `signal-trader` 风险口径对齐。 |
| [trade](trade/SOUL.md) | 交易执行；按计划、限价优先、风控与报告体例。 |

---

## 4. 阅读顺序

1. 对话角色与人设 → 对应 **`SOUL.md`**。  
2. A 股信号 / 晨间 / 收盘 / 切户 → **[`../skills/trade/TRUTH_SOURCE.md`](../skills/trade/TRUTH_SOURCE.md)** 与各场景 `SKILL.md`（真源 [`signal-trader/SKILL.md`](../skills/trade/signal-trader/SKILL.md)）。  
3. 本机已存在 `config.yaml` / `skills/` 时 → 再读 Hermes 官方说明与本目录 §2。

<!-- version: 1.2 last_updated: 2026-05-13 — 新增 sent、risk profile -->
