#!/usr/bin/env python3
"""Verify relative markdown links under hermes-agent/skills/trade/ resolve to existing files.

Exit 1 if any target is missing (for CI). Usage from repo root:
  python hermes-agent/skills/trade/scripts/check_skill_pack_links.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _pack_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = _pack_root()
    repo_root = root.parent.parent
    missing: list[str] = []
    checked = 0
    for path in sorted(root.rglob("*.md")):
        if "_probe_skill" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path_only = target.split("#", 1)[0]
            if not path_only:
                continue
            checked += 1
            resolved = (path.parent / path_only).resolve()
            try:
                resolved.relative_to(repo_root.resolve())
            except ValueError:
                continue
            if not resolved.exists():
                missing.append(f"{path.relative_to(root)}\t->\t{target}")
    for line in missing:
        print(f"MISSING\t{line}")
    if missing:
        print(f"ERROR\t{len(missing)} missing link(s) under skill pack", file=sys.stderr)
        return 1
    print(f"OK\tchecked {checked} relative link(s) under {root.name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
