#!/usr/bin/env python3
"""List markdown links under hermes-agent/skills/trade/ for migration / smoke checks."""
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _pack_root() -> Path:
    """Skill pack root: parent of `signal-trader/` (i.e. `skills/trade/`)."""
    here = Path(__file__).resolve()
    return here.parents[2]


def main() -> int:
    root = _pack_root()
    md_files = sorted(root.rglob("*.md"))
    for path in md_files:
        if "_probe_skill" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            target = m.group(1).strip()
            if target.startswith("http") or target.startswith("#"):
                continue
            path_only = target.split("#", 1)[0]
            if not path_only:
                continue
            rel = (path.parent / path_only).resolve()
            ok = rel.exists()
            flag = "OK" if ok else "MISSING"
            print(f"{flag}\t{path.relative_to(root)}\t->\t{target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
