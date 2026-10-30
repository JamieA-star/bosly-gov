#!/usr/bin/env python3
"""The pile must hold the unanswered questions when the jsonl has rows."""
import json, sys
sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers.things import find_things

SRC = "/home/bosly_accord/bosly-gov/data/unknown-intents.jsonl"
try:
    rows = [l for l in open(SRC, encoding="utf-8") if l.strip()]
except FileNotFoundError:
    print("SKIP: no jsonl"); sys.exit(0)
if not rows:
    print("SKIP: jsonl empty"); sys.exit(0)
n = find_things(kind="unanswered", status="active", limit=500)["result"]["count"]
print(f"jsonl rows: {len(rows)}, pile active: {n}")
if n < len(rows):
    print(f"FAIL: pile has {n}, jsonl has {len(rows)}"); sys.exit(1)
sys.exit(0)
