#!/usr/bin/env python3
"""
Check: a vault user has no enabled ProductToggle.

lib/managed.ts says "The vault has no toggles and always returns
false — a vault chat can never gain a tool." That is a docstring.
This check queries the real database and makes it a rule.

A vault user is one with managedById IS NULL. A ProductToggle row for
such a user, with enabled = true, is a contradiction: hasProduct would
return true for a vault, which the code says can never happen. Zero is
the correct state. Any row is a breach.

REPORT_ONLY: when True, a breach is printed and the check exits 0, for
calibration. When False, a breach exits 1. A CHECK THAT CANNOT BE
EVALUATED (no DATABASE_URL, DB unreachable, non-numeric output) ALWAYS
EXITS 1 — an unevaluated invariant is not a passing invariant.

DATABASE_URL is read from the environment only. No file fallback.

Run:
    python3 checks/hasProduct_vault_false.py
"""
from __future__ import annotations

import os
import subprocess
import sys

REPORT_ONLY = True

SQL = """
SELECT count(*)
FROM "ProductToggle" pt
JOIN "User" u ON u.id = pt."userId"
WHERE u."managedById" IS NULL
  AND pt.enabled = true;
"""


def main() -> int:
    print("")
    print("Invariant: no vault user has an enabled ProductToggle")
    print("-" * 52)

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("  COULD NOT EVALUATE: DATABASE_URL is not set in the environment")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    r = subprocess.run(
        ["psql", db_url, "-tAc", SQL],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        first = (r.stderr.strip().splitlines() or ["(no stderr)"])[0]
        print(f"  COULD NOT EVALUATE: psql failed — {first}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    try:
        count = int((r.stdout or "0").strip() or "0")
    except ValueError:
        print(f"  COULD NOT EVALUATE: psql returned non-numeric output: {r.stdout!r}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    print(f"  vault users with an enabled toggle: {count}")
    print("")
    if count == 0:
        print("  PASS: the vault has no toggles, as lib/managed.ts says")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    print(f"  FAIL: {count} vault user(s) have an enabled ProductToggle")
    print("  hasProduct would return true for a vault. The docstring is false.")
    print("")
    print("SUMMARY: FAIL")
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
