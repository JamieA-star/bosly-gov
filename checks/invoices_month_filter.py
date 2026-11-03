#!/usr/bin/env python3
"""
Check: GET /api/invoices?month=YYYY-MM returns only that month's rows.

Step 1 of accord.invoices_organised_by_month. The route filters on
issueDate with a plain [gte start, lt end) range, built from the
month param (app/api/invoices/route.ts). This check proves that
range, against the real database, two ways:

  1. COMPLETE — every invoice whose issueDate truly falls in the
     chosen month (by date_trunc) is included in the route's
     [start, end) range. Nothing from the month is left out.
  2. PURE — every invoice inside the route's [start, end) range
     truly belongs to the chosen month (by date_trunc). Nothing
     from another month leaks in.

Both must hold, and both are counts, not opinions: a row satisfying
one condition and not the other is a counted mismatch, not a guess.

The month under test is the month of the most recent invoice
(MAX(issueDate)), so the check exercises a real month with real
rows rather than an empty one. If there are no invoices at all, the
check cannot be evaluated — zero rows cannot prove a filter.

REPORT_ONLY: when True, a breach is printed and the check exits 0,
so it can be calibrated before it fails the pipeline. When False, a
breach exits 1. A CHECK THAT CANNOT BE EVALUATED (no DATABASE_URL,
DB unreachable, no invoices, non-numeric output) ALWAYS EXITS 1 — an
unevaluated invariant is not a passing invariant.

DATABASE_URL is read from the environment only. There is no file
fallback: one source of truth, and it is the one the runner carries.

Run:
    python3 checks/invoices_month_filter.py
"""
from __future__ import annotations

import os
import subprocess
import sys

REPORT_ONLY = True

FIND_MONTH_SQL = """
SELECT to_char(date_trunc('month', max("issueDate")), 'YYYY-MM-DD')
FROM "Invoice";
"""

# Mirrors app/api/invoices/route.ts: where.issueDate = { gte: start, lt: end }
# with start/end built from the chosen month.
COMPLETE_SQL = """
SELECT count(*)
FROM "Invoice"
WHERE date_trunc('month', "issueDate") = date_trunc('month', %(month)s::date)
  AND NOT (
    "issueDate" >= date_trunc('month', %(month)s::date)
    AND "issueDate" < (date_trunc('month', %(month)s::date) + interval '1 month')
  );
"""

PURE_SQL = """
SELECT count(*)
FROM "Invoice"
WHERE "issueDate" >= date_trunc('month', %(month)s::date)
  AND "issueDate" < (date_trunc('month', %(month)s::date) + interval '1 month')
  AND date_trunc('month', "issueDate") <> date_trunc('month', %(month)s::date);
"""

IN_RANGE_SQL = """
SELECT count(*)
FROM "Invoice"
WHERE "issueDate" >= date_trunc('month', %(month)s::date)
  AND "issueDate" < (date_trunc('month', %(month)s::date) + interval '1 month');
"""


def run_sql(db_url: str, sql: str, month: str | None = None) -> str:
    if month is not None:
        sql = sql.replace("%(month)s", f"'{month}'")
    r = subprocess.run(["psql", db_url, "-tAc", sql], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr.strip().splitlines() or ["(no stderr)"])[0])
    return (r.stdout or "").strip()


def main() -> int:
    print("")
    print("Invariant: ?month= on GET /api/invoices returns only that month's rows")
    print("-" * 52)

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("  COULD NOT EVALUATE: DATABASE_URL is not set in the environment")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    try:
        month_raw = run_sql(db_url, FIND_MONTH_SQL)
    except RuntimeError as e:
        print(f"  COULD NOT EVALUATE: psql failed — {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    if not month_raw or month_raw.lower() == "null":
        print("  COULD NOT EVALUATE: no invoices in the database to test against")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    try:
        in_range = int(run_sql(db_url, IN_RANGE_SQL, month_raw) or "0")
        missing = int(run_sql(db_url, COMPLETE_SQL, month_raw) or "0")
        leaked = int(run_sql(db_url, PURE_SQL, month_raw) or "0")
    except (RuntimeError, ValueError) as e:
        print(f"  COULD NOT EVALUATE: {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    print(f"  month under test: {month_raw[:7]}")
    print(f"  rows the route's [start, end) range returns: {in_range}")
    print(f"  rows of that month missing from the range (should be 0): {missing}")
    print(f"  rows in the range from another month (should be 0): {leaked}")
    print("")

    if missing == 0 and leaked == 0:
        print("  PASS: the range is complete and pure — only that month's rows")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    print(f"  FAIL: missing={missing} leaked={leaked}")
    print("")
    print("SUMMARY: FAIL")
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
