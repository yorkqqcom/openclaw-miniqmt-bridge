# openclaw-miniqmt-bridge（xtqmt 交易中间件发布包）

本仓库是一套面向 **国内券商 miniQMT / xtquant（常见 QMT 交易通道）** 的 **实盘执行与运营中间件**，而不是「内置黑箱策略」或替代券商终端的炒股软件。它把 **策略决策**（你想买卖什么、目标仓位是什么）与 **下单、回报、对账、风控** 分层：策略侧只产出受约束的 `**OrderIntent` / `TargetPosition`**，由中间层完成 **OMS、幂等、事前风控、事件驱动状态机与可观测性**，便于你在单机或小型部署上 **稳定交付、复盘与扩展**。

**适合谁**：个人或小团队量化开发者；需要 **统一装机与账户档案** 的培训 / 集成方；希望在 **Cursor 等支持 MCP 的环境**里，在明确权限边界下做查询、核对与限价类操作的工程师。

**对外提供的主要形态**（可按需组合）：

- **Runtime（`run_live` ）**：常驻跑策略与快照循环；生产环境策略正文以 **SQLite（`APP_DB_URL`）** 中活动配置为准。
- **HTTP API + 零构建管理 UI**：资金、持仓、委托、成交、历史、策略看板与快捷交易等；券商口令经 API **内存连接**，**不入库**。
- **MCP 服务**：把受 Token / `TRADING_ENABLED` / 风控约束的能力暴露给 Agent，与自有或示例技能包联调。
- **Hermes / Cursor Skill 与人设（`hermes-agent/`）**：本仓库附带的 **交易编排、晨间/收盘流程、多账户与输出契约** 等 Markdown 技能资产，与 **xtqmt MCP**（及可选数据 MCP）搭配使用；详见下文 **「五、Hermes Agent 技能包」**。
- **本地 SQLite 持久化**：在轻量通道往往缺少完整「远程历史 API」的前提下，用快照与补数脚本形成 **可查询的跨日账本**。

---

## 架构一览



- **miniQMT**：券商提供的极简 QMT 终端 + `userdata_mini` 数据目录；Python 侧通过 **xtquant** 连接。
- **中间件**：在 xtquant 之上提供 OMS、风控、对账、观测与 **HTTP API**；**MCP 进程**负责把 API 封装成模型可调用的工具。
- **OpenClaw / Cursor（含 Hermes-agent）**：作为 **MCP Client**，通过 `stdio` 或 **HTTP（SSE / streamable-http）** 连接 `xtqmt_mcp`（或上游提供的等价 MCP 地址）。

---

## 示例



## 一、部署与登录 miniQMT（对接中间件前必做）

以下步骤与券商版本有关，以你方 **支持 miniQMT 的 QMT** 官方说明为准；中间件侧只要求：**本机能 import xtquant，且 mini 用户目录路径正确**。

1. **安装 QMT 客户端**
  从券商官网安装完整交易端，确保带 **miniQMT（极简模式）** 或独立 mini 入口。
2. **确认 mini 用户数据目录**
  典型路径类似：`D:/xxxQMT交易端模拟/userdata_mini`（模拟）或实盘对应目录。  
   该目录需存在，且你已在 QMT 内 **登录资金账号**（模拟或实盘按合规选择）。
3. **Python 环境与 xtquant**
  - 打包版中间件已内置运行时则 **无需再装 Python**。  
  - 若从源码/venv 运行：需安装与券商匹配的 **xtquant**（及券商文档要求的 VC 运行库等）。
4. **在中间件中绑定该路径**
  编辑发布目录下的账户配置，例如 `run_mcp.dist/configs/accounts/account_a.yaml`（或 `run_api.dist` 下同名结构），设置：
  - `**miniqmt_path`**：指向上述 `**userdata_mini` 根目录**（与 QMT 里 mini 模式使用的目录一致）。
  - `**stock_account` / `session_id`** 等：按你券商与终端里显示的账号、会话填写（具体字段含义以你方 `xtqmt` 版本文档为准）。
