#!/usr/bin/env python3
"""
Check: every paid (Accord) route enforces the tier.

The free/paid boundary is drawn around features, not pills, and it
cuts across prefixes. Finance is the clear case: manual invoicing
(free, the lead magnet) shares the prefix with transactions (paid).
So this check names routes explicitly — a prefix scan cannot tell
them apart.

The inbox is NOT here. It is count-gated, not feature-gated: free
for one connected account, up to five on Accord, enforced in
/api/email-connection. See accord.free_paid_boundary in PLAN.md.

A route is gated if it calls requireAccord (or the older
hasAccord / hasAccordAccess / subscriptionTier read).

Exit 0 if every listed route is gated, 1 otherwise.

Run:
    python3 checks/paid_routes_gated.py
"""

import sys
from pathlib import Path

APP = Path("/home/bosly_accord/bosly-1.0/app/api")

# Routes that must enforce the Accord tier. Explicit, because the
# boundary cuts across prefixes. Add a route here when it becomes
# paid; remove it when it stops being paid.
PAID_ROUTES = [
    "finance/categories",
    "finance/ftx",
    "finance/import-transactions",
    "finance/parse-statement",
    "finance/transactions",
    "finance/tax-pack",
    "social/generate-captions",
    "social/generate-ideas",
    "data-health/check",
    "data-health/identities",
    "chat",
]

# A route is gated if it mentions any of these.
GATE_MARKERS = ["requireAccord", "hasAccord", "hasAccordAccess", "subscriptionTier"]


def main() -> int:
    print("")
    print("Invariant: every paid route enforces the Accord tier")
    print("----------------------------------------------------")

    ungated = []
    for rel in PAID_ROUTES:
        route = APP / rel / "route.ts"
        if not route.exists():
            print(f"  MISSING  {rel}/route.ts")
            ungated.append(rel + " (missing)")
            continue
        text = route.read_text(encoding="utf-8")
        gated = any(m in text for m in GATE_MARKERS)
        print(f"  {'OK' if gated else 'UNGATED'}  {rel}")
        if not gated:
            ungated.append(rel)

    print("")
    if ungated:
        print(f"  FAIL: {len(ungated)} paid route(s) have no tier gate:")
        for r in ungated:
            print(f"        {r}")
        print("")
    print(
        f"SUMMARY: {'PASS' if not ungated else 'FAIL'} "
        f"({len(PAID_ROUTES)} routes, {len(ungated)} ungated)"
    )
    print("")
    return 0 if not ungated else 1


if __name__ == "__main__":
    sys.exit(main())
