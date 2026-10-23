#!/usr/bin/env python3
"""
Check: the Custodian door is gated to the founder.

Accord.founder is the door to the Executive Custodian, which reaches
the Copilot's tools. The gate is isFounder: the route returns 403 when
false, and the chat only calls the door when the mode says founder.

Static check on the founder route.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROUTE = Path("/home/bosly_accord/bosly-1.0/app/api/executive/founder/route.ts")


def main() -> int:
    print("")
    print("Invariant: the Custodian door is gated to the founder")
    print("-" * 52)

    if not ROUTE.exists():
        print(f"  FAIL: founder route not found: {ROUTE}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    src = ROUTE.read_text(encoding="utf-8")
    findings = []
    if "isFounder(" not in src:
        findings.append("the route does not call isFounder")
    if "founder_only" not in src:
        findings.append("the route does not return founder_only for a non-founder")
    if "/api/chat" not in src and "3102" not in src:
        findings.append("the route does not call the Copilot")

    if findings:
        print(f"  FAIL: {len(findings)} finding(s)")
        for f in findings:
            print(f"    - {f}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    print("  PASS: the door calls isFounder, refuses, and reaches the Copilot")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
