#!/usr/bin/env python3
"""Backfill unknown-intents.jsonl into the pile, idempotent by tag.

save_thing(thing_id=...) only updates an existing row, so the sha1 is a
tag, not an id: lookup before write. Run twice; the count must not
change.
"""
import hashlib, json, sys
sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers.things import save_thing, find_things

SRC = "/home/bosly_accord/bosly-gov/data/unknown-intents.jsonl"
created = skipped = 0
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    h = hashlib.sha1((r["ts"] + r["userId"] + r["message"]).encode()).hexdigest()[:16]
    tag = f"backfill:{h}"
    if find_things(query=tag, limit=1)["result"]["things"]:
        skipped += 1
        continue
    res = save_thing(
        kind="unanswered",
        title=r["message"][:120],
        body=r["message"],
        status="active",
        tags=f"userId:{r['userId']} {tag}",
    )
    if not res.get("ok"):
        print("FAIL", h, res.get("error")); sys.exit(1)
    created += 1
print(f"created {created}, skipped {skipped}")
