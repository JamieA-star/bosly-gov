#!/usr/bin/env python3
"""
Check: the memory route's validator agrees with the EncryptedPayload type.

On 22 Oct a 400 invalid_encrypted_payload was found: encrypt() returns
version: 1 (a number, per lib/crypto/types.ts), but isEncryptedPayload
in app/api/chat/memory/route.ts checked typeof version === "string".
Every memory save failed, silently. The type is the contract; the
validator had drifted.

This reads the type's field types and the validator's typeof checks
and asserts they agree. The declaration may be `export interface` or
`export type`; both are accepted. Static, fast, no DB.

Run:
    python3 checks/encrypted_payload_shape.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TYPES = Path("/home/bosly_accord/bosly-1.0/lib/crypto/types.ts")
ROUTE = Path("/home/bosly_accord/bosly-1.0/app/api/chat/memory/route.ts")

TS_TO_TYPEOF = {"string": "string", "number": "number", "boolean": "boolean"}


def main() -> int:
    print("")
    print("Invariant: EncryptedPayload validator matches the type")
    print("-" * 52)

    if not TYPES.exists() or not ROUTE.exists():
        print("  COULD NOT EVALUATE: types.ts or the memory route is missing")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    tsrc = TYPES.read_text(encoding="utf-8")
    rsrc = ROUTE.read_text(encoding="utf-8")

    m = re.search(
        r"export\s+(?:type|interface)\s+EncryptedPayload\s*(?:=\s*)?\{([^}]*)\}",
        tsrc,
    )
    if not m:
        print("  COULD NOT EVALUATE: EncryptedPayload declaration not found")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    field_types: dict[str, str] = {}
    for line in m.group(1).splitlines():
        fm = re.match(r"\s*(\w+)\s*:\s*(\w+)", line)
        if fm:
            field_types[fm.group(1)] = fm.group(2)

    if not field_types:
        print("  COULD NOT EVALUATE: no fields parsed from EncryptedPayload")
        print("")
        print("SUMMARY: COULD NOT EVALUATE (hard fail)")
        print("")
        return 1

    findings = []
    for field, ts_type in field_types.items():
        expected = TS_TO_TYPEOF.get(ts_type)
        if not expected:
            continue
        vm = re.search(
            rf'typeof\s+p\.{re.escape(field)}\s*===\s*["\'](\w+)["\']',
            rsrc,
        )
        if not vm:
            findings.append(f"{field}: no typeof check in the validator")
            continue
        if vm.group(1) != expected:
            findings.append(
                f"{field}: type says {ts_type} (expects typeof '{expected}'), "
                f"validator checks '{vm.group(1)}'"
            )

    if findings:
        print(f"  FAIL: {len(findings)} disagreement(s)")
        for f in findings:
            print(f"    - {f}")
        print("")
        print("SUMMARY: FAIL")
        print("")
        return 1

    print(f"  PASS: {len(field_types)} field(s) agree between the type and the validator")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
