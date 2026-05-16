#!/usr/bin/env python3
"""Weak check: tool names listed in docs/DATA_AND_MCP_RESOURCE_CATALOG §4.1 should appear in mcp-data-availability.md.

Non-blocking (exit 0): prints WARN lines for catalog tools not mentioned in the availability doc.
Usage from repo root:
  python hermes-agent/skills/trade/scripts/check_catalog_tool_mentions.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _catalog_tools(catalog: Path) -> set[str]:
    text = catalog.read_text(encoding="utf-8")
    tools: set[str] = set()
    started = False
    for line in text.splitlines():
        if "### 4.1" in line:
            started = True
            continue
        if started and re.match(r"^##\s+5\.", line):
            break
        if not started:
            continue
        m = re.search(r"\|\s*`([a-z0-9_]+)`\s*\|", line)
        if m:
            tools.add(m.group(1))
    return tools


def main() -> int:
    root = _repo_root()
    catalog = root / "docs" / "DATA_AND_MCP_RESOURCE_CATALOG.md"
    avail = root / "hermes-agent" / "skills" / "trade" / "signal-trader" / "references" / "mcp-data-availability.md"
    if not catalog.is_file() or not avail.is_file():
        print("SKIP\tmissing catalog or mcp-data-availability.md", file=sys.stderr)
        return 0
    tools = _catalog_tools(catalog)
    blob = avail.read_text(encoding="utf-8")
    missing = sorted(t for t in tools if t and f"`{t}`" not in blob and t not in blob)
    for t in missing:
        print(f"WARN\tcatalog tool not mentioned in mcp-data-availability.md: {t}")
    if not missing:
        print(f"OK\tall {len(tools)} catalog §4.1 tool names have a mention in mcp-data-availability.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
