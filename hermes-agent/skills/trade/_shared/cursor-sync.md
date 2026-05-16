<!--
last_updated: 2026-05-15
summary: Cursor IDE 与 hermes-agent/skills/trade 单一真源对齐方式（可选）。
-->

# Cursor 与 Hermes 包内 Skill 同步（可选）

**真源**：交易编排与合规以 **`hermes-agent/skills/trade/`** 为准（见 [`../TRUTH_SOURCE.md`](../TRUTH_SOURCE.md)）。`.cursor/skills/` 下文件面向 **IDE 开发/排障**，不假设 Cursor Agent 自动加载 Hermes 包内 Skill。

## 推荐做法：符号链接（Windows / Unix）

在仓库根或本机 Cursor 配置目录中，将需本地编辑的条目 **symlink** 到包内文件，例如（路径按本机调整）：

- `.cursor/skills/hermes-xtqmt-mcp` → 可保持现有独立文件，但正文顶部应 **链到** `hermes-agent/skills/trade/` 真源段落，避免双份阈值。

Unix 示例：

```bash
ln -sf ../../hermes-agent/skills/trade/stock-symbol-resolve/SKILL.md .cursor/skills/stock-symbol-resolve.md
```

Windows（管理员或开发者模式）可使用 `mklink`。

## 禁止

- 在 Cursor 侧维护 **第二套** 与 `signal-trader` 冲突的阈值或阶段定义。

<!-- version: 1.0 last_updated: 2026-05-15 -->
