#!/usr/bin/env python3
"""
Check: the Executive proxy calls hasProduct with the literal "executive".

The guard must be specific. hasProduct(uid, "executive") pins the
product; hasProduct(uid, someVariable) can be pointed at a different
product without anyone noticing, which silently weakens the gate.
The literal string is the contract.

Report-only at first (calibration rule). Flip REPORT_ONLY when trusted.

Run:
    python3 checks/executive_proxy_managed_only.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPORT_ONLY = True

ROUTE = Path("/home/bosly_accord/bosly-1.0/app/api/executive/proxy/route.ts")

# hasProduct( <anything>, "executive" )  — literal, double or single quotes
LITERAL = re.compile(r'hasProduct\s*\(\s*[^,]+,\s*(["\'])executive\1\s*\)')

# Any hasProduct call at all, so a call with a non-literal argument is caught
ANY_CALL = re.compile(r'hasProduct\s*\(')


def main() -> int:
    print("")
    print("Invariant: the Executive proxy gates on the literal 'executive'")
    print("-" * 52)

    if not ROUTE.exists():
        print(f"  FAIL: proxy route not found: {ROUTE}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    src = ROUTE.read_text(encoding="utf-8")
    findings = []

    any_calls = [m.start() for m in ANY_CALL.finditer(src)]
    literals = [m.start() for m in LITERAL.finditer(src)]

    if not any_calls:
        findings.append("hasProduct is not called at all")
    elif not literals:
        findings.append('hasProduct is called but not with the literal "executive"')

    if findings:
        print(f"  FAIL: {len(findings)} problem(s)")
        for f in findings:
            print(f"    - {f}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    print('  PASS: hasProduct is called with the literal "executive"')
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
