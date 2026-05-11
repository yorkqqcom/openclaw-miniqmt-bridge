\# openclaw-miniqmt-bridge 全流程部署



本文自成一体，说明在 \*\*Windows\*\* 上安装 \*\*openclaw-miniqmt-bridge\*\*（Wheel + 脚本）、启动依赖服务、安装 \*\*miniQMT\*\*、可选 \*\*WSL2 / Ubuntu\*\*，以及 \*\*Nous Hermes Agent\*\* 通过 MCP 调用本桥。第三方产品步骤以对应官网为准，文中仅给出可直接操作的要点。



\---



\## 一、openclaw-miniqmt-bridge 安装与需启动的服务



\### 1.1 安装方式：Wheel + 安装脚本



\*\*前提\*\*：目标机已安装 \*\*Python 3.10+\*\*，且 `python` 在 PATH 中；网络能访问托管 `\*\*install.ps1`\*\* 与 \*\*wheel zip\*\* 的 HTTPS 地址（下例为 GitHub Releases）。



\*\*推荐命令（先下载脚本再本地执行，便于核对脚本内容）\*\*。在 \*\*PowerShell\*\* 中于目标目录依次执行：



```powershell

Invoke-WebRequest -Uri "https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/download/openclaw-miniqmt-bridge/install.ps1" -OutFile ".\\install.ps1" -UseBasicParsing

```
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\\install.ps1" -DownloadBaseUrl "https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/download/openclaw-miniqmt-bridge/" -BundleFileName "openclaw-miniqmt-bridge-0.1.0-wheels.zip" -ExpectedSha256 "d5ced3cfb0e8b3fd9f5310d70f84cf0ab4758223fd0ca0a191529046425ab8a7"

```



\*\*可选安装根\*\*：在执行上一段之前可设置：



```powershell

$env:OPENCLAW\_INSTALL\_ROOT='c:\\path\\to\\openclaw-install'

```



不设时常见默认目录名为 `\*\*openclaw-install\*\*`（相对当前工作目录或脚本约定目录，以实际 `install.ps1` 行为为准）。



\*\*安装完成后\*\*：



\- 安装根下应有虚拟环境（常见为 `\*\*.venv`\*\*）及 `\*\*Run-\*.cmd`\*\*；环境变量 `\*\*OPENCLAW\_PROJECT\_ROOT\*\*`。

\- 安装根下的 `\*\*.env\*\*`，按下文「环境变量提要」填写。

\- 可执行入口位于 venv 的 `\*\*Scripts\*\*` 目录：`\*\*xtqmt-api.exe\*\*`、`\*\*xtqmt-runtime.exe\*\*`、`\*\*xtqmt-live.exe\*\*`、`\*\*xtqmt-mcp.exe\*\*`（名称以安装结果为准）；也可双击安装根下 `\*\*Run-\*.cmd\*\*` 中对应项。



\*\*备选（一行远程 bootstrap）\*\*：等价于下载远程 PowerShell 并执行，信任边界更大；若使用，须信任 HTTPS、托管方与该 ref 上的脚本，且 zip 仍应由安装逻辑做 SHA-256 校验。具体一行命令随你方 Release 上发布的 bootstrap 文件名与 URL 而定，此处不展开。



\### 1.2 必须先启动的外部服务



\- \*\*MiniQMT 客户端\*\*：使用 xtquant / easytrader 与柜台交互前，须先启动券商侧 \*\*MiniQMT\*\*（例如安装目录下的 `\*\*XtMiniQmt.exe`\*\*，或在 QMT 中以极简模式登录）。详见本文第二节。



\### 1.3 本仓库建议启动的进程（矩阵）



典型拓扑：\*\*最小联调\*\*可只开 \*\*API\*\* 与（按需）\*\*Live\*\*；生产再叠加 \*\*UI\*\*、\*\*MCP\*\*、反向代理与监控。





| 组件                        | 启动（venv / `Run-\*.cmd`）          | 默认监听 / 说明                                                                                 |

| ------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |

| HTTP API                  | `xtqmt-api`                     | 默认 `http://127.0.0.1:8000`；健康检查 `\*\*GET /health`\*\*；指标 `\*\*GET /metrics`\*\*（通常需 `API\_TOKEN`）。 |

| 实盘编排（策略 + 对账等）            | `xtqmt-live`                    | 内部以 `\*\*live\*\*` 模式跑运行时；常见内置间隔示例为策略约 \*\*5s\*\*、对账约 \*\*20s\*\*、健康约 \*\*10s\*\*（以实际版本为准）。               |

| 通用运行时（非「一键 live」）         | `xtqmt-runtime`                 | 通过子命令/参数选择模式与间隔，以 `\*\*--help`\*\* 与当前版本说明为准。                                                 |

