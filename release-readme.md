# openclaw-miniqmt-bridge — 发布包说明

**GitHub 首页说明**（产品简介、管理台截图、Release 下载与安装步骤）见仓库根目录 [README.md](README.md)。本文档补充 wheelhouse zip 安装后的部署细节。

本文档面向从 **GitHub Releases** 下载 **`openclaw-miniqmt-bridge-*-wheels.zip`** 并通过 **`install.ps1`** 完成安装的使用者。

---

## 这是什么

**openclaw-miniqmt-bridge** 是面向 **miniQMT / xtquant** 的实盘**执行与运营中间件**：策略层只产出 **`OrderIntent` / `TargetPosition`**，订单状态以**回调事件驱动**；在券商通道之上提供 **OMS、风控、对账与可观测性**。

对外 Release 仅提供 **wheelhouse zip**（需本机 **Python 3.10+**）；`install.ps1` 会在安装根创建 **`.venv`** 并生成 **`Run-*.cmd`** 启动器。**不提供 Nuitka 预编译 zip。**

---

## 运行环境与前置条件

| 项 | 说明 |
|----|------|
| 操作系统 | **Windows 10/11**（x64），与 miniQMT / QMT 典型部署一致 |
| Python | **3.10+**，且 `python` 在 PATH 中（安装脚本用其创建 venv） |
| 交易通道 | 需已正确安装并配置 **easytrader[miniqmt] / xtquant** 所依赖的券商终端与权限；具体以你方券商与终端文档为准 |
| 网络与防火墙 | 若启用 HTTP API / UI / MCP，请自行放行本机或内网访问端口 |
| 合规与资质 | 实盘与对外暴露接口前，请遵守当地监管、券商协议及贵司法务要求；**本软件不提供收益承诺，不替代券商终端** |

---

## 安装根主要产物

`install.ps1` 完成后，安装根（默认 `openclaw-install`）通常包含：

| 路径 / 启动器 | 用途简述 |
|---------------|----------|
| `.venv\Scripts\xtqmt-api.exe` + **`Run-API.cmd`** | **HTTP API**（默认 `http://127.0.0.1:8000`） |
| **`Run-UI.cmd`** + `scripts\run_ui.py` + `ui\` | **管理台**（默认 `http://127.0.0.1:8080`） |
| `.venv\Scripts\xtqmt-mcp.exe` + **`Run-MCP.cmd`** | **MCP 服务**（须在 API 就绪且账户已 connect 后启动） |
| `.venv\Scripts\xtqmt-runtime.exe` + **`Run-Runtime.cmd`** | 完整策略循环（`--mode live --env prod`） |
| **`Run-Runtime-sync.cmd`** | 仅同步本地库（`--sync-db-only`，不要求活动策略） |
| `.env.example` → **`.env`** | 环境变量（安装后须复制并编辑） |
| `configs\`、`scripts\`（部分） | 配置模板与辅助脚本（如策略导入） |

各 `Run-*.cmd` 会 `cd` 到安装根，并设置 **`OPENCLAW_PROJECT_ROOT`** / **`XTQMT_PROJECT_ROOT`**，以便加载同目录 **`.env`**。

---

## 最小部署步骤（建议顺序）

1. **安装**：按 [README.md](README.md) 从 Release 下载 zip、`install.ps1`、`SHA256SUMS` 并执行安装（或使用 `remote_install_bootstrap.ps1` 一行安装）。
2. **配置环境**：复制 **`.env.example`** → **`.env`**，至少设置 `APP_DB_URL`、`API_TOKEN`、`TRADING_ENABLED=false`。
3. **配置策略与账户**（按需）：文件型 SQLite 下，跑完整策略时策略正文以库表 **`strategy_profiles`** 活动行为准（管理台「策略配置」或 `scripts/import_strategy_profiles_from_yaml.py` 导入）；账户档案写入 **`trading_account_profiles`**（管理台「证券账户管理」）。仅 **`Run-Runtime-sync.cmd`** 或 API+UI 路径可不要活动策略行。详见 [`hermes-agent/skills/trade/references/deployment.md`](hermes-agent/skills/trade/references/deployment.md) §3.1。
4. **安全默认**：首次联调保持 **`TRADING_ENABLED=false`**，确认观测无误后再开启实盘下单。
5. **启动顺序**（典型）：先 **MiniQMT** → **`Run-API.cmd`** → **`Run-UI.cmd`** → 管理台 **连接** 账户 → 按需 **`Run-MCP.cmd`** / **`Run-Runtime.cmd`**。端口与认证见 [README.md](README.md) 与 [`ui_runbook.md`](hermes-agent/skills/trade/references/ui_runbook.md)、[`mcp_runbook.md`](hermes-agent/skills/trade/references/mcp_runbook.md)。

---

## 延伸阅读

- [README.md](README.md) — 产品说明与 Release 安装命令
- [docs/install_curl.md](docs/install_curl.md) — 安装参数与安全说明
- [docs/release_packaging_flow.md](docs/release_packaging_flow.md) — 安装后启动路径与排障
- [`runbook.md`](hermes-agent/skills/trade/references/runbook.md) — 运行巡检

---

## 版本与校验

- **版本号**：以 Release 标题或安装收尾打印的 `Installed bridge version:` 为准；应与 `openclaw-miniqmt-bridge-0.1.3-wheels.zip` 内 wheel 版本一致。
- **完整性**：安装前对照 **`SHA256SUMS`** 校验 zip（及可选的 `install.ps1`），防止传输篡改。

---

## 问题反馈与边界

- **缺陷与功能请求**：请在本仓库 **Issues** 中提交，并附上版本、Windows 版本、复现步骤与脱敏日志。
- **刻意不承诺的能力**：见 [docs/marketing_positioning.md](docs/marketing_positioning.md) 与 [README.md](README.md) 中的产品边界说明。

---

感谢使用 **openclaw-miniqmt-bridge**。
