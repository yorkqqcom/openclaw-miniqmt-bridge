# Trading Ecosystem Architecture

> Context for the broader system that `signal-trader` operates within.
> Three components: delivery products + internal base.

## Component Map

```text
┌─────────────────────────────────────────────────────┐
│         xtqmt-user — MCP Trading Server             │
│  (Skill Store core product / 交付品 1)               │
│                                                     │
│  A 股限价执行 / 持仓 / 风控 / 订单审计 / 可计费       │
│  License 绑定机器+用户，沙盒/生产环境隔离              │
│  Agent 可读的 tool description + 结构化错误           │
│  HTTP API + MCP tools (16+ 工具)                     │
│  运行方式：xtqmt_mcp.exe --transport streamable-http  │
│           --host 0.0.0.0 --port 8765 --path /mcp     │
└──────────────────┬──────────────────────────────────┘
                   │ StreamableHTTP (session handshake)
                   ▼
┌─────────────────────────────────────────────────────┐
│   openclaw-miniqmt-bridge — Windows Bridge          │
│  (Delivery installer / 交付品 2)                     │
│                                                     │
│  Windows 一键部署                                    │
│  连接 Cursor / Claude Desktop / OpenClaw / Hermes    │
│  附接入文档 + 视频                                   │
│  QMT-投研版 or 极简版用户开箱即用                     │
└──────────────────┬──────────────────────────────────┘
                   │ local network (172.24.144.x)
                   ▼
┌─────────────────────────────────────────────────────┐
│     tusharestock — Data Pipeline (Internal)         │
│  (Technical depth / 自用基座，不公开销售)             │
│                                                     │
│  tusharestockForPostgreSQL: 数据入仓 + 特征工程       │
│  zhongxin-stock: 内部研究评估                        │
│  ML 回测管道                                        │
│  定位：投研基础设施，不面向 C 端                       │
└─────────────────────────────────────────────────────┘
```

## Network Topology (WSL + Windows)

```
Windows (172.24.144.1)
├── QMT 客户端 (xtquant)
├── xtqmt_mcp.exe (8765/mcp/)  ← StreamableHTTP, session required
└── tushare MCP (8001/mcp)     ← StreamableHTTP, no session needed

WSL (Hermes Agent)
├── config.yaml → mcp_servers
│   ├── tushare-hermes-remote: http://172.24.144.1:8001/mcp
│   └── xtqmt-trading-remote: http://172.24.144.1:8765/mcp/
└── Hermes TUI
```

## StreamableHTTP Server Variations

| Aspect | tushare (8001) | xtqmt (8765) |
|--------|----------------|--------------|
| Session required | No | Yes |
| Response format | JSON | SSE events |
| URL trailing slash | Optional | Required (`/mcp/`) |
| Auth | None | None (local) |
| Stateful | No | Yes (per session) |

## Business Positioning

**One-liner**: "Not a stock-picking app for humans — an auditable execution layer for AI Agents."

**Two delivery products + one internal base:**
1. **xtqmt-user MCP Server** — the product that goes on Skill Store
2. **openclaw-miniqmt-bridge** — the installer that makes it deployable
3. **tusharestock** — internal data/research pipeline, not sold publicly

**Compliance boundary (important for OPC / Skill Store):**
- API calls contain no investment advice
- Full audit logs: caller identity, timestamp, complete params
- TRADING_ENABLED global switch
- `max_order_amount` per-order risk control
- Caller bears all investment decisions