| 管理 UI（可选）                 | 安装包提供的 `Run-\*.cmd` 或同目录说明       | 默认 `\*\*http://127.0.0.1:8080`\*\*。                                                           |

| MCP（可选，供 Hermes / Cursor） | `xtqmt-mcp`                     | \*\*必须在 API 已监听之后\*\*再启动；环境变量见本文第五节与下表摘要。                                                     |

| 反向代理 + Prometheus（生产可选）   | 自建 Nginx / Caddy 等 + Prometheus | 见下文「生产与监控摘要」。                                                                             |





\*\*建议启动顺序\*\*：先 \*\*API\*\*，再按需 \*\*Runtime / Live\*\*、\*\*UI\*\*、\*\*MCP\*\*。



\*\*生产与监控摘要\*\*：



\- \*\*反向代理\*\*：对外建议 \*\*HTTPS\*\*，将 `/` 转发到 UI（如 `127.0.0.1:8080`），将 `\*\*/api/`\*\* 转发到 API（如 `127.0.0.1:8000/api/`），并转发 `\*\*/health`\*\*、`\*\*/metrics`\*\* 至 API；配置 `Host`、`X-Forwarded-For`、`X-Forwarded-Proto`。若 UI 与 API 不同域，需为 API 配置明确的跨域来源（如 `API\_ALLOW\_ORIGIN`），勿长期用 `\*` 上生产。

\- `\*\*/metrics\*\*`：建议仅内网或加白名单/二次鉴权，勿裸奔公网。

\- \*\*Prometheus\*\*：在抓取配置中加入 API 的 `\*\*/metrics`\*\* 目标；将你方提供的告警规则 YAML（若随发行附带则按其路径）加入 Prometheus `\*\*rule\_files`\*\*；重载后在 Targets / Alerts 中确认状态。关注拒单类指标（如 `order\_reject\_total`、`order\_reject\_reason\_total`）并接入飞书/钉钉等通知。



\### 1.4 环境变量提要



下列变量写入安装根 `\*\*.env`\*\*（或按进程环境注入）。`\*\*OPENCLAW\_\*`\*\* 与 `\*\*XTQMT\_\*\*\*` 成对出现时，`\*\*OPENCLAW\_\*\*\*` 优先。





| 类别       | 变量                                                             | 说明                                                             |

| -------- | -------------------------------------------------------------- | -------------------------------------------------------------- |

| 安装根 / 配置 | `OPENCLAW\_PROJECT\_ROOT`                                        | 指向安装根，便于解析 `.env` 与相对路径。                                       |

| 配置根      | `OPENCLAW\_CONFIG\_ROOT`                                         | YAML 配置根；多副本部署时可显式指定。                                          |

| 点 env 路径 | `OPENCLAW\_DOTENV\_PATH`                                         | 显式指定 `.env` 文件路径时使用。                                           |

| 逻辑账户     | `OPENCLAW\_LOGICAL\_ACCOUNT\_ID`、`XTQMT\_LOGICAL\_ACCOUNT\_ID`       | 覆盖默认逻辑账户 ID。                                                   |

| 持久化      | `APP\_DB\_URL`                                                   | 使用 `\*\*sqlite:///...\*\*` 指向\*\*文件\*\*库方可跨进程、跨日累积委托/成交/快照等；纯内存库不保留历史。 |

| API 安全   | `API\_TOKEN`、`API\_PROTECT\_HEALTH`、`API\_ALLOW\_ORIGIN`            | 强随机 Token；是否保护 `/health`；CORS 来源。                              |

| UI       | `UI\_AUTH\_USERNAME`、`UI\_AUTH\_PASSWORD`、`UI\_SESSION\_TTL\_SECONDS` | 管理台登录（与券商密码无关）。                                                |

| 交易开关     | `TRADING\_ENABLED`                                              | 联调建议 `\*\*false`\*\*，确认观测与对账后再改为 `\*\*true`\*\*。                       |





\*\*与历史数据相关的现实约束（轻量通道）\*\*：MiniQMT / 券商实时源上，跨日 `\*\*query\_history\_`\*\*\* 类接口常为空或不可用；跨日分析多依赖 \*\*运行时在线\*\* 时周期性快照写入 SQLite，以及后续补数脚本（若你方流程包含）。查询侧可使用 `\*\*history\_scope=local`\*\*（或 UI 等价选项）读取已落库数据。



\### 1.5 组件关系（示意）



