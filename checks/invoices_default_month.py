#!/usr/bin/env python3
"""
Check: opening Finance shows the current month.

Step 4 of accord.invoices_organised_by_month. The UI lives in
bosly-1.0/components/workspace/FinancePill.tsx. Opening Finance must:

  1. set selectedMonth to the CURRENT month on mount (not all-time);
  2. scope the invoice list to selectedMonth, so the list shown is that
     month's invoices, not the flat list capped at 50;
  3. keep the month filter server-side: the list request carries
     ?month=, which the API filters on issueDate (step 1).

This is a SOURCE CONTRACT check: it proves the wiring is in the component,
not a pixel render. A render proof needs a browser run, which this check
does not do. Say so when reporting it.

A file that cannot be read is COULD NOT EVALUATE and exits 1.

Run:
    python3 checks/invoices_default_month.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TSX = Path("/home/bosly_accord/bosly-1.0/components/workspace/FinancePill.tsx")

# (label, regex) — each must match somewhere in the component source.
REQUIRED = [
    (
        "mount sets selectedMonth to the current month",
        r"setSelectedMonth\(\s*thisMonth\s*\)",
    ),
    (
        "current month is derived from today's date",
        r"getFullYear\(\)\s*\+\s*\"-\"\s*\+\s*String\(\s*now\.getMonth\(\)\s*\+\s*1\s*\)\.padStart\(2,\s*\"0\"\)",
    ),
    (
        "invoice list request is scoped by ?month=",
        r"/api/invoices\?month=",
    ),
    (
        "invoice list request uses selectedMonth",
        r"month=\$\{\s*selectedMonth\s*\}",
    ),
]


def main() -> int:
    print("")
    print("Invariant: opening Finance shows the current month")
    print("-" * 78)

    try:
        src = TSX.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  COULD NOT EVALUATE: cannot read {TSX} — {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    missing = []
    for label, pattern in REQUIRED:
        ok = re.search(pattern, src) is not None
        print(f"  {'ok  ' if ok else 'MISS'} {label}")
        if not ok:
            missing.append(label)
    print("")

    if not missing:
        print("  PASS: Finance opens on the current month and the list is scoped to it")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    print(f"  FAIL: {len(missing)} of {len(REQUIRED)} contract points missing")
    print("")
    print("SUMMARY: FAIL")
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
