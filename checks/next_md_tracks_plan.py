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
if stale:
    print(f"FAIL: NEXT.md lists {len(stale)} done item(s) as open: {stale}")
    sys.exit(1)
print(f"OK: {len(done)} done, none stale in NEXT.md")
