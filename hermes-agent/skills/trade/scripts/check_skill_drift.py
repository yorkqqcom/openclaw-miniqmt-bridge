#!/usr/bin/env python3
"""Heuristic checks for accidental duplication of signal-trader logic in other skills.

Heuristic drift checks for non-signal-trader skills — advisory only;
exit code 0 unless --strict is passed and any rule fires (reserved for CI).

Usage (from repo root):
  python hermes-agent/skills/trade/scripts/check_skill_drift.py
  python hermes-agent/skills/trade/scripts/check_skill_drift.py --strict
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Paths relative to hermes-agent/skills/trade/
SOURCE_OF_TRUTH = Path("signal-trader/SKILL.md")

# (substring or regex-like simple 'in', message) — keep few high-signal needles.
DRIFT_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    ("综合评分 = 技术评分 × 0.7 + 基本面评分 × 0.3", "疑似复制 signal-trader 综合评分公式"),
    ("**NOT 规则（一票否决", "疑似复制 signal-trader NOT 规则小节"),
    ('<a id="account-id-user-facing"></a>', "重复定义 account-id-user-facing 锚点（应链到 signal-trader）"),
)


def _skill_pack_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check non-signal-trader SKILL.md for drift markers.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any warning (for future CI; default prints only).",
    )
    args = parser.parse_args()
    root = _skill_pack_root()
    st = root / SOURCE_OF_TRUTH
    if not st.is_file():
        print(f"ERROR: missing source of truth {st}", file=sys.stderr)
        return 2

    warnings: list[str] = []
    for path in sorted(root.glob("*/SKILL.md")):
        rel = path.relative_to(root)
        if rel == SOURCE_OF_TRUTH:
            continue
        text = path.read_text(encoding="utf-8")
        for needle, msg in DRIFT_SUBSTRINGS:
            if needle in text:
                warnings.append(f"WARN\t{rel}\t{msg}\tmatched: {needle[:48]}...")

    for line in warnings:
        print(line)
    if not warnings:
        print("OK\tno drift markers in non-signal-trader SKILL.md files")
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
