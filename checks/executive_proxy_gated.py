#!/usr/bin/env python3
"""
Check: the Executive proxy is gated by requireAccord AND hasProduct.

The proxy is a relay that calls a paid model on a user's behalf. It
must be gated twice: requireAccord (the paid tier) and
hasProduct(uid, "executive") (the toggle). Both gates must appear
before the model call. If either is removed or reordered after the
fetch, the route is under-gated.

Report-only at first (calibration rule): prints findings and exits 0.
Flip REPORT_ONLY to False once trusted.

Run:
    python3 checks/executive_proxy_gated.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPORT_ONLY = True

ROUTE = Path("/home/bosly_accord/bosly-1.0/app/api/executive/proxy/route.ts")


def main() -> int:
    print("")
    print("Invariant: Executive proxy is gated twice")
    print("-" * 52)

    if not ROUTE.exists():
        print(f"  FAIL: proxy route not found: {ROUTE}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    src = ROUTE.read_text(encoding="utf-8")
    findings = []

    accord = [m.start() for m in re.finditer(r"requireAccord\s*\(", src)]
    product = [m.start() for m in re.finditer(r"hasProduct\s*\(", src)]
    model = [m.start() for m in re.finditer(r'fetch\s*\(\s*["\']https://api\.anthropic\.com', src)]

    if not accord:
        findings.append("requireAccord is not called")
    if not product:
        findings.append("hasProduct is not called")
    if not model:
        findings.append("no model call found (route may have changed shape)")

    if accord and product and model:
        first_model = model[0]
        if accord[0] > first_model:
            findings.append("requireAccord is called after the model call")
        if product[0] > first_model:
            findings.append("hasProduct is called after the model call")

    if findings:
        print(f"  FAIL: {len(findings)} gating problem(s)")
        for f in findings:
            print(f"    - {f}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    print("  PASS: requireAccord and hasProduct both precede the model call")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