5. **联调安全**
  - 首次只观察：在环境配置里保持 `**dry_run: true`**（如 `configs/env/dev.yaml`）或关闭实盘开关（若存在 `TRADING_ENABLED`，置于 `false`）。  
  - 确认行情、持仓回调、日志与对账无误后，再按合规流程开启真实下单。
6. **防火墙与网络**
  miniQMT 与中间件通常同机；若 API/MCP 对局域网开放，请在系统防火墙中放行对应端口，并避免将管理接口暴露到公网。

---

## 二、配置并启动中间件（连接 miniQMT）

以下以 `**run_mcp.dist` 根目录** 为「安装根目录」说明（`run_api.dist` 同理，二者配置结构一致时需保持账户与环境配置同步）。


| 步骤          | 说明                                                                                                                                             |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. 解压到固定路径  | 路径中尽量避免中文括号、极长路径；`miniqmt_path` 建议与实际目录一致。                                                                                                     |
| 2. 环境变量     | 若发布包带 `.env.example`，复制为 `.env`，按注释填写 **API Token、交易开关、License 公钥路径** 等（以你方构建说明为准）。                                                            |
| 3. 账户与策略    | 编辑 `configs/accounts/*.yaml`、`configs/strategies/*.yaml`。策略里可能出现 `**mcp_url`** 等字段，用于 **策略侧调用外部 MCP 信号**；与下文「AI 客户端连接 xtqmt_mcp」不是同一概念，勿混淆。    |
| 4. 启动顺序（典型） | 先 `**xtqmt_api.exe`**（HTTP 服务），再按需 `**xtqmt_live.exe**`（实盘编排），最后 `**xtqmt_mcp.exe**`（供 AI 通过 MCP 调 API）。若你的包要求先起 `xtqmt_runtime.exe`，以构建方文档为准。 |
| 5. 验证 API   | 对 API 根地址做健康检查或文档中的 probe 接口（端口与路径以实际配置为准）。                                                                                                    |


**License（若启用）**：按构建说明放置 `license.json` 与公钥；若需指定公钥文件路径，可使用环境变量 `**LICENSE_PUBLIC_KEY_PATH`** 指向 `.pem`。

---

## 三、在 OpenClaw 中通过 MCP 连接中间件

