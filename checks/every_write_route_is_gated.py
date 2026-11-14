#!/usr/bin/env python3
"""
gov.accord_every_write_route_is_gated

Every route under a paid pill that writes calls requireAccord.

Found 14 Nov: calendar, contacts and invoices had no tier check at all,
so a lapsed user could add, edit, delete and send for free while finance
refused them. Twelve write routes gained the gate; contacts/[id] was
missed by the first sweep and found by hand. This check is that sweep,
in the tier.

Read routes stay open on purpose: the workspace renders and the paywall
appears at the action, not at the door.
"""
import os
import re
import sys
from pathlib import Path

ACCORD = Path(os.environ.get("ACCORD_ROOT", "/home/bosly_accord/bosly-1.0"))
PILLS = ["app/api/calendar", "app/api/contacts", "app/api/invoices"]

WRITE = re.compile(r"export\s+async\s+function\s+(POST|PATCH|PUT|DELETE)\b")
GATED = re.compile(r"requireAccord\s*\(")

failures = []
for pill in PILLS:
    root = ACCORD / pill
    if not root.exists():
        continue
    for p in root.rglob("route.ts"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if WRITE.search(text) and not GATED.search(text):
            failures.append(str(p.relative_to(ACCORD)))

if failures:
    print("FAIL gov.accord_every_write_route_is_gated")
    for f in failures:
        print(f"  {f} writes without requireAccord")
    sys.exit(1)

print("PASS gov.accord_every_write_route_is_gated")
