#!/usr/bin/env python3
"""
Check: the Executive proxy has no path to the database.

The promise: the LLM never sees a user's sensitive business data. The
structural guarantee: /api/executive/proxy relays a prompt the browser
built; it does not read the database. This check fails if the proxy
route file imports prisma directly, or calls a Prisma model query.

A transitive import through requireAccord is fine — the gate reads the
user's tier, which is not content. The check looks at the proxy route
file itself, not its imports.

Run:
    python3 checks/executive_proxy_no_db.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROUTE = Path("/home/bosly_accord/bosly-1.0/app/api/executive/proxy/route.ts")

# Direct prisma import, or a direct model query, in the proxy file.
PATTERNS = [
    (re.compile(r'^\s*import\s+.*\bprisma\b.*from\s+["\']@/lib/(db|prisma)["\']', re.M),
     "direct prisma import"),
    (re.compile(r'\bprisma\.\w+\.(findMany|findUnique|findFirst|create|update|delete|query)\b'),
     "direct prisma model query"),
]

def main() -> int:
    print("")
    print("Invariant: Executive proxy has no database path")
    print("-" * 52)

    if not ROUTE.exists():
        print(f"  FAIL: proxy route not found: {ROUTE}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    src = ROUTE.read_text(encoding="utf-8")
    failures = []
    for pattern, label in PATTERNS:
        for m in pattern.finditer(src):
            line = src[:m.start()].count("\n") + 1
            failures.append((line, label, m.group(0)[:80]))

    if failures:
        print(f"  FAIL: {len(failures)} database path(s) found in the proxy")
        for line, label, text in failures:
            print(f"    line {line}: {label} — {text}")
        print("")
        print("  The proxy relays; it does not read. Data-minimisation")
        print("  happens in the browser and in the client-side tools.")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    print("  PASS: no direct database import or query in the proxy")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
