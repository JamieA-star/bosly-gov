#!/usr/bin/env python3
"""append_plan_entry refuses an unknown item id, and names the ids near it."""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: an unknown item id is refused, not appended")
    print("-" * 52)
    ok = True

    from routers.tools import append_plan_entry
    r = append_plan_entry("    a note that should not land\n",
                          item_id="zzz.no.such.item.20261105")
    refused = not r.get("ok")
    print(f"  an unknown id is refused: {refused}")
    ok = ok and refused

    near = r.get("near") or []
    print(f"  it names ids near the search: {bool(near)}")
    ok = ok and bool(near)

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
