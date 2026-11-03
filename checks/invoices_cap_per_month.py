#!/usr/bin/env python3
"""
Check: GET /api/invoices?month=YYYY-MM returns the month's complete list,
and the response says whether the list is capped.

Step 6 of invoice-chips (accord.invoices_organised_by_month). The route
used to apply take: 50 to every query, so a month with more than 50
invoices was silently cut. The contract this check proves, read from the
route source (app/api/invoices/route.ts):

  1. A month query is not capped. The take: 50 limit applies only when
     there is no ?month=, written as  ...(month ? {} : { take: 50 }).
  2. There is no bare, unconditional take: 50 left in the GET handler.
  3. The response carries a `capped` field, so the list can say when
     the all-time list (no month) has been cut at 50.

A DATABASE_URL, when set, adds one fact to the output: the largest
month's row count. It does not decide pass or fail. The source contract
is what this check proves; the database says whether the cap could bite
on real data today.

Any missing contract point is a FAIL (exit 1). A route file that cannot
be read is COULD NOT EVALUATE (exit 1). An unevaluated invariant is not
a passing invariant.

Run:
    python3 checks/invoices_cap_per_month.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

ACCORD_ROOT = os.environ.get("ACCORD_ROOT", "/home/bosly_accord/bosly-1.0")
ROUTE = os.path.join(ACCORD_ROOT, "app", "api", "invoices", "route.ts")

MAX_MONTH_SQL = """
SELECT to_char(date_trunc('month', "issueDate"), 'YYYY-MM') || ' ' || count(*)
FROM "Invoice"
GROUP BY 1
ORDER BY count(*) DESC
LIMIT 1;
"""


def get_handler(src: str) -> str | None:
    m = re.search(r"export\s+async\s+function\s+GET\s*\(", src)
    if not m:
        return None
    nxt = re.search(r"export\s+async\s+function\s+POST\s*\(", src[m.end():])
    end = m.end() + nxt.start() if nxt else len(src)
    return src[m.start():end]


def main() -> int:
    print("")
    print("Invariant: a month's list is complete; the list says if it is capped")
    print("-" * 70)

    try:
        with open(ROUTE, encoding="utf-8") as f:
            src = f.read()
    except OSError as e:
        print(f"  COULD NOT EVALUATE: cannot read {ROUTE} — {e}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    handler = get_handler(src)
    if handler is None:
        print("  COULD NOT EVALUATE: no GET handler found in the route")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    points = []

    conditional = re.search(
        r"\.\.\.\s*\(\s*month\s*\?\s*\{\s*\}\s*:\s*\{\s*take:\s*50\s*\}\s*\)",
        handler,
    )
    points.append((
        "a month query is not capped (take: 50 only when there is no month)",
        conditional is not None,
    ))

    bare_take = re.search(r"^\s*take:\s*50\s*,?\s*$", handler, re.MULTILINE)
    points.append((
        "no bare, unconditional take: 50 in the GET handler",
        bare_take is None,
    ))

    points.append((
        "the response carries a `capped` field",
        re.search(r"NextResponse\.json\(\s*\{[^}]*\bcapped\b[^}]*\}\s*\)", handler) is not None,
    ))

    for label, ok in points:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")

    if os.environ.get("DATABASE_URL", "").strip():
        try:
            r = subprocess.run(
                ["psql", os.environ["DATABASE_URL"], "-tAc", MAX_MONTH_SQL],
                capture_output=True, text=True,
            )
            if r.returncode == 0 and r.stdout.strip():
                print(f"  fact: largest month in the database is {r.stdout.strip()} rows")
            else:
                print("  fact: largest month could not be read from the database (not a verdict)")
        except OSError:
            print("  fact: psql not available (not a verdict)")
    else:
        print("  fact: DATABASE_URL not set; the month size on real data was not read (not a verdict)")

    print("")
    if all(ok for _, ok in points):
        print("  PASS: a month's list is complete and the list reports when it is capped")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    print("  FAIL: the route does not yet meet the contract")
    print("")
    print("SUMMARY: FAIL")
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
