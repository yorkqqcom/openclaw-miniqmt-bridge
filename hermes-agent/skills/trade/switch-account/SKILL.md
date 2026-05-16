---
name: switch-account
description: >-
  Use when user says 切换账号 / 换账户 / 用哪个账户下单 / 当前操作账户 / lock trading account.
  Thin skill: list_trading_accounts + lock logical account_id for session; no default account;
  prerequisite connect via API/UI. Links to signal-trader multi-account protocol.
version: 1.0.1
author: Hermes Agent
tags: [trading, multi-account, mcp, xtqmt]
metadata:
  hermes:
    related_skills: [signal-trader, closing-review, daily-morning-check, stock-symbol-resolve, buy-single, sell-single, buy-batch, sell-batch, cancel-order, cancel-orders-batch, query-today-orders, query-today-trades]
    requires_soul: profiles/trade/SOUL.md
---

# switch-account — 锁定当前操作逻辑账户

## Overview

在 **多账户** 或需显式对齐的场景下，由 Agent 在**当前对话**中锁定后续 `get_*` / `place_*` / `cancel_*` 使用的 **`account_id`**（与库内 **`trading_account_profiles.logical_id`** 一致）。**不**替代管理台或 **`POST /api/v1/trading-accounts/{logical_id}/connect`** 的物理连接；仅处理**逻辑上下文**与输出话术模板。

权威交易阶段见 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md)；多账户执行协议见该文 **[多账户执行协议](../signal-trader/SKILL.md#多账户执行协议)**。

## When to Use

- 用户说「切换账号」「换账户」「用哪个账户」「锁定 account」「当前用哪张户下单」等。
- **`list_accounts` / `list_trading_accounts` 显示 ≥2 个已连接**且用户未给出明确 `logical_id`，而后续将进入 [`signal-trader`](../signal-trader/SKILL.md) 阶段 C/D 等**含 Y/N 或限价确认**的流程 — **须先**完成本 skill 或等价锁定，避免无账号前缀的下单确认（见 [`signal-trader` 用户可见文案规则](../signal-trader/SKILL.md#account-id-user-facing)）。

## When NOT to Use

- 无 xtqmt / openclaw-miniqmt-bridge MCP 或未启动 API+MCP 的环境。
- 用户仅做行情/信号分析、**不涉及**任何账户维度 MCP 调用时。

## Prerequisites

与 [`../signal-trader/SKILL.md`](../signal-trader/SKILL.md) 多账户协议及仓库根 [`readme.md`](../../../../readme.md) §5.4 一致：先 API、各户 **connect**、再 MCP。

### MCP 工具语义（须按此解析，勿自行猜测）

| 工具 | 底层 | 返回要点 |
|------|------|----------|
| **`list_trading_accounts`** | `GET /api/v1/trading-accounts` | 合并档案与编排状态；每行 **`logical_id`**、**`connection`** 等 — **优先**用于判断是否需要 connect。 |
| **`list_accounts`** | `GET /health` | `data.accounts`：**字符串列表**，为编排器 **已连接** 的 logical id；**无**逐条 `connection` 对象。 |

要看档案与连接态 → **`list_trading_accounts`**；仅要当前 runtime id 列表 → **`list_accounts`** 或由上表推导。

按账户的 `get_*` / `place_*` / `cancel_*` / `snapshot_ingest_account` 均须 **`account_id`**；核实见仓库 [`src/xtqmt_system/interfaces/mcp_server.py`](../../../../src/xtqmt_system/interfaces/mcp_server.py)。

## 执行步骤

1. **`health_check`** — 确认 API / xtqmt 状态可接受。
2. **`list_trading_accounts`**（主）— 解析每行 **`logical_id`** 与 **`connection`**；辅以 **`list_accounts`** 核对 `data.accounts`。
3. **分支**（与 [`signal-trader` 多账户执行协议](../signal-trader/SKILL.md#多账户执行协议) 一致）：
   - **单账户直通**：若 `list_accounts` → `data.accounts` **仅 1 个元素**（或等价仅一个已连接 runtime），可**跳过**「请从列表选择」，直接输出 **`当前唯一操作账户 account_id=<该 id>`**，并进入步骤 4（有效期说明仍须给出）。
   - **用户口述 ID**：用户已给出 **`logical_id`** → 校验其存在于 **`list_trading_accounts`** 且已连接（或档案存在则引导 **`POST /api/v1/trading-accounts/{logical_id}/connect`**）；**通过则直接锁定**，不必展示全表；**失败**则展示合并列表 + connect 引导。
   - **多账户且未口述**：≥2 已连接且用户未指定 → **列出**候选（`logical_id` + 简要连接态），请用户选定后再锁定。
4. **确认切换**：向用户复述：**`后续本对话锁定 account_id=<logical_id>`**。并声明：**「除非您再次切换账号或开启新会话，否则上述锁定持续有效。」**
5. **断连兜底**：在即将调用 `place_*` / `cancel_*` 前若 `health_check` 或工具错误表明目标账户不可用 → **停止**下单类确认；重新执行步骤 1–2 或引导 connect。
6. （可选）用户要求仅保留单一连接：说明 **`POST /api/v1/trading-accounts/{logical_id}/disconnect`** 对其余 id 的影响；默认**不**建议无故断开他户。

## 标准输出模板（供 signal-trader / closing-review 对齐）

**单行锁定（单账户或已锁定一节内）：**

```text
当前操作账户 account_id=<logical_id>
以下限价/撤单/复盘段落均针对该账户，直至您再次切换或新会话。
```

**并行多账户（同一回复含多节计划或确认）：**

```text
以下计划涉及 N 个账户（N=2）
--- 账户：<logical_id_A> ---
当前操作账户 account_id=<logical_id_A>
（该户标的与金额要点…）
--- 账户：<logical_id_B> ---
当前操作账户 account_id=<logical_id_B>
（该户标的与金额要点…）
```

## 语义回归用例（合并后人工走查）

1. `data.accounts` 仅 1 个 → 输出「当前唯一操作账户…」，无强制列表选择。  
2. ≥2 已连接且用户未说 id → **不得**发出含 Y/N 的下单确认；先本 skill。  
3. 口述有效 id → 校验后锁定，不必展全表。  
4. 口述无效 id → 全表 + connect。  
5. 阶段 C/D 对外首行含 `account_id=`。  
6. 并行两户：N=2 + 两节 `--- 账户：… ---`。  
7. [`closing-review`](../closing-review/SKILL.md) 分节：每节首行标注账户。  
8. 工具报错暗示断连 → 重新选户 / connect，不静默改户发单。

## Verification

- 相对链接可打开：`../signal-trader/SKILL.md`、`../closing-review/SKILL.md`、`../TRUTH_SOURCE.md`。

<!-- version: 1.0.1 last_updated: 2026-05-13 -->
