#!/usr/bin/env python3
"""Write hermes-agent/skills/trade/.cache/data_readiness.json by probing Tushare Hermes MCP (optional).

Hybrid cache model: run on a timer (e.g. every 15m) or ad hoc; Skills read the file and
surface stale/partial states in the data-quality declaration.

Environment:
  HERMES_DATA_MCP_URL       POST URL for MCP (e.g. http://127.0.0.1:8001/mcp)
  HERMES_DATA_MCP_API_KEY   Optional X-Api-Key header

Usage from repo root:
  python hermes-agent/skills/trade/scripts/preflight_data_readiness.py
  python hermes-agent/skills/trade/scripts/preflight_data_readiness.py --stub-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def _pack_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_output_path() -> Path:
    cache = _pack_root() / ".cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache / "data_readiness.json"


def _normalize_mcp_post_url(raw: str) -> str:
    u = raw.strip().rstrip("/")
    if not u.endswith("/mcp"):
        u = f"{u}/mcp"
    return u


def _mcp_tools_call(url: str, tool: str, arguments: dict, api_key: str | None) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _unwrap_mcp_envelope(raw: dict) -> dict:
    """Best-effort parse MCP tools/call JSON envelope into inner JSON dict."""
    if raw.get("error"):
        return {"success": False, "message": str(raw.get("error"))}
    try:
        content = raw["result"]["content"][0]["text"]
        return json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError):
        return {"success": False, "message": "unparseable MCP envelope", "_raw": raw}


def _classify_inner(inner: dict, _tool: str) -> tuple[str, str]:
    if inner.get("success") is False:
        return "error", str(inner.get("message") or inner.get("error") or "unknown")
    data = inner.get("data")
    if data is None:
        return "empty", "no data key"
    if isinstance(data, dict) and not data:
        return "empty", "empty object"
    if isinstance(data, list) and len(data) == 0:
        return "empty", "empty list"
    return "ok", "non-empty"


def _stub_payload() -> dict:
    now = datetime.now(timezone.utc)
    stale = now + timedelta(seconds=900)
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "stale_after": stale.isoformat(),
        "cache_ttl_seconds": 900,
        "mcp_endpoint_configured": False,
        "note": "stub-only: set HERMES_DATA_MCP_URL to run live probes",
        "probes": [
            {
                "tool": "health_check",
                "status": "not_configured",
                "checked_at": now.isoformat(),
                "detail": "HERMES_DATA_MCP_URL unset or --stub-only",
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Default: hermes-agent/skills/trade/.cache/data_readiness.json",
    )
    parser.add_argument("--stub-only", action="store_true", help="Write stub JSON without network")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any probe status is error (live mode only)",
    )
    args = parser.parse_args()

    out = args.output or _default_output_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.stub_only:
        out.write_text(json.dumps(_stub_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK\twrote stub -> {out}")
        return 0

    raw_url = (os.environ.get("HERMES_DATA_MCP_URL") or "").strip()
    if not raw_url:
        out.write_text(json.dumps(_stub_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK\tno HERMES_DATA_MCP_URL; wrote stub -> {out}")
        return 0

    url = _normalize_mcp_post_url(raw_url)
    api_key = (os.environ.get("HERMES_DATA_MCP_API_KEY") or "").strip() or None
    now = datetime.now(timezone.utc)
    stale = now + timedelta(seconds=900)

    end = date.today()
    start = end - timedelta(days=35)
    start_s = start.isoformat()
    end_s = end.isoformat()

    probe_specs: list[tuple[str, dict]] = [
        ("health_check", {}),
        ("get_trade_calendar_statistics", {}),
        (
            "get_index_daily_range",
            {"ts_code": "000001.SH", "start_date": start_s, "end_date": end_s, "limit": 5},
        ),
        (
            "get_fund_share_change_range",
            {"ts_code": "510300.SH", "start_date": start_s, "end_date": end_s, "limit": 5},
        ),
    ]

    probes: list[dict] = []
    any_error = False
    for tool, arguments in probe_specs:
        try:
            raw = _mcp_tools_call(url, tool, arguments, api_key)
            inner = _unwrap_mcp_envelope(raw)
            status, detail = _classify_inner(inner, tool)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
            status, detail = "error", str(e)
        if status == "error":
            any_error = True
        probes.append(
            {
                "tool": tool,
                "status": status,
                "checked_at": now.isoformat(),
                "detail": detail[:500],
            }
        )

    payload = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "stale_after": stale.isoformat(),
        "cache_ttl_seconds": 900,
        "mcp_endpoint_configured": True,
        "mcp_url_host": urllib.parse.urlparse(url).netloc,
        "probes": probes,
    }

    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK\twrote {len(probes)} probe(s) -> {out}")
    if args.strict and any_error:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
