#!/usr/bin/env python3
"""
Check: the Executive proxy is live in the running build.

The deploy trap, made a check. A route can typecheck, be in the
source, and be absent from the running build — twice on 21 Oct a route
existed and the deployed server didn't have it. This curls the running
app and asserts the route answers, not 404.

A 303 (auth middleware redirect), 401, or 403 means the route is live
and gated. A 404 means it is not in the running build — the trap. A
000 means nothing is listening on 3100 — the app is down, which is
also a failure, not a skip.

The app is expected on http://localhost:3100 (pm2-managed,
deploy-safe.sh). If the port changes, change it here.

REPORT_ONLY: when True, a 404 or 000 prints and the check exits 0, for
calibration. When False, it exits 1. A CHECK THAT CANNOT BE EVALUATED
(curl missing, unexpected error) ALWAYS EXITS 1.

Run:
    python3 checks/executive_proxy_live.py
"""
from __future__ import annotations

import subprocess
import sys

REPORT_ONLY = True

URL = "http://localhost:3100/api/executive/proxy"
BODY = '{"messages":[{"role":"user","content":"health probe"}]}'

# A pass is the route answering and being gated. 404 is the trap.
PASS_CODES = {"303", "401", "403"}


def main() -> int:
    print("")
    print("Invariant: the Executive proxy is live in the running build")
    print("-" * 52)

    try:
        r = subprocess.run(
            [
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "-X", "POST", URL,
                "-H", "Content-Type: application/json",
                "-d", BODY,
                "--max-time", "10",
            ],
            capture_output=True, text=True, timeout=15,
        )
    except Exception as e:
        print(f"  COULD NOT EVALUATE: curl failed — {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    code = (r.stdout or "").strip() or "000"

    if code in PASS_CODES:
        print(f"  PASS: route answered HTTP {code} (live, gated)")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    if code == "404":
        print("  FAIL: HTTP 404 — the route is not in the running build")
        print("  This is the deploy trap: source has it, the build doesn't.")
        print("")
        print("SUMMARY: FAIL (deploy trap)")
        print("")
        return 0 if REPORT_ONLY else 1

    if code == "000":
        print("  FAIL: nothing listening on 3100 — the app is down")
        print("  pm2 list | grep bosly; check the logs.")
        print("")
        print("SUMMARY: FAIL (app down)")
        print("")
        return 0 if REPORT_ONLY else 1

    print(f"  FAIL: unexpected HTTP {code}")
    print("")
    print("SUMMARY: FAIL (unexpected)")
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
