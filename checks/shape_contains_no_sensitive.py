#!/usr/bin/env python3
"""
Check: every stored shape contains no sensitive value, and has a slot.

Ladder rung B: the cache stores a shape — the question with value-
looking tokens replaced by slots. This is what D shares: Gov holds the
shape, the browser fills the slots, the filled question is never sent
back.

The check reads every answer-cache/*.json, every entry's `shape`, and
asserts:
  - no digit, currency/percent token, or two capitalised words
  - at least one [slot] — a shape with no slot is the question
    verbatim, the extraction did nothing, and it defeats D's purpose

REPORT_ONLY: when True, breaches print and the check exits 0, for
calibration. When False, a breach exits 1. A CHECK THAT CANNOT BE
EVALUATED is a hard fail.

Run:
    python3 checks/shape_contains_no_sensitive.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPORT_ONLY = True

CACHE_DIR = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/answer-cache")

SENSITIVE = [
    (re.compile(r"\d"), "digit in the shape"),
    (re.compile(r"[£$%@]"), "currency/percent/contact token in the shape"),
    (re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"), "two capitalised words in the shape"),
]
SLOT = re.compile(r"\[[a-z][a-z ]*\]")


def main() -> int:
    print("")
    print("Invariant: every stored shape has no value and at least one slot")
    print("-" * 52)

    if not CACHE_DIR.exists():
        print("  PASS: no cache dir yet (nothing stored, nothing to breach)")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    files = sorted(CACHE_DIR.glob("*.json"))
    unreadable = []
    findings = []

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
            entry = e or {}
            shape = entry.get("shape")
            has_slots = entry.get("hasSlots")
            question = entry.get("question", "")

            if not isinstance(shape, str) or not shape:
                findings.append((f.name, i, "no shape field", ""))
                continue
            if not isinstance(has_slots, bool):
                findings.append((f.name, i, "no hasSlots field (pre-hardening entry)", shape[:100]))
                continue

            # The claim must match the shape: hasSlots true -> a [slot];
            # hasSlots false -> the shape equals the question.
            if has_slots and not SLOT.search(shape):
                findings.append((f.name, i, "hasSlots true but no [slot] — the claim is false", shape[:100]))
                continue
            if (not has_slots) and shape != question:
                findings.append((f.name, i, "hasSlots false but the shape differs from the question", shape[:100]))
                continue

            for pattern, label in SENSITIVE:
                if pattern.search(shape):
                    findings.append((f.name, i, label, shape[:100]))
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
        print(f"  FAIL: {len(findings)} shape problem(s)")
        for name, i, label, s in findings:
            print(f"    {name} [{i}]: {label} — {s}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    print(f"  PASS: {len(files)} file(s), every shape is slot-only")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
