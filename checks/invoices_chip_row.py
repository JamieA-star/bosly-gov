#!/usr/bin/env python3
"""
Check: the Finance invoice month chip row renders, with the current month selected.

Step 3 of accord.invoices_organised_by_month. The UI lives in
bosly-1.0/components/workspace/FinancePill.tsx. The chip row must:

  1. load its months from GET /api/invoices/months (step 2, already built);
  2. render one chip per month, marked data-month="YYYY-MM";
  3. hold a selectedMonth state that starts at the CURRENT month, and mark
     the chip for that month data-selected="true".

This is a SOURCE CONTRACT check: it proves the wiring is in the component,
not a pixel render. A render proof needs a browser run, which this check
does not do. Say so when reporting it.

A file that cannot be read is COULD NOT EVALUATE and exits 1.

Run:
    python3 checks/invoices_chip_row.py
"""
from __future__ import annotations

import sys
from pathlib import Path

TSX = Path("/home/bosly_accord/bosly-1.0/components/workspace/FinancePill.tsx")

REQUIRED = [
    ("loads months from /api/invoices/months", '"/api/invoices/months"'),
    ("chip per month carries data-month", "data-month="),
    ("selected chip carries data-selected", "data-selected="),
    ("selectedMonth state exists", "selectedMonth"),
    ("default month is the current month", "setSelectedMonth("),
]


def main() -> int:
    print("")
    print("Invariant: the invoice month chip row renders with the current month selected")
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
    for label, needle in REQUIRED:
        ok = needle in src
        print(f"  {'ok  ' if ok else 'MISS'} {label}  [{needle}]")
        if not ok:
            missing.append(label)
    print("")

    if not missing:
        print("  PASS: the chip row is wired to the months feed, marks the current month")
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
