#!/usr/bin/env python3
"""Validate <!-- stage_id: ... --> anchors in signal-trader and optional refs elsewhere.

- Collects allowed ids from signal-trader/SKILL.md HTML comments.
- Fails if fewer than 5 ids (A–E pipeline).
- Any other */SKILL.md under hermes-agent/skills/trade/ mentioning stage_id: <id> must use allowed id.

Usage from repo root:
  python hermes-agent/skills/trade/scripts/check_stage_id_refs.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

STAGE_COMMENT_RE = re.compile(r"<!--\s*stage_id:\s*([A-Za-z0-9_]+)\s*-->")
STAGE_REF_RE = re.compile(r"\bstage_id:\s*([A-Za-z0-9_]+)")


def _pack_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = _pack_root()
    st = root / "signal-trader" / "SKILL.md"
    if not st.is_file():
        print(f"ERROR: missing {st}", file=sys.stderr)
        return 2
    allowed = set(STAGE_COMMENT_RE.findall(st.read_text(encoding="utf-8")))
    if len(allowed) < 5:
        print(
            f"ERROR: expected >=5 stage_id comments in signal-trader, found {sorted(allowed)}",
            file=sys.stderr,
        )
        return 1
    print(f"OK\tsignal-trader stage_id anchors: {sorted(allowed)}")

    bad: list[str] = []
    for path in sorted(root.glob("*/SKILL.md")):
        rel = path.relative_to(root)
        if rel.parts[0] == "signal-trader":
            continue
        text = path.read_text(encoding="utf-8")
        for m in STAGE_REF_RE.finditer(text):
            rid = m.group(1)
            if rid not in allowed:
                bad.append(f"{rel}\tunknown stage_id ref: {rid}")
    for line in bad:
        print(f"WARN\t{line}")
    if bad:
        print("ERROR\tunknown stage_id reference(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