OpenClaw 在配置里维护 MCP 服务注册表，官方说明见：[Configuration reference — MCP](https://docs.openclaw.ai/gateway/configuration-reference) 与 [CLI — MCP](https://docs.openclaw.ai/cli/mcp#openclaw-as-an-mcp-client-registry)。

### 3.1 编辑 `~/.openclaw/openclaw.json`（Windows 多为 `C:\Users\<用户>\.openclaw\openclaw.json`）

在 `**mcp.servers**` 下增加一项，二选一（以你实际暴露的传输为准）。

**方式 A：本机 stdio（MCP 可执行文件）**

```json5
{
  mcp: {
    servers: {
      "xtqmt-miniqmt": {
        command: "D:\\\\PycharmProjects\\\\openclaw-miniqmt-bridge\\\\run_mcp.dist\\\\xtqmt_mcp.exe",
        args: [],
        env: {
          // 与 .env / 构建约定一致，示例名仅供参考
          // XTQMT_API_TOKEN: "your-token",
        },
      },
    },
  },
}
```

**方式 B：远程 HTTP（`streamable-http` 或 `sse`）**

若中间件或反向代理以 URL 提供 MCP（例如 `https://your-host/mcp`）：

```json5
{
  mcp: {
    servers: {
      "xtqmt-miniqmt-remote": {
        url: "https://your-host/mcp",
        transport: "streamable-http", // 或 "sse"，与服务器一致
        headers: {
          Authorization: "Bearer ${MCP_REMOTE_TOKEN}",
        },
      },
    },
  },
}
```

### 3.2 工具权限（profile）

若使用受限 `**tools.profile**`（如 `messaging` / `minimal`），需在配置中允许 **bundle MCP** 工具，否则模型看不到已注册的 MCP 工具。详见官方 [Tools](https://docs.openclaw.ai/tools) 中关于 `**bundle-mcp`** 与 `**tools.alsoAllow**` 的说明。

### 3.3 可选：mcporter + Skill

社区亦有通过 **mcporter**（`~/.mcporter/mcporter.json`）注册远程 MCP，再在 OpenClaw **workspace skills** 里用 `SKILL.md` 描述调用方式的集成路径；若你采用该模式，保持 **URL / Header** 与中间件鉴权一致即可。

修改 `mcp.`* 后，OpenClaw 会丢弃已缓存的 MCP 会话；下一次工具发现会按新配置重建。

---

## 四、在 Cursor（含 Hermes-agent）中通过 MCP 连接中间件

**Hermes-agent** 指 Cursor 中已配置的 **MCP 服务器之一**（常见服务器名为 `hermes-agent`）。它与 **本中间件的 MCP（`xtqmt_mcp`）** 是并列关系：要在对话里调用交易能力，需在 **同一套 MCP 配置** 里单独增加一条指向 `xtqmt_mcp`（或其中间件提供的 HTTP MCP）的条目，**不能**用 Hermes-agent 替代 xtqmt 进程。

### 4.1 用户级 `mcp.json`（Cursor / Hermes-agent 共用）

在用户级 MCP 配置中增加服务器定义（路径以 Cursor 当前版本为准，常见为 **用户目录下** `.cursor/mcp.json`）。若你已启用 **Hermes-agent**，文件中应已有对应服务器条目（键名常见为 `hermes-agent`，以你安装为准）；**保留该项不动**，在同一 `mcpServers` 对象内**追加**本中间件条目即可。

**仅追加 xtqmt 中间件（stdio）示例：**

```json
{
  "mcpServers": {
    "xtqmt-miniqmt": {
      "command": "D:\\PycharmProjects\\openclaw-miniqmt-bridge\\run_mcp.dist\\xtqmt_mcp.exe",
      "args": [],
      "env": {}
    }
  }
}
```

将上述 `xtqmt-miniqmt` 块**合并进**你现有的 `mcpServers`（与 Hermes-agent 的配置并列，同一层级）。

**若 Cursor 支持基于 URL 的 MCP**：按客户端文档填写 `url` 与 `headers`（例如 `Authorization: Bearer <token>`），与中间件实际暴露的传输类型一致即可。

保存后 **重启 Cursor** 或按界面提示重新加载 MCP，在 MCP 面板中确认 **xtqmt** 对应工具列表已出现；Hermes-agent 与 xtqmt 应可同时在线。

---

## 五、Hermes Agent 技能包（本仓库 `hermes-agent/`）

本仓库在 `hermes-agent/` 下附带 **Hermes / Cursor 可用的 Skill 与人设资产**，用于在已挂载 **xtqmt MCP**（及可选 Tushare 等数据 MCP）的前提下，约束 Agent 的 **编排顺序、输出体例、多账户口径与交易风险话术**。Skill 文档描述 **「何时读哪份规范、对用户怎么说」**；具体下单/查询仍由 **中间件 MCP 工具** 执行，二者需同时配置。

### 5.1 文档入口（建议按此顺序阅读）


| 文档                                                                                       | 作用                                                                 |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `[hermes-agent/profiles/README.md](hermes-agent/profiles/README.md)`                     | 角色 `SOUL.md` 与人设目录说明。                                            |
| `[hermes-agent/skills/trade/TRUTH_SOURCE.md](hermes-agent/skills/trade/TRUTH_SOURCE.md)` | 策略与阈值类条目的逻辑真源索引（细则仍以 `signal-trader` 正文为准）。                        |
| `[hermes-agent/skills/trade/signal-trader/SKILL.md](hermes-agent/skills/trade/signal-trader/SKILL.md)` | A 股信号交易全流程、阶段、多账户与 MCP 工具顺序的 **唯一真源**。 |


### 5.2 目录与能力概要

- `**hermes-agent/profiles/`**：按角色划分的 `**SOUL.md**`（如 `admin`、`ana`、`sent`、`tech`、`risk`、`trade`）及可选 Hermes 运行参数；定义身份、流程与输出契约，**不替代**交易阶段规则正文。详见 `[hermes-agent/profiles/README.md](hermes-agent/profiles/README.md)`。
- `**hermes-agent/skills/trade/`**：自研 **A 股信号交易 + 晨间编排 + 收盘盘点 + 多账户切换 + 证券解析与原子写单/查询 + 只读投研编排** 等 Skill；**业务规则真源**在 `[signal-trader/SKILL.md](hermes-agent/skills/trade/signal-trader/SKILL.md)`，晨间/收盘等编排层仅作薄引用，避免与真源双份维护。
- `**hermes-agent/skills/trade/_shared/`**：无 YAML 头的共享附录（Cron JSON-RPC、微信简报体、QMT 坑点、订单风险契约等），供多个 skill 引用。

### 5.3 技能树速查（意图 → 主读 skill）

| 用户意图 / 场景                     | 主读 skill                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 信号交易、研究员流程、阶段 A–D、MCP 工具顺序与阈值 | `signal-trader`                                                                                                                                         |
| 切换/锁定当前操作账户 `account_id`      | `switch-account`                                                                                                                                        |
| 中文名/简称 → 规范代码                 | `stock-symbol-resolve`                                                                                                                                  |
| 单笔/批量限价买、卖、撤单；当日委托/成交查询       | `buy-single` / `buy-batch`、`sell-single` / `sell-batch`、`cancel-order` / `cancel-orders-batch`、`query-today-orders`、`query-today-trades`                |
| 早盘 Cron 编排                    | `daily-morning-check`                                                                                                                                   |
| 收盘盈亏与成交核对                     | `closing-review`                                                                                                                                        |
| 深度基本面只读包、信号排障、行业资金流、ETF 份额战术等 | `equity-research-pack`、`prediction-signal-debug`、`sector-moneyflow-brief`、`etf-fund-flow-tactical` 等（路径均位于 `hermes-agent/skills/trade/<name>/SKILL.md`） |


### 5.4 与 xtqmt 联调时的建议顺序（Skill 包与中间件一致）

1. 启动 **HTTP API**（如 `python scripts/run_api.py` 或发布包中的 `xtqmt_api`）。
2. 对参与编排的每个逻辑账户 **connect 成功**（含口令；未连接则查询可能为空、写单失败）。
3. 启动 **MCP**（如 `python scripts/run_mcp.py` 或 `xtqmt_mcp`），环境变量 `**MCP_API_BASE_URL`**、`**MCP_API_TOKEN**`（或 `**API_TOKEN**`）与 API 侧一致。
4. 执行交易类 skill 时先 `**list_trading_accounts` / `list_accounts` / `health_check**`；多账户与用户可见 `**account_id**` 文案以 `signal-trader`、`switch-account` 正文为准。

包内可选自检脚本（自仓库根运行）：`python hermes-agent/skills/trade/scripts/check_skill_pack_links.py`、`check_stage_id_refs.py`、`check_skill_drift.py`（可加 `--strict`）；链接巡检亦可运行 `hermes-agent/skills/trade/signal-trader/scripts/scan_skill_links.py`。

---

## 六、合规与问题反馈

- 实盘与对外网暴露 API/MCP 前，请遵守监管、券商协议与内部风控；本说明不提供投资建议。  
- **缺陷反馈**请携带：Windows 版本、中间件版本、miniQMT 券商类型、`miniqmt_path` 是否本机可访问（日志中勿粘贴明文密码与 Token）。

---

## 参考链接

- [OpenClaw 文档首页](https://docs.openclaw.ai)  
- [OpenClaw — Tools（含 bundle-mcp 与 profile）](https://docs.openclaw.ai/tools)  
- [OpenClaw — Gateway configuration reference（MCP 段）](https://docs.openclaw.ai/gateway/configuration-reference)  
- [OpenClaw — CLI MCP](https://docs.openclaw.ai/cli/mcp#openclaw-as-an-mcp-client-registry)

