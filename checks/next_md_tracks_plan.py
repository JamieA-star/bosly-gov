#!/usr/bin/env python3
"""NEXT.md must not list as open an item PLAN.md marks done.

The front door is maintained by the butler, and it sometimes promises
to update it and does not. A prompt rule is not a control; this is.
"""
import re, sys
PLAN = "/home/bosly_accord/bosly-gov/PLAN.md"
NEXT = "/home/bosly_accord/bosly-gov/NEXT.md"

done = set()
for line in open(PLAN, encoding="utf-8"):
    m = re.match(r"^\[x\]\s+(?:\[LIVE\]\s+)?([\w.\-]+)", line)
    if m:
        done.add(m.group(1))

open_ids = set()
for line in open(NEXT, encoding="utf-8"):
    m = re.match(r"^\s*-\s+\[ \]\s+([\w.\-]+)", line)
    if m:
        open_ids.add(m.group(1))

stale = sorted(done & open_ids)

# Reverse direction: an item PLAN.md still marks open ([ ] or [~]) but that
# is not mentioned anywhere in NEXT.md at all. This reads both files whole
# from disk (not the 40KB slice a chat read_file call gets), so it is
# reliable for PLAN.md's full size.
plan_open = set()
open_pattern = re.compile(r"^\[([ x~])\]\s+(?:\[LIVE\]\s+)?([\w.\-]+)")
for line in open(PLAN, encoding="utf-8"):
    m = open_pattern.match(line)
    if m and m.group(1) in (" ", "~"):
        plan_open.add(m.group(2))

next_text = open(NEXT, encoding="utf-8").read()
missing = sorted(
    pid for pid in plan_open
    if not re.search(r"\b" + re.escape(pid) + r"\b", next_text)
)

if stale or missing:
    if stale:
        print(f"FAIL: NEXT.md lists {len(stale)} done item(s) as open: {stale}")
    if missing:
        print(f"FAIL: NEXT.md omits {len(missing)} item(s) still open in PLAN.md: {missing}")
    sys.exit(1)
print(f"OK: {len(done)} done, none stale in NEXT.md; {len(plan_open)} open in PLAN.md, none missing from NEXT.md")
