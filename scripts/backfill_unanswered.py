#!/usr/bin/env python3
"""Backfill unknown-intents.jsonl into the pile, idempotent.

Stable thing_id from sha1(ts+userId+message) so a re-run updates rather
than inserts. Run it twice; the count must not change.
"""
import hashlib, json, sys
sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers.things import save_thing

SRC = "/home/bosly_accord/bosly-gov/data/unknown-intents.jsonl"
n = 0
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    tid = "thing-bf-" + hashlib.sha1(
        (r["ts"] + r["userId"] + r["message"]).encode()
    ).hexdigest()[:16]
    res = save_thing(
        kind="unanswered",
        title=r["message"][:120],
        body=r["message"],
        status="active",
        tags=f"userId:{r['userId']}",
        thing_id=tid,
    )
    if not res.get("ok"):
        print("FAIL", tid, res.get("error")); sys.exit(1)
    n += 1
print("backfilled", n)
