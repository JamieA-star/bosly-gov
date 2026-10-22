#!/usr/bin/env python3
"""
Check: the learned-answer cache stores no sensitive question.

Ladder rung A's rule: the write path refuses a question that looks
like it carries a value — a digit, a currency/percent token, two
consecutive capitalised words (a client name), or a health-value term
with a digit. The code has that denylist; this check proves the STORED
DATA obeys it.

It reads every answer-cache/*.json and scans each stored question. A
digit or a value token in a stored question is a breach: the denylist
failed, or something wrote past it.

REPORT_ONLY: when True, breaches print and the check exits 0, for
calibration. When False, a breach exits 1. A CHECK THAT CANNOT BE
EVALUATED (the cache dir is missing, a file is unreadable) is not a
pass: a missing dir is OK (no cache yet), but an unreadable file is a
hard fail.

Run:
    python3 checks/answer_cache_no_sensitive.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPORT_ONLY = True

CACHE_DIR = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/answer-cache")

# The same refuse conditions as the route's looksSensitive, applied to
# stored data. Conservative: refusal is the safe direction.
SENSITIVE = [
    (re.compile(r"\d"), "digit (amount, date, account)"),
    (re.compile(r"[£$%@]"), "currency/percent/contact token"),
    (re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"), "two capitalised words (client name)"),
]


def main() -> int:
    print("")
    print("Invariant: the learned-answer cache stores no sensitive question")
    print("-" * 52)

    if not CACHE_DIR.exists():
        print("  PASS: no cache dir yet (nothing stored, nothing to breach)")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    files = sorted(CACHE_DIR.glob("*.json"))
    findings = []
    unreadable = []

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            unreadable.append((f.name, str(e)))
            continue
        entries = data.get("entries") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            continue
        for i, e in enumerate(entries):
            q = (e or {}).get("question", "")
            if not isinstance(q, str):
                continue
            for pattern, label in SENSITIVE:
                if pattern.search(q):
                    findings.append((f.name, i, label, q[:100]))
                    break

    if unreadable:
        print(f"  FAIL: {len(unreadable)} cache file(s) could not be read")
        for name, err in unreadable:
            print(f"    {name}: {err}")
        print("")
        print("SUMMARY: FAIL (could not evaluate a file)")
        print("")
        return 0 if REPORT_ONLY else 1

    if findings:
        print(f"  FAIL: {len(findings)} stored question(s) look sensitive")
        for name, i, label, q in findings:
            print(f"    {name} [{i}]: {label} — {q}")
        print("")
        print("  The denylist failed, or something wrote past it. B (the")
        print("  extractor) is the proof; until then, this is the watch.")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    print(f"  PASS: {len(files)} cache file(s), no stored question carries a value")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
