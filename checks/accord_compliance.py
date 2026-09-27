#!/usr/bin/env python3
"""
Check: the Accord's encryption claims match the code.

Reads the <!-- encrypted-models: ... --> marker from the Accord's
Part III 3.1, reads every model with an encryptedData field from
prisma/schema.prisma, and fails if the two disagree.

The marker is the machine-readable form of the prose above it. The
prose is for humans; the marker is for this check. They state the
same fact. If the code gains or loses an encrypted model and the
marker is not updated, this check fails.

Found 27 Sept 2026: the Accord, the plan, and the marketing copy
all disagreed with the schema about which pills are encrypted. No
check existed, so the drift went unnoticed. This is that check.

Exit 0 if the lists agree, 1 otherwise.

Run:
    python3 checks/accord_compliance.py
"""

import re
import sys
from pathlib import Path

ACCORD = Path("/home/bosly_accord/bosly-1.0/docs/ACCORD.md")
SCHEMA = Path("/home/bosly_accord/bosly-1.0/prisma/schema.prisma")

MARKER_RE = re.compile(r"<!--\s*encrypted-models:\s*(.*?)\s*-->")
MODEL_RE = re.compile(r"^model\s+(\w+)\s*\{")


def accord_encrypted_models() -> set[str]:
    text = ACCORD.read_text(encoding="utf-8")
    m = MARKER_RE.search(text)
    if not m:
        raise SystemExit(
            "FAIL: no <!-- encrypted-models: ... --> marker found in "
            f"{ACCORD}. Cannot verify."
        )
    return {name.strip() for name in m.group(1).split(",") if name.strip()}


def schema_encrypted_models() -> set[str]:
    lines = SCHEMA.read_text(encoding="utf-8").splitlines()
    current = None
    found = set()
    for line in lines:
        s = line.strip()
        if s.startswith("//"):
            continue
        m = MODEL_RE.match(s)
        if m:
            current = m.group(1)
            continue
        if "encryptedData" in s and current:
            found.add(current)
    return found


def main() -> int:
    accord = accord_encrypted_models()
    schema = schema_encrypted_models()

    print("")
    print("Invariant: Accord encryption claims match the schema")
    print("----------------------------------------------------")
    print(f"  Accord says encrypted ({len(accord)}): {', '.join(sorted(accord))}")
    print(f"  Schema says encrypted ({len(schema)}): {', '.join(sorted(schema))}")
    print("")

    missing = schema - accord
    extra = accord - schema
    ok = not missing and not extra

    if missing:
        print("  FAIL: schema has encryptedData on these models, but the")
        print("        Accord marker does not list them:")
        for name in sorted(missing):
            print(f"          {name}")
        print("")
    if extra:
        print("  FAIL: the Accord marker lists these models as encrypted,")
        print("        but the schema has no encryptedData on them:")
        for name in sorted(extra):
            print(f"          {name}")
        print("")

    print(f"SUMMARY: {'PASS' if ok else 'FAIL'}")
    print("")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
