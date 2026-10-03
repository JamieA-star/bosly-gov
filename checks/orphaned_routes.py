#!/usr/bin/env python3
"""
Check: every API route has a caller, or is explicitly server-only.

A route with no caller is dead — the AI routes, the iCloud calendar
routes, the password-reset API all sat unreachable. Nothing caught
them; every build passed. This check lists them.

A route is "reached" if its path appears anywhere in the app or
components, outside its own file. Server-only routes (cron, webhooks,
NextAuth, health) are allowlisted.

Report-only at first: it prints orphans and exits 0. Once calibrated,
remove the report_only flag to make it fail the pipeline.

Run:
    python3 checks/orphaned_routes.py
"""

import re
import sys
from pathlib import Path

APP = Path("/home/bosly_accord/bosly-1.0/app")
SCAN = [APP, Path("/home/bosly_accord/bosly-1.0/components"),
        Path("/home/bosly_accord/bosly-1.0/lib")]

# Routes reached only from outside the repo: cron, webhooks, OAuth
# callbacks, health probes. Add here with a reason.
SERVER_ONLY = [
    "api/cron",             # run by cron
    "api/billing/webhook",  # called by Stripe
    "api/health",           # called by monitoring
    "api/auth",             # OAuth callbacks and NextAuth
    "api/inbox/webhooks",   # called by email providers
    "api/internal",         # called by cron scripts
    "api/uploads",          # served to the browser directly
    "api/version",          # called by the update banner
]

REPORT_ONLY = True


def route_path(route_file: Path) -> str:
    rel = route_file.relative_to(APP)
    parts = list(rel.parts[:-1])
    parts = [p for p in parts if not (p.startswith("(") and p.endswith(")"))]
    return "/" + "/".join(parts)


def is_server_only(path: str) -> bool:
    p = path.lstrip("/")
    return any(p.startswith(s) for s in SERVER_ONLY)


def all_source_files() -> list[Path]:
    out = []
    for root in SCAN:
        if root.exists():
            out.extend(root.rglob("*.ts"))
            out.extend(root.rglob("*.tsx"))
    return out


def main() -> int:
    routes = sorted(APP.rglob("route.ts"))
    sources = all_source_files()

    # Pre-read every source file once.
    blobs = []
    for f in sources:
        try:
            blobs.append((f, f.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            pass

    print("")
    print("Invariant: every API route has a caller or is server-only")
    print("--------------------------------------------------------")
    print(f"  routes: {len(routes)}   source files: {len(blobs)}")

    orphans = []
    for route in routes:
        path = route_path(route)
        if is_server_only(path):
            continue

        # A path with [id] is a dynamic segment; callers use a real id.
        # Match on the static prefix before the first bracket.
        static = re.split(r"\[", path)[0].rstrip("/")
        if not static:
            static = path

        found = False
        for f, text in blobs:
            if f == route:
                continue
            if static in text:
                found = True
                break
        if not found:
            orphans.append(path)

    print("")
    if orphans:
        print(f"  {len(orphans)} route(s) with no caller:")
        for o in orphans:
            print(f"    {o}")
    else:
        print("  OK: every route has a caller")

    print("")
    verdict = "REPORT" if REPORT_ONLY else ("PASS" if not orphans else "FAIL")
    print(f"SUMMARY: {verdict} ({len(routes)} routes, {len(orphans)} orphaned)")
    print("")
    return 0 if (REPORT_ONLY or not orphans) else 1


if __name__ == "__main__":
    sys.exit(main())
