#!/usr/bin/env python3
"""
Check: every paid-pill API route enforces the Accord tier.

The paid pills are Inbox, Finance, Social, and Data health. Every
route under them must call a tier gate (requireAccord, or the
existing hasAccord/hasAccordAccess). On 30 Sept the checks were
scattered: the chat route checked, most pills did not, so the whole
app was usable for free.

This check fails, listing the ungated routes, until each is gated.
It is the guide for the enforcement sweep.

Exit 0 if every paid route is gated, 1 otherwise.

Run:
    python3 checks/paid_routes_gated.py
"""

import sys
from pathlib import Path

APP = Path("/home/bosly_accord/bosly-1.0/app/api")

PAID_PREFIXES = [
    APP / "inbox",
    APP / "finance",
    APP / "social",
    APP / "data-health",
]

# A route is gated if it mentions any of these.
GATE_MARKERS = ["requireAccord", "hasAccord", "hasAccordAccess", "subscriptionTier"]

# Routes that are exempt — webhooks, cron, and other non-user calls
# that cannot carry a session.
EXEMPT_SUBSTRINGS = ["/webhooks/", "/cron/", "/callback"]


def is_exempt(path: Path) -> bool:
    s = str(path).replace("\\", "/")
    return any(x in s for x in EXEMPT_SUBSTRINGS)


def main() -> int:
    routes = []
    for prefix in PAID_PREFIXES:
        if prefix.exists():
            routes.extend(sorted(prefix.rglob("route.ts")))

    print("")
    print("Invariant: every paid-pill route enforces the Accord tier")
    print("----------------------------------------------------")

    ungated = []
    for route in routes:
        if is_exempt(route):
            continue
        text = route.read_text(encoding="utf-8")
        gated = any(m in text for m in GATE_MARKERS)
        rel = str(route).replace(str(APP) + "/", "")
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
        f"({len(routes)} routes, {len(ungated)} ungated)"
    )
    print("")
    return 0 if not ungated else 1


if __name__ == "__main__":
    sys.exit(main())
