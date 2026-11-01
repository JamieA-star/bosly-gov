#!/usr/bin/env python3
"""Check: a question asked through the UI actually fills the cache.

The cache has two halves. The loop CHECKING it is proven by the drawer
(Accord's own chat, 3100). The UI STORING to it is the other half: the
UI is served by Gov on 3102 and POSTs to /gov/api/executive/cache, a
route Gov does not have. On 1 Nov that POST returned 404, so the UI's
half never filled. This check asks a question with a unique marker,
then asserts the marker landed in the cache file.

It fails today by design. REPORT_ONLY keeps it from reddening the fast
tier until the CORS/proxy fix lands; flip it to False in the same
commit as that fix.

Run:
    python3 checks/answer_cache_fills.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPORT_ONLY = True

UI_URL = "http://localhost:3102/gov/api/executive/cache"
CACHE_DIR = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/answer-cache")
MARK = f"answer-cache-fills-probe-{int(time.time())}"


def count_entries() -> int:
    if not CACHE_DIR.exists():
        return 0
    n = 0
    for f in CACHE_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        entries = d.get("entries") if isinstance(d, dict) else None
        if isinstance(entries, list):
            n += len(entries)
    return n


def main() -> int:
    print("")
    print("Invariant: a question asked through the UI fills the cache")
    print("-" * 52)

    before = count_entries()
    print(f"  entries before: {before}")

    status = None
    try:
        req = urllib.request.Request(
            UI_URL,
            data=json.dumps({"question": MARK, "answer": "probe"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        print(f"  FAIL: could not reach {UI_URL}: {e}")
        print("")
        print("SUMMARY: " + ("REPORT-ONLY" if REPORT_ONLY else "FAIL"))
        print("")
        return 0 if REPORT_ONLY else 1

    print(f"  POST {UI_URL} -> {status}")

    after = count_entries()
    print(f"  entries after:  {after}")

    ok = status == 200 and after > before
    if ok:
        print("  PASS: the UI's POST stored; the entry count went up")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    label = "NOTE" if REPORT_ONLY else "FAIL"
    print(f"  {label}: status={status}, delta={after - before}")
    print("")
    print("SUMMARY: " + ("REPORT-ONLY" if REPORT_ONLY else "FAIL"))
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
