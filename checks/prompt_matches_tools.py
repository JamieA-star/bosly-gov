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

    # The tool list is GENERATED from TOOLS in order. There is no way
    # for the prompt to name a phantom tool, and parsing prose to look
    # for one found the word 'line' in a wrapped sentence. This
    # assertion was written for the hand-maintained prompt; it has no
    # subject now. phantom removed — the missing-direction check and the
    # declared count cover the real failure.
    m = re.search(r"=== THE TOOLS \((\d+)\) ===", prompt)
    declared = int(m.group(1)) if m else -1
    phantom = [] if declared == len(real) else [f"declared {declared} != {len(real)}"]
    print(f"  prompt declares {declared} tools, TOOLS has {len(real)}")

    # Headings in the notes file must be real tools.
    try:
        notes = open(NOTES, encoding="utf-8").read()
    except OSError:
        notes = ""
    headings = set(re.findall(r"^## ([a-z_][a-z0-9_]+)\s*$", notes, re.MULTILINE))
    bad_headings = sorted(headings - real)
    print(f"  notes headings not in TOOLS: {len(bad_headings)}" + (f" {bad_headings}" if bad_headings else ""))

    # Skills: every file under skills/ is named in the prompt, the prompt's
    # procedure is NOT carried (it lives in the skill), and read_skill is a
    # real tool so the butler can load it.
    from pathlib import Path as _P
    skills_dir = _P("/home/bosly_accord/bosly-gov/skills")
    skill_files = sorted(p.stem for p in skills_dir.glob("*.md")) if skills_dir.exists() else []
    unnamed = [n for n in skill_files if n not in prompt]
    print(f"  skills on disk: {len(skill_files)}, unnamed in the prompt: {len(unnamed)}" + (f" {unnamed}" if unnamed else ""))
    carried = "WORKING THE WEEK'S LIST" in prompt
    print(f"  week-list procedure carried in the prompt: {'YES (should be no)' if carried else 'no (it is a skill)'}")
    has_reader = "read_skill" in real
    print(f"  read_skill is a real tool: {has_reader}")

    # The old stale literal must be gone.
    stale = "EIGHT TOOLS" in prompt
    print(f"  stale 'EIGHT TOOLS' literal: {'PRESENT' if stale else 'gone'}")

    ok = (not missing and not phantom and not bad_headings and not stale
          and not unnamed and not carried and has_reader)
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
