#!/usr/bin/env python3
"""
Check: the founder service token is never in the repo.

The token is the Executive's key to Accord.founder. It lives in .env
on both sides, never in the source. A token in the repo is a token
leaked.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPOS = [
    Path("/home/bosly_accord/bosly-1.0"),
    Path("/home/bosly_accord/bosly-gov"),
    Path("/home/bosly_accord/bosly-keep"),
]

PATTERN = re.compile(r"FOUNDER_SERVICE_TOKEN\s*=\s*[\"\']?[A-Za-z0-9_\-]{20,}")


def main() -> int:
    print("")
    print("Invariant: the founder service token is not in the repo")
    print("-" * 52)

    findings = []
    for repo in REPOS:
        if not repo.exists():
            continue
        for f in repo.rglob("*"):
            if not f.is_file():
                continue
            if any(p in f.parts for p in (".git", "node_modules", ".next", "dist")):
                continue
            if f.suffix in (".png", ".jpg", ".ico", ".woff", ".woff2", ".lock"):
                continue
            if f.name.startswith(".env"):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in PATTERN.finditer(text):
                findings.append((str(f), m.group(0)[:60]))

    if findings:
        print(f"  FAIL: {len(findings)} literal token(s) in the repo")
        for path, text in findings:
            print(f"    {path}: {text}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    print("  PASS: no literal FOUNDER_SERVICE_TOKEN in the repos (only .env)")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
