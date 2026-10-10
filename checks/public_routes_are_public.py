#!/usr/bin/env python3
"""
Check: known-critical public routes are in the public list.

The list lives in lib/public-routes.ts, imported by both the
middleware (server gate) and VaultProvider (client redirect). It
used to live inline in middleware.ts. On 10 Oct it moved, and this
check was updated to follow — a check that reads a file the list
has left is reading nothing.

Routes that must work without a session (webhooks, uploads,
callbacks, cron) have to be listed, or they are redirected to
/signin. On 30 Sept this broke the logo upload, the branding
upload, and the Stripe webhook — the last silently, so a real
payment succeeded and the tier never set.

This check asserts a declared set of critical routes is present in
the public list. A regression guard: it catches a route being
removed or the list being rewritten, not a brand-new route being
forgotten.

Exit 0 if all present, 1 otherwise.

Run:
    python3 checks/public_routes_are_public.py
"""

import re
import sys
from pathlib import Path

PUBLIC_ROUTES = Path("/home/bosly_accord/bosly-1.0/lib/public-routes.ts")

REQUIRED = [
    "/api/billing/webhook",
    "/api/cron",
    "/api/auth",
    "/uploads",
]


def quoted_strings(text: str) -> set[str]:
    # Match within each line — a stray quote in the file would
    # otherwise let [^"]+ span multiple lines and swallow routes.
    out: set[str] = set()
    for line in text.splitlines():
        out.update(re.findall(r'"([^"]+)"', line))
    return out


def main() -> int:
    if not PUBLIC_ROUTES.exists():
        print(f"FAIL: {PUBLIC_ROUTES} not found")
        return 1

    text = PUBLIC_ROUTES.read_text(encoding="utf-8")
    quoted = quoted_strings(text)

    print("")
    print("Invariant: known public routes are in the public list")
    print("----------------------------------------------------")

    missing = []
    for route in REQUIRED:
        present = route in quoted
        print(f"  {'OK' if present else 'MISSING'}  {route}")
        if not present:
            missing.append(route)

    print("")
    if missing:
        print("  FAIL: these must be reachable without a session but are")
        print("        not in the middleware's public list:")
        for m in missing:
            print(f"          {m}")
        print("")
    print(f"SUMMARY: {'PASS' if not missing else 'FAIL'}")
    print("")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
