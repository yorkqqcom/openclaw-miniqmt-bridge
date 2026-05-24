# Windows：curl / 下载式安装（第一阶段不提供源码 zip）

本文面向 **仅 Windows** 的对外交付：客户 **不下载完整源码树**，只通过 **HTTPS 获取 `install.ps1` + 校验 + 下载发布 zip** 完成安装。`install.sh` 仍保留在仓库内供非 Windows 场景，**不作为本阶段对外主路径**。

**说明**：Wheel 包内仍含 Python 包文件（可读性高于 Nuitka）；若需尽量避免交付可读逻辑，请改用 **Nuitka zip + `install_nuitka_zip.ps1`**。

## 快速：一行 PowerShell（GitHub Releases + bootstrap）

**前提**：已安装 **Python 3.10+**；将 **`OWNER` / `REPO` / `TAG`** 换成你的仓库与 Release 的 Tag；该 Tag 的 Release 资源中须包含 **`remote_install_bootstrap.ps1`**（且其中默认的 zip 名与 **SHA-256** 已与本次 zip 一致）。

```powershell
$u='https://github.com/OWNER/REPO/releases/download/TAG/remote_install_bootstrap.ps1'; $r=Invoke-WebRequest -Uri $u -UseBasicParsing; iex ($(if ($r.Content -is [byte[]]) { [System.Text.Encoding]::UTF8.GetString($r.Content) } else { [string]$r.Content }))
```

**可选安装目录**：执行上一行前设置 `$env:OPENCLAW_INSTALL_ROOT='D:\path\to\openclaw-install'`（详见 [scripts/install/remote_install_bootstrap.ps1](../scripts/install/remote_install_bootstrap.ps1)）。

维护者打 zip、上传资产、更新 bootstrap 的完整步骤见 [release_packaging_flow.md](release_packaging_flow.md)。安全权衡与「先下载再 `-File`」主路径见下文 **「安全主路径」** 与 **「远程一键安装」**。

## 第一阶段推荐组合（无源码 zip）

| 客户环境 | 发布 zip 内容 | 安装脚本 | `-BundleLayout` |
| --- | --- | --- | --- |
| 已安装 Python 3.10+ | **wheelhouse**（全部依赖与本项目的 `.whl`，**以及** 同 zip 内的 `.env.example`、**`configs/`**、**`ui/`**（含 `index.html` 与 **`admin/`** 网关页）、**`scripts/run_ui.py`** 与建议的 **`scripts/import_strategy_profiles_from_yaml.py`**（文件库策略离线入库），不含完整 `src/` 目录树） | `install.ps1` | `Wheelhouse`（**默认**） |
| 不能装 Python | **Nuitka 目录产物** zip | `install_nuitka_zip.ps1` | 不适用 |

**不要**在第一阶段对外提供含 `pyproject.toml` + `src/` + `scripts/` 的源码 zip；若内部或合作方需要源码安装，可单独走 `-BundleLayout SourceTree`（不作为对外默认）。

安装完成后，venv 内提供 **`xtqmt-api.exe` / `xtqmt-runtime.exe` / `xtqmt-mcp.exe`**（由 `pyproject.toml` 的 `[project.scripts]` 生成）；`install.ps1` 会在安装根目录生成 **`Run-API.cmd` / `Run-Runtime.cmd` / `Run-MCP.cmd`**，并在 zip 内含 **`ui/`** 与 **`scripts/run_ui.py`** 时生成 **`Run-UI.cmd`**（用 venv 的 Python 托管管理台；浏览器默认 **`http://127.0.0.1:8080/`**，网关 MCP 管理 **`http://127.0.0.1:8080/admin/`**）。脚本会设置 **`OPENCLAW_PROJECT_ROOT`** 与 **`XTQMT_PROJECT_ROOT`** 指向安装根，以便加载同目录下的 `.env`。发布 zip 内的 **`configs/`**、**`ui/`**、**`scripts/run_ui.py`**、（若打包）**`scripts/import_strategy_profiles_from_yaml.py`** 会复制到安装根（见 [release_packaging_flow.md](release_packaging_flow.md)）。**`Run-Runtime.cmd`** 默认执行 **`--mode live --env prod`**（完整策略循环，自动交易策略）。**盯盘**默认由 **`Run-API.cmd`** 后台线程执行（见 **`deployment.md` §3.2**）。**`Run-Runtime-sync.cmd`** 为 **`--sync-db-only`**（仅对账/健康/快照写库，**不要求**活动 **`strategy_profiles`**）。**`run_live.py` / `xtqmt-live`** 等价于 **`xtqmt-runtime --mode live`**（参数可透传，启动时有 deprecation 提示）。

