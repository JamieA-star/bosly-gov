#!/usr/bin/env python3
"""The Suggested block is behind a chip, not always on screen.

Step 5 of accord.invoices_organised_by_month. The block used to render
whenever suggestions existed; the spec says one click away. This reads
the component and asserts: a Suggested chip exists, a showSuggested
flag gates the block, and the block is behind the flag.
"""
import re
import sys

COMP = "/home/bosly_accord/bosly-1.0/components/workspace/FinancePill.tsx"


def main() -> int:
    print("")
    print("Invariant: the Suggested block is behind a chip")
    print("-" * 52)
    ok = True
    try:
        text = open(COMP, encoding="utf-8").read()
    except Exception as e:
        print(f"  FAIL: cannot read {COMP}: {e}")
        print("SUMMARY: FAIL")
        return 1

    has_flag = "showSuggested" in text
    print(f"  a showSuggested flag exists: {has_flag}")
    ok = ok and has_flag

    has_chip = bool(re.search(r"Suggested(\s*\(|\s*\{)", text)) and "button" in text
    print(f"  a Suggested chip (button) exists: {has_chip}")
    ok = ok and has_chip

    # The block must be gated: showSuggested && near the suggestions render.
    gated = bool(re.search(r"showSuggested\s*&&", text))
    print(f"  the block is gated on showSuggested: {gated}")
    ok = ok and gated

    # The chip must set the flag.
    toggles = bool(re.search(r"setShowSuggested\s*\(", text))
    print(f"  the chip toggles the flag: {toggles}")
    ok = ok and toggles

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
