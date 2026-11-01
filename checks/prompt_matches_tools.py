#!/usr/bin/env python3
"""The composed prompt names every real tool, and only real tools.

The prompt said "YOU HAVE EIGHT TOOLS" and listed thirteen while
routers/tools.py TOOLS held twenty-three. A prompt that drifts from
the code is a promise with no wire: the model cannot use a tool it has
never been told exists. This check fails when the composed prompt and
TOOLS disagree, in either direction, and when a heading in
tools_prompt.tools.md names a tool that does not exist.

Run:
    python3 checks/prompt_matches_tools.py
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

NOTES = "/home/bosly_accord/bosly-gov/tools_prompt.tools.md"


def main() -> int:
    print("")
    print("Invariant: the composed prompt matches routers/tools.py TOOLS")
    print("-" * 52)

    try:
        from routers.tools import TOOLS
    except Exception as e:
        print(f"  FAIL: cannot import TOOLS: {e}")
        print("SUMMARY: FAIL")
        return 1

    try:
        from routers.tool_loop import _read_prompt
        prompt = _read_prompt()
    except Exception as e:
        print(f"  FAIL: cannot compose the prompt: {e}")
        print("SUMMARY: FAIL")
        return 1

    real = {t["name"] for t in TOOLS}
    print(f"  TOOLS: {len(real)}")

    missing = sorted(n for n in real if not re.search(rf"^\s*{re.escape(n)}\s+—", prompt, re.MULTILINE))
    print(f"  missing from the prompt: {len(missing)}" + (f" {missing}" if missing else ""))

    # Any name the tool list section mentions that TOOLS does not have.
    m = re.search(r"=== THE TOOLS \(\d+\) ===(.*?)(?:\n=== |\Z)", prompt, re.DOTALL)
    listed = set()
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^\s*([a-z_][a-z0-9_]+)\s+—", line)
            if mm:
                listed.add(mm.group(1))
    phantom = sorted(listed - real)
    print(f"  in the prompt but not in TOOLS: {len(phantom)}" + (f" {phantom}" if phantom else ""))

    # Headings in the notes file must be real tools.
    try:
        notes = open(NOTES, encoding="utf-8").read()
    except OSError:
        notes = ""
    headings = set(re.findall(r"^## ([a-z_][a-z0-9_]+)\s*$", notes, re.MULTILINE))
    bad_headings = sorted(headings - real)
    print(f"  notes headings not in TOOLS: {len(bad_headings)}" + (f" {bad_headings}" if bad_headings else ""))

    # The old stale literal must be gone.
    stale = "EIGHT TOOLS" in prompt
    print(f"  stale 'EIGHT TOOLS' literal: {'PRESENT' if stale else 'gone'}")

    ok = not missing and not phantom and not bad_headings and not stale
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
