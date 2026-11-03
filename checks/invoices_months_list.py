#!/usr/bin/env python3
"""
Check: GET /api/invoices/months lists YYYY-MM with counts.

Step 2 of accord.invoices_organised_by_month. The route
(app/api/invoices/months/route.ts) groups a user's invoices by
calendar month with:

    SELECT to_char(date_trunc('month', "issueDate"), 'YYYY-MM') AS month,
           count(*) AS count
    FROM "Invoice"
    WHERE "userId" = <uid>
GROUP BY to_char(date_trunc('month', "issueDate"), 'YYYY-MM')
    ORDER BY 1 DESC

This check proves that grouping against the real database, two ways,
for a real user (the one with the most invoices, so the check
exercises real buckets rather than an empty or single-row case):

  1. MIRROR — the route's own query, run directly.
  2. INDEPENDENT — the same grouping computed a different way
     (EXTRACT(YEAR/MONTH) + lpad, not date_trunc/to_char), so a bug
     shared between the route and a copy-pasted check would not
     hide behind agreement with itself.

Both must produce the identical (month, count) rows, in the same
order, and every count must sum to that user's total invoice count
(COMPLETE — nothing dropped) with every row's month matching
YYYY-MM (well-formed).

REPORT_ONLY: when True, a breach is printed and the check exits 0,
so it can be calibrated before it fails the pipeline. When False, a
breach exits 1. A CHECK THAT CANNOT BE EVALUATED (no DATABASE_URL,
DB unreachable, no invoices, malformed output) ALWAYS EXITS 1 — an
unevaluated invariant is not a passing invariant.

DATABASE_URL is read from the environment only. There is no file
fallback: one source of truth, and it is the one the runner carries.

Run:
    python3 checks/invoices_months_list.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

REPORT_ONLY = True

FIND_USER_SQL = """
SELECT "userId"
FROM "Invoice"
GROUP BY "userId"
ORDER BY count(*) DESC
LIMIT 1;
"""

TOTAL_SQL = """
SELECT count(*)
FROM "Invoice"
WHERE "userId" = '%(uid)s';
"""

# Mirrors app/api/invoices/months/route.ts exactly.
MIRROR_SQL = """
SELECT to_char(date_trunc('month', "issueDate"), 'YYYY-MM') || '|' || count(*)
FROM "Invoice"
WHERE "userId" = '%(uid)s'
GROUP BY to_char(date_trunc('month', "issueDate"), 'YYYY-MM')
ORDER BY 1 DESC;
"""

# Computed a different way: EXTRACT + lpad, not date_trunc/to_char.
INDEPENDENT_SQL = """
SELECT (lpad(EXTRACT(YEAR FROM "issueDate")::text, 4, '0') || '-' ||
        lpad(EXTRACT(MONTH FROM "issueDate")::text, 2, '0')) || '|' || count(*)
FROM "Invoice"
WHERE "userId" = '%(uid)s'
GROUP BY (lpad(EXTRACT(YEAR FROM "issueDate")::text, 4, '0') || '-' ||
          lpad(EXTRACT(MONTH FROM "issueDate")::text, 2, '0'))
ORDER BY 1 DESC;
"""

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def run_sql(db_url: str, sql: str) -> str:
    r = subprocess.run(["psql", db_url, "-tAc", sql], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr.strip().splitlines() or ["(no stderr)"])[0])
    return (r.stdout or "").strip()


def parse_rows(raw: str) -> list[tuple[str, int]]:
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        month, _, cnt = line.partition("|")
        rows.append((month, int(cnt)))
    return rows


def main() -> int:
    print("")
    print("Invariant: GET /api/invoices/months lists YYYY-MM with counts")
    print("-" * 52)

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("  COULD NOT EVALUATE: DATABASE_URL is not set in the environment")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    try:
        uid = run_sql(db_url, FIND_USER_SQL)
    except RuntimeError as e:
        print(f"  COULD NOT EVALUATE: psql failed — {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    if not uid:
        print("  COULD NOT EVALUATE: no invoices in the database to test against")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    try:
        total = int(run_sql(db_url, TOTAL_SQL % {"uid": uid}) or "0")
        mirror_raw = run_sql(db_url, MIRROR_SQL % {"uid": uid})
        independent_raw = run_sql(db_url, INDEPENDENT_SQL % {"uid": uid})
    except (RuntimeError, ValueError) as e:
        print(f"  COULD NOT EVALUATE: {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    try:
        mirror_rows = parse_rows(mirror_raw)
        independent_rows = parse_rows(independent_raw)
    except ValueError as e:
        print(f"  COULD NOT EVALUATE: malformed row output — {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    mirror_sum = sum(c for _, c in mirror_rows)
    bad_format = [m for m, _ in mirror_rows if not MONTH_RE.match(m)]
    agree = mirror_rows == independent_rows

    print(f"  user under test: {uid}")
    print(f"  total invoices for that user: {total}")
    print(f"  months route would return: {len(mirror_rows)}")
    print(f"  sum of counts across months (should equal total): {mirror_sum}")
    print(f"  months with a bad YYYY-MM format (should be 0): {len(bad_format)}")
    print(f"  mirror query == independent query: {agree}")
    print("")

    if mirror_sum == total and not bad_format and agree:
        print("  PASS: the grouping is complete, well-formed, and agrees two ways")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    print(
        f"  FAIL: sum_mismatch={mirror_sum != total} "
        f"bad_format={bad_format} agree={agree}"
    )
    print("")
    print("SUMMARY: FAIL")
    print("")
    return 0 if REPORT_ONLY else 1


if __name__ == "__main__":
    sys.exit(main())