```mermaid

flowchart LR

&#x20; subgraph win \[Windows主机]

&#x20;   MiniQMT\[MiniQMT客户端]

&#x20;   API\[xtqmt-api]

&#x20;   Runtime\[xtqmt-live或runtime]

&#x20;   MCP\[xtqmt-mcp]

&#x20;   MiniQMT --> Runtime

&#x20;   API --> Runtime

&#x20;   MCP --> API

&#x20; end

&#x20; subgraph optional \[可选]

&#x20;   Hermes\[HermesAgent]

&#x20;   Hermes --> MCP

&#x20; end

```







\---



\## 二、miniQMT 下载地址与安装



\*\*说明\*\*：miniQMT 常随 \*\*券商 QMT\*\*、\*\*邮件分发\*\* 或 \*\*投研/极简通道\*\* 提供，\*\*没有\*\*适用于所有人的单一固定 exe 直链；以下为官方面向文档与下载聚合入口，实际安装包请以 \*\*开户券商\*\* 与 \*\*迅投当前说明\*\* 为准。





| 资源                 | URL                                                                                                                          |

| ------------------ | ---------------------------------------------------------------------------------------------------------------------------- |

| QMT 极简版（mini）知识库   | \[http://docs.thinktrader.net/QMT-mini/](http://docs.thinktrader.net/QMT-mini/)                                               |

| xtquant 等下载（迅投知识库） | \[https://dict.thinktrader.net/nativeApi/download\_xtquant.html](https://dict.thinktrader.net/nativeApi/download\_xtquant.html) |

| 迅投官网               | \[https://www.thinktrader.net/](https://www.thinktrader.net/)                                                                 |





\*\*安装与启动要点\*\*：



1\. 按券商或迅投指引完成 QMT / miniQMT 安装与资金账号权限开通。

2\. 启动 \*\*极简模式\*\* MiniQMT，或直接运行安装目录中的 `\*\*XtMiniQmt.exe`\*\*（路径因安装而异）。

3\. 在本桥 `.env` 或账户连接参数中配置 `\*\*XTMINI\_PATH`\*\*（通常指向含 `userdata\_mini` 的客户端路径）、`\*\*XTMINI\_ACCOUNT`\*\*、`\*\*XTMINI\_SESSION\_ID\*\*`；多会话勿重复使用同一 `session\_id`。



\---



\## 三、`wsl --install` 安装 WSL



在 \*\*Windows 10/11\*\* 上启用适用于 Linux 的 Windows 子系统，常用方式为管理员 PowerShell 执行：



```powershell

wsl --install

```



\- 可能需先开启 \*\*虚拟机平台\*\* 等 Windows 可选功能；若命令报错，按系统提示在「启用或关闭 Windows 功能」中勾选相关项并重启。

\- 官方步骤与故障排除：\*\*\[在 Windows 上安装 WSL](https://learn.microsoft.com/zh-cn/windows/wsl/install)\*\*（微软文档，标题与路径以官网为准）。



\---



\## 四、WSL2 与 Ubuntu 安装及升级



\### 4.1 使用 WSL2 作为默认版本



安装完成后建议将默认版本设为 \*\*2\*\*（性能与兼容性通常优于 WSL1）：



```powershell

wsl --set-default-version 2

wsl -l -v

```



在列表中确认目标发行版的 \*\*VERSION\*\* 为 \*\*2\*\*。



\### 4.2 安装 Ubuntu



\- \*\*方式 A\*\*：`wsl --install` 默认可能带 Ubuntu；或执行 `wsl --install -d Ubuntu`。

\- \*\*方式 B\*\*：从 \*\*Microsoft Store\*\* 搜索「Ubuntu」安装。



\### 4.3 升级（两个层次）





| 层次                  | 作用                | 常见命令 / 操作                                        |

| ------------------- | ----------------- | ------------------------------------------------ |

| Windows 侧 WSL 内核与组件 | 更新 WSL 本身         | 管理员 PowerShell：`wsl --update`                    |

| Linux 发行版内软件包       | 更新 Ubuntu 内 apt 包 | 在 Ubuntu 内：`sudo apt update \&\& sudo apt upgrade` |





\### 4.4 与 openclaw-miniqmt-bridge 的边界



\- \*\*交易桥与 miniQMT 应在 Windows 本机运行\*\*，与券商终端、QMT 典型部署一致。

\- \*\*WSL2 / Ubuntu\*\* 适合运行 \*\*Hermes Agent\*\*、开发工具链等；\*\*不要\*\*指望在 WSL 内直接替代 Windows 上的 miniQMT 客户端（除非你有单独验证过的架构，不在本文范围）。



\---



\## 五、Hermes Agent（Nous Research）安装与对接本桥 MCP



\### 5.1 Hermes Agent 安装



Hermes Agent 由 \*\*Nous Research\*\* 维护，安装命令与依赖随版本变化，\*\*请以官方文档为准\*\*：



\- 入门安装：\[https://hermes-agent.nousresearch.com/docs/getting-started/installation](https://hermes-agent.nousresearch.com/docs/getting-started/installation)  

\- MCP 总览：\[https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)  

\- 使用 MCP 指南：\[https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes](https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes)



若安装时未包含 MCP 相关依赖，按官方说明为 Hermes 环境追加 `\*\*\[mcp]`\*\* 或等价 extra 后再配置下文 MCP 服务器。



\### 5.2 MCP 进程环境变量（本桥 `xtqmt-mcp`）





| 变量                                                  | 说明                                                                                     |

| --------------------------------------------------- | -------------------------------------------------------------------------------------- |

| `MCP\_API\_BASE\_URL`                                  | 交易 HTTP API 根地址，默认 `http://127.0.0.1:8000`。                                            |

| `MCP\_API\_TOKEN`                                     | 优先使用；未设时回退 `\*\*API\_TOKEN`\*\*；与 API 的 `\*\*Authorization: Bearer`\*\* 或 `\*\*X-API-Token\*\*` 一致。 |

| `MCP\_TRANSPORT`                                     | `stdio`（默认） / `streamable-http` / `sse`；命令行 `--transport http` 等价于 `streamable-http`。  |

| `MCP\_HTTP\_HOST` / `MCP\_HTTP\_PORT` / `MCP\_HTTP\_PATH` | HTTP/SSE 监听与路径，常见默认主机 `127.0.0.1`、端口 `\*\*8765\*\*`、路径 `\*\*/mcp\*\*`。                         |

| `MCP\_HTTP\_JSON\_RESPONSE`                            | 设为 `true` 时强制非流式 JSON（兼容不支持流的客户端）。                                                     |

| `MCP\_PING\_ON\_START`                                 | 设为 `true` 时启动前请求 `\*\*GET /health\*\*`，失败则退出。                                              |





网卡许可等若与 API/Runtime 共用同一套门禁，请与当前版本行为保持一致；仅在明确关闭门禁的环境变量取值下 MCP 才可能跳过校验。



\### 5.3 对接本桥的操作顺序



1\. \*\*先启动 HTTP API\*\*（`xtqmt-api` 或对应 `Run-\*.cmd`），确认 `\*\*GET /health`\*\* 返回正常。

2\. \*\*再启动 MCP\*\*（`xtqmt-mcp`）。  

\*\*streamable-http\*\* 示例（供支持该传输的客户端连接；公网须 HTTPS 反代、限流与白名单）：



```powershell

$env:MCP\_API\_BASE\_URL='http://127.0.0.1:8000'

$env:MCP\_API\_TOKEN='与API侧API\_TOKEN一致'

\& 'D:\\你的安装根\\openclaw-install\\.venv\\Scripts\\xtqmt-mcp.exe' --transport streamable-http --host 127.0.0.1 --port 8765 --path /mcp

```



1\. 在 Hermes 的配置中增加 MCP 服务器项（路径与字段名以 Hermes 当前版本为准，常见文件为 `\*\*\~/.hermes/config.yaml\*\*` 下的 `\*\*mcp\_servers\*\*`）。与上列 \*\*stdio\*\* 等价的语义为：



\- `\*\*command`\*\*：指向 `\*\*Scripts\\xtqmt-mcp.exe`\*\* 的绝对路径。  

\- `\*\*args\*\*`：至少包含 `--transport`、`stdio`（或你选择的传输及 host/port/path）。  

\- `\*\*env\*\*`：至少 `\*\*MCP\_API\_BASE\_URL\*\*`、`\*\*MCP\_API\_TOKEN\*\*`（与 `\*\*API\_TOKEN\*\*` 一致）。Wheel 安装到 venv 后\*\*通常不需要\*\* `PYTHONPATH`。







\### 5.4 远程 MCP（可选）



若使用 `\*\*streamable-http`\*\* 并对公网暴露，务必 \*\*HTTPS 终止\*\*、限流、IP 白名单；MCP 进程访问下游 API 时仍使用 `\*\*MCP\_API\_TOKEN`\*\*，勿将 Token 写入可公开下载的配置仓库。



\---



\## 合规与安全提示



\- 实盘与对外暴露 API / MCP 前，请遵守当地监管、券商协议及贵司法务要求；本软件不替代券商终端，亦不提供收益承诺。

\- `\*\*API\_TOKEN`\*\*、`\*\*MCP\_API\_TOKEN`\*\* 与券商口令须妥善保管，勿提交到版本库；生产建议使用 HTTPS 或仅监听本机并配合强鉴权。

\- 各产品下载链接与安装步骤可能变更，请以 \*\*迅投、微软、Nous Hermes\*\* 等官方页面最新内容为准。





