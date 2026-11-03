#!/usr/bin/env python3
"""A parked question names the step that is current now.

Tonight a build was parked on step 3, the state advanced to step 4, and
the app kept asking the step-3 question. A question about a finished
step is a lie: it asks the founder to decide something already decided.
park_for_founder stamps step_at_park; this check compares it to current.
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

BUILDS = "/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds"


def main() -> int:
    print("")
    print("Invariant: a parked question is about the current step")
    print("-" * 52)
    ok = True
    from pathlib import Path
    import json

    base = Path(BUILDS)
    if not base.exists():
        print("  no builds yet")
        print("SUMMARY: PASS")
        return 0

    for d in sorted(base.iterdir()):
        sf = d / "state.json"
        if not sf.exists():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if st.get("status") != "needs_founder":
            continue
        at = st.get("step_at_park")
        cur = st.get("current", 0)
        if at is None:
            print(f"  {d.name}: parked with no step_at_park — backfill it")
            ok = False
        elif at != cur:
            print(f"  {d.name}: parked on step {at}, current is {cur} — stale")
            ok = False
        else:
            print(f"  {d.name}: parked on step {cur}, current — good")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
