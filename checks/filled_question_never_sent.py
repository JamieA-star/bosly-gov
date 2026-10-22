#!/usr/bin/env python3
"""
Check: the filled question is never sent to Gov.

Rung D's hard rule. The browser fills a shared shape's slots with its
own data; the filled question goes nowhere but the screen. The proxy
call must carry the SHAPE (sharedHint) and the user's message, never a
filled template.

Static check on components/chat/ChatDrawer.tsx: take the slice from the
proxy fetch to its closing, and assert it does not reference a filled
template.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CLIENT = Path("/home/bosly_accord/bosly-1.0/components/chat/ChatDrawer.tsx")


def main() -> int:
    print("")
    print("Invariant: the filled question is never sent to Gov")
    print("-" * 52)

    if not CLIENT.exists():
        print(f"  COULD NOT EVALUATE: client not found: {CLIENT}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    src = CLIENT.read_text(encoding="utf-8")

    start = src.find('fetch("/api/executive/proxy"')
    if start == -1:
        start = src.find("fetch('/api/executive/proxy'")
    if start == -1:
        print("  COULD NOT EVALUATE: proxy fetch not found")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    end = src.find("});", start)
    if end == -1:
        print("  COULD NOT EVALUATE: proxy fetch body end not found")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    body = src[start:end + 3]
    findings = []
    for bad in ("filled", "filledQuestion", "assembled"):
        if re.search(r"\b" + bad + r"\b", body):
            findings.append(f"proxy body references '{bad}'")
    if re.search(r"\$\{[^}]*\.question", body):
        findings.append("proxy body interpolates a .question field")

    if findings:
        print(f"  FAIL: {len(findings)} finding(s)")
        for f in findings:
            print(f"    - {f}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    print("  PASS: the proxy body carries the shape, not a filled template")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
