#!/usr/bin/env python3
"""append_plan_entry with an item_id lands the note on that item.

The founder's complaint: an update to accord.butler_knows_today landed
7,000 lines from the item it was about. With an item_id the note is
inserted after that item's block; the rest of the plan is unchanged.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

PLAN = Path("/home/bosly_accord/bosly-gov/PLAN.md")
BAK = PLAN.with_suffix(".md.bak-anchor-check")


def main() -> int:
    print("")
    print("Invariant: a note with an item id lands on that item")
    print("-" * 52)
    ok = True
    shutil.copy2(PLAN, BAK)

    try:
        from routers.tools import append_plan_entry
        # A real item, and a note that could only be found by its marker.
        marker = "anchor-check-marker-20261105"
        target = "gov.plan_updates_have_no_anchor"
        r = append_plan_entry(
            f"    {marker}\n",
            item_id=target,
        )
        wrote = r.get("ok")
        print(f"  the write is accepted: {wrote}")
        ok = ok and wrote

        text = PLAN.read_text(encoding="utf-8")
        found = marker in text
        print(f"  the marker is in the plan: {found}")
        ok = ok and found

        # It must be near the item, not at the end.
        ti = text.find(target)
        mi = text.find(marker)
        near = ti >= 0 and mi > ti and (mi - ti) < 4000
        print(f"  the marker is within 4000 chars of the item: {near}")
        ok = ok and near
    except TypeError:
        print("  FAIL: append_plan_entry does not take item_id yet")
        ok = False
    finally:
        shutil.copy2(BAK, PLAN)
        BAK.unlink(missing_ok=True)
        print("  plan restored")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