## 安全主路径（推荐写进对外文档）

1. 使用 **HTTPS** 固定域名托管 `install.ps1`、`SHA256SUMS` 与发布 zip（勿使用明文 HTTP）。
2. 客户 **先下载** `install.ps1` 到本机（勿宣传无校验的 `curl … \| powershell` / `iwr … \| iex`）。
3. 对照你发布的 **SHA-256**（见 `SHA256SUMS`）校验安装脚本与 zip（PowerShell：`Get-FileHash -Algorithm SHA256 .\install.ps1`）。
4. 执行示例（wheelhouse，默认）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 `
  -DownloadBaseUrl "https://你的域名/openclaw-miniqmt-bridge/v0.1.3/" `
  -BundleFileName "openclaw-miniqmt-bridge-0.1.3-wheels.zip" `
  -ExpectedSha256 "<来自 SHA256SUMS 的小写 hex>"
```

可选：`-BundleLayout SourceTree`（仅当你**主动**提供源码 zip 时）。

开发联调可临时使用 `-SkipChecksum`（会打印警告），**不得**作为生产默认。

## 远程一键安装（`irm` / `iex` / `curl` 管道类，弱于主路径）

与「先下载、本地 `-File`、可对 `install.ps1` 做哈希」相比，下面方式**等价于远程拉取脚本并执行**：你信任 **HTTPS + GitHub + 该 ref 上的脚本内容**；**不**校验 `install.ps1` 本体，仅沿用 `install.ps1` 内对 **wheel zip** 的 SHA-256 校验。

发版前请在本仓库更新 [scripts/install/remote_install_bootstrap.ps1](../scripts/install/remote_install_bootstrap.ps1) 顶部的 **`ReleaseTag` / `BundleFileName` / `ExpectedSha256` 默认值**，再打 **Tag**；**建议**把同文件作为 **Release Asset** 上传（与 `install.ps1` 并列），客户用 **`releases/download/<Tag>/remote_install_bootstrap.ps1`**，通常比 **`raw.githubusercontent.com`** 更易连通。

**Tag 名以 Release 页 URL 为准**：`https://github.com/<owner>/<repo>/releases/tag/<Tag名>` 里最后一段就是 **`ReleaseTag`**（例如 `openclaw-miniqmt-bridge`，不必是 `v0.1.3`）。

### PowerShell（优先：Release 上的 bootstrap）

**推荐单行**已写在本文最上方的 **「快速：一行 PowerShell」**；本节给出等价多行写法与备选 URL，便于排查。

下例与 [openclaw-miniqmt-bridge 0.1.3](https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/tag/openclaw-miniqmt-bridge) 的 **Assets** 一致；将 **OWNER / REPO / TAG** 换成你的仓库即可。

