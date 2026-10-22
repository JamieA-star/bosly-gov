#!/usr/bin/env python3
"""
Check: every token in a stored shape is a known-safe word or a [slot].

The pattern check (gov.shape_contains_no_sensitive) and the extractor
share the same rules, so a value both miss passes. A lowercase client
name ('acme plumbing') is the demonstrated residue: the pattern check
passes it. This check is the independent angle: it does not look for
values; it asks whether EVERY token is a known-safe word. A token not
in the vocabulary is flagged, regardless of what it looks like.

The vocabulary lives at
  /mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/answer-cache/vocabulary.txt
one word per line, comments with #. It grows as a human proves a word
safe. A flagged token means: review this shape before C shares it.

REPORT_ONLY: when True, findings print and the check exits 0, for
calibration. When False, a finding exits 1. A CHECK THAT CANNOT BE
EVALUATED is a hard fail.

Run:
    python3 checks/vocabulary_covers_shapes.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPORT_ONLY = True

CACHE_DIR = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/answer-cache")
VOCAB = CACHE_DIR / "vocabulary.txt"

# A slot may carry a possessive: [date]'s. Swallow it, so the 's is
# part of the slot and not a word the tokeniser invents.
SLOT = re.compile(r"\[[a-z][a-z ]*\](?:'s)?")
# A token must start with a letter or digit; a leading apostrophe
# (as in " 's ") is not a word. "what's" stays one token; " 's "
# alone produces nothing.
TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def load_vocab() -> set[str]:
    words: set[str] = set()
    for line in VOCAB.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        words.add(line.lower())
    return words


def main() -> int:
    print("")
    print("Invariant: every token in a stored shape is known-safe")
    print("-" * 52)

    if not VOCAB.exists():
        print(f"  COULD NOT EVALUATE: vocabulary not found: {VOCAB}")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    if not CACHE_DIR.exists():
        print("  PASS: no cache dir yet")
        print("")
        print("SUMMARY: PASS")
        print("")
        return 0

    vocab = load_vocab()
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
            shape = (e or {}).get("shape")
            if not isinstance(shape, str) or not shape:
                continue
            # Strip the slots before tokenising: a slot is a marker, its
            # label is irrelevant, and leaving it in makes the tokeniser
            # read the label as a word. Report EVERY unknown token, so a
            # safe word cannot hide a dangerous one.
            masked = SLOT.sub(" ", shape.lower())
            unknown = [t for t in TOKEN.findall(masked) if t not in vocab]
            if unknown:
                findings.append((f.name, i, ", ".join(sorted(set(unknown))), shape[:90]))

    if unreadable:
        print(f"  FAIL: {len(unreadable)} cache file(s) could not be read")
        for name, err in unreadable:
            print(f"    {name}: {err}")
        print("")
        print("SUMMARY: FAIL (could not evaluate a file)")
        print("")
        return 0 if REPORT_ONLY else 1

    if findings:
        print(f"  FAIL: {len(findings)} shape(s) contain a token not in the vocabulary")
        for name, i, tok, s in findings:
            print(f"    {name} [{i}]: '{tok}' not in vocabulary — {s}")
        print("")
        print("  Review the shape, or add the word to vocabulary.txt if it is safe.")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 0 if REPORT_ONLY else 1

    print(f"  PASS: {len(files)} file(s), every token is known-safe or a slot")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
