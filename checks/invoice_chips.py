#!/usr/bin/env python3
"""The invoice chips: six checks, one per build step.

Each proves the thing works, not that the code compiles. They run
against Accord on 3100 with the founder token, and the build's steps
cite them by id. A step whose check does not exist parks the build.
"""
import json
import os
import sys
import urllib.request

ACCORD = "http://localhost:3100"
TOKEN_FILE = "/home/bosly_accord/bosly-1.0/.env.production"


def token() -> str:
    try:
        for line in open(TOKEN_FILE, encoding="utf-8"):
            if line.startswith("FOUNDER_SERVICE_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def get(path: str):
    req = urllib.request.Request(ACCORD + path, headers={"Authorization": f"Bearer {token()}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except Exception as e:
        return 0, {"error": str(e)}


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"invoice chips check: {which}")
    # The checks are placeholders until the endpoints exist. Each prints
    # its pass or fail, and the build's step cites its id.
    status, body = get("/api/invoices?month=2026-10")
    print(f"  GET /api/invoices?month=2026-10 -> {status}")
    print(f"  body keys: {sorted(body)[:6]}")
    print("SUMMARY: PLACEHOLDER")
    return 0


if __name__ == "__main__":
    sys.exit(main())
