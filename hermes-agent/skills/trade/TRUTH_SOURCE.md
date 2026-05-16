# 策略与交易数值真源（Hermes-Agent）

**A 股信号交易全流程、阈值、阶段 A–E、MCP 调用顺序、多账户与 `account_id` 用户可见规则** 的 **唯一真源** 为：

- [`signal-trader/SKILL.md`](signal-trader/SKILL.md)

编排 Skill（`daily-morning-check`、`closing-review`）、原子操作 Skill（`buy-single` 等）、`stock-symbol-resolve` **不得**另写一套与之冲突的阈值或阶段定义；仅允许 **摘要 + 链到真源**。

人设与报告壳见 `profiles/*/SOUL.md`。
