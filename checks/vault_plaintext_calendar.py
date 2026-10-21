#!/usr/bin/env python3
"""
Check: no vault user's calendar row carries a plaintext title.

The vault promise (PRODUCT DESIGN block, "ACCORD VAULT") says the
developer is blind. That promise is only true if the server never
reads plaintext. The calendar table stores both a plaintext title and
an encryptedData blob; the list route selects the plaintext title with
no mode check. Today there are no vault users, so nothing leaks — but
the structure does not enforce it, and nothing watches it.

This check answers one question against the real database: does any
user with managedById IS NULL have a CalendarEvent with a non-empty
title? Zero is the correct state. Any row is a breach.

A vault row WITH ciphertext and WITHOUT a plaintext title is the
correct state and is not counted.

REPORT_ONLY: when True, a breach is printed and the check exits 0,
so it can be calibrated before it fails the pipeline. When False, a
breach exits 1. A CHECK THAT CANNOT BE EVALUATED (no DATABASE_URL,
DB unreachable, non-numeric output) ALWAYS EXITS 1 — an unevaluated
invariant is not a passing invariant.

DATABASE_URL is read from the environment only. There is no file
fallback: one source of truth, and it is the one the runner carries.

Run:
    python3 checks/vault_plaintext_calendar.py
"""
from __future__ import annotations

import os
import subprocess
import sys

REPORT_ONLY = True

SQL = """
SELECT count(*)
FROM "CalendarEvent" e
JOIN "User" u ON u.id = e."userId"
WHERE u."managedById" IS NULL
  AND e.title IS NOT NULL
  AND e.title <> '';
"""


def main() -> int:
    print("")
    print("Invariant: no vault plaintext in calendar")
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
        first_line = (r.stderr.strip().splitlines() or ["(no stderr)"])[0]
        print(f"  COULD NOT EVALUATE: psql failed — {first_line}")
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

    print(f"  vault calendar rows with a plaintext title: {count}")
    print("")
    if count == 0:
        print("  PASS: every vault calendar row is ciphertext-only")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    print(f"  FAIL: {count} vault calendar row(s) carry a plaintext title")
    print("  The vault promise says the developer is blind. This is a breach.")
    print("")
    print("SUMMARY: FAIL")
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
