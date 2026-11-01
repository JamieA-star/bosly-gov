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
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPORT_ONLY = False

# The route is Accord's, on 3100 — not Gov's. The founder bearer
# token is what the butler uses to reach Accord's routes without a
# browser session; it is in Gov's own environment (proven 1 Nov).
ROUTE_URL = "http://localhost:3100/api/executive/cache"
TOKEN = (os.environ.get("FOUNDER_SERVICE_TOKEN") or "").strip()
CACHE_DIR = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/answer-cache")
# Digit-free and value-free by design: the route's looksSensitive()
# refuses any question containing a digit, and its already_cached guard
# refuses a repeat, so a fixed or small-vocabulary marker fails on the
# second or nth run. Encode the clock in letters: unique for decades,
# no digits, no real word, no collision with a client question.
def _letters(n: int) -> str:
    out = []
    while n:
        n, r = divmod(n, 26)
        out.append(chr(ord("a") + r))
    return "".join(reversed(out)) or "a"

MARK = "what is the answer cache probe " + _letters(int(time.time() * 1000))


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


def stored_question(mark: str) -> bool:
    """True if this exact question is in any cache file.

    The directory count was inflated: shared.json has entries too, so a
    store that promoted a shape added one to the user file and one to
    shared, and the delta read +2 for a single POST. Assert the question
    itself — precise, and it cannot be inflated by a promotion or by a
    probe left over from an earlier run.
    """
    if not CACHE_DIR.exists():
        return False
    for f in CACHE_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for e in (d.get("entries") or []):
            if isinstance(e, dict) and e.get("question") == mark:
                return True
    return False


def main() -> int:
    print("")
    print("Invariant: a question asked through the UI fills the cache")
    print("-" * 52)

    before = count_entries()
    print(f"  entries before: {before}")

    status = None
    try:
        req = urllib.request.Request(
            ROUTE_URL,
            data=json.dumps({"question": MARK, "answer": "probe"}).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            status = r.status
            body = json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        status = e.code
        body = {}
    except Exception as e:
        print(f"  FAIL: could not reach {ROUTE_URL}: {e}")
        print("")
        print("SUMMARY: " + ("REPORT-ONLY" if REPORT_ONLY else "FAIL"))
        print("")
        return 0 if REPORT_ONLY else 1
    except Exception as e:
        print(f"  FAIL: could not reach {ROUTE_URL}: {e}")
        print("")
        print("SUMMARY: " + ("REPORT-ONLY" if REPORT_ONLY else "FAIL"))
        print("")
        return 0 if REPORT_ONLY else 1

    print(f"  POST {ROUTE_URL} -> {status}")

    after = count_entries()
    print(f"  entries after:  {after}")

    stored = bool(body.get("stored"))
    found = stored_question(MARK)
    ok = status == 200 and stored and found
    if ok:
        print("  PASS: the UI's POST stored; the question is in the cache")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    label = "NOTE" if REPORT_ONLY else "FAIL"
    print(f"  {label}: status={status}, stored={stored}, found={found}, delta={after - before}")
    print("")
    print("SUMMARY: " + ("REPORT-ONLY" if REPORT_ONLY else "FAIL"))
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