部分环境（含部分 PowerShell 7 + GitHub 将脚本标为二进制时）下，`Invoke-WebRequest` 的 **`.Content` 为 `byte[]`**，直接 `iex (...Content)` 会报错：`无法将“System.Byte[]”转换为参数“Command”所需的类型“System.String”**。下面写法**同时兼容** `Content` 为字符串或字节数组：

```powershell
$u = "https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/download/openclaw-miniqmt-bridge/remote_install_bootstrap.ps1"
$r = Invoke-WebRequest -Uri $u -UseBasicParsing
$script = if ($r.Content -is [byte[]]) { [System.Text.Encoding]::UTF8.GetString($r.Content) } else { [string]$r.Content }
iex $script
```

若你确认本机 `Invoke-RestMethod` 返回的是字符串，也可简写为（在少数环境下仍可能是 `byte[]`，失败则用上一段）：

```powershell
iex (Invoke-RestMethod -Uri "https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/download/openclaw-miniqmt-bridge/remote_install_bootstrap.ps1" -UseBasicParsing)
```

可选：下载后对照 Release 页上 **`remote_install_bootstrap.ps1` 的 sha256** 再执行（先 `OutFile` 再 `Get-FileHash` 再 `-File`）。

### 备选：raw.githubusercontent.com（需该 Tag 的 Git 树里含此文件）

```powershell
iex (irm "https://raw.githubusercontent.com/yorkqqcom/openclaw-miniqmt-bridge/openclaw-miniqmt-bridge/scripts/install/remote_install_bootstrap.ps1" -UseBasicParsing)
```

若 **`raw.githubusercontent.com` 连接失败**（如 `Connection was reset`），请只用 **Release 资产 URL**（上一节）或浏览器下载 **`install.ps1`** 后走「安全主路径」的 **`-File .\install.ps1`**。

### 用 `curl.exe` 拉 Release 上的 bootstrap（一条命令）

```powershell
iex ((curl.exe -fsSL "https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/download/openclaw-miniqmt-bridge/remote_install_bootstrap.ps1"))
```

在 PowerShell 中请使用 **`curl.exe`**，避免 `curl` 被解析为 `Invoke-WebRequest`。

### Git Bash / 类 Unix 上管道进 PowerShell（Release 资产）

```bash
curl -fsSL "https://github.com/yorkqqcom/openclaw-miniqmt-bridge/releases/download/openclaw-miniqmt-bridge/remote_install_bootstrap.ps1" | powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression ([Console]::In.ReadToEnd())"
```

### 覆盖默认参数（已下载 bootstrap 到本地时）

在磁盘上执行时可传参（**`iex (irm …)` 无法直接传参到子脚本**，需本地文件或包装一行 `& { … }`）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\remote_install_bootstrap.ps1 -ReleaseTag "openclaw-miniqmt-bridge" -ExpectedSha256 "<hex>"
```

## `install.ps1` 参数摘要

- **`-DownloadBaseUrl`**：HTTPS 基址（建议以 `/` 结尾）。
- **`-BundleFileName`**：仅文件名，与基址拼接为完整 URL。第一阶段请使用 **wheelhouse zip** 或后续 Nuitka zip 的文件名。
- **`-ExpectedSha256`**：该 zip 的小写十六进制 SHA-256；生产环境应必填。
- **`-InstallRoot`**：安装目录，默认 `.\openclaw-install`。
- **`-BundleLayout`**：默认 **`Wheelhouse`**；`SourceTree` 仅用于你明确提供源码树 zip 时。
- **`-PythonExe`**：默认 `python`。

**`.env.example`**：若 wheel zip 内未附带，请你在发布页单独提供或由运维下发；也可在构建 wheel zip 时放入仓库根的 `.env.example`（与 `.whl` 同包一层 zip）。

安装完成后按 [README.md](../README.md) 配置 `.env`（`APP_DB_URL`、`API_TOKEN`、`TRADING_ENABLED` 等）。

## 无 Python：Nuitka zip

使用 [scripts/install/install_nuitka_zip.ps1](../scripts/install/install_nuitka_zip.ps1) 下载并解压 **Nuitka 目录** zip，在安装根生成 `Run-*.cmd`。构建流程见 [README.md](../README.md)「Nuitka 打包」。

## Linux / macOS（非本阶段对外）

仓库内保留 [scripts/install/install.sh](../scripts/install/install.sh) 供需要时使用；对外第一阶段以 Windows 文档为准。

## 维护者：生成 `SHA256SUMS`

在放置 `install.ps1`、发布 zip 的**同一目录**执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install/generate_sha256sums.ps1 -ArtifactDir "D:\path\to\release\files"
```

## Nuitka 打包形态与入口

与 [README.md](../README.md) 一致：

- **默认**：**目录模式**（勿用 `-OneFile`），再打成客户 zip。
- **入口**：至少 **runtime**、**api**、**ui**（`xtqmt_ui.exe`，管理台）；需要 MCP 时包含 **mcp**。默认 Nuitka 流水线**不再**单独打 **`xtqmt_live.exe`**；实盘编排请用 **`xtqmt_runtime.exe`** 的 live 模式或源码 **`python scripts/run_live.py`**。
- **校验 / 裁剪**：`scripts/verify_bundle.ps1`、`scripts/prepare_release_bundle.ps1`。

## 离线企业环境

将整个发布目录（`install.ps1`、`SHA256SUMS`、zip 与 `.env.example` 等说明）打成 **离线 U 盘包**；安装机不出网时仍应先校验哈希再执行脚本。
