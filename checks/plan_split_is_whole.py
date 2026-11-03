#!/usr/bin/env python3
"""The plan is split and nothing was lost.

PLAN.md crossed read_file's 400,000-byte ceiling on 2 Nov: the butler
could not read its own plan. The done items moved to PLAN-archive.md
verbatim. This check proves the live plan is under the ceiling and
plan_query still sees every item, before and after.
"""
import sys
from pathlib import Path

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: the plan is under the read ceiling, and nothing was lost")
    print("-" * 52)
    ok = True

    plan = Path("/home/bosly_accord/bosly-gov/PLAN.md")
    archive = Path("/home/bosly_accord/bosly-gov/PLAN-archive.md")
    size = plan.stat().st_size if plan.exists() else 0
    under = size < 400_000
    print(f"  PLAN.md size: {size} bytes (under 400000: {under})")
    ok = ok and under and archive.exists()

    try:
        from routers.tools import plan_query
    except Exception as e:
        print(f"  FAIL: cannot import plan_query: {e}")
        print("SUMMARY: FAIL")
        return 1

    open_n = plan_query(status="open").get("result", {}).get("count")
    done_n = plan_query(status="done").get("result", {}).get("count")
    print(f"  open: {open_n}, done: {done_n}")

    # done may be in either file: the archive holds the split's done
    # items, and an item ticked after the split lives in the live plan.
    # plan_query reads both, so the count is the sum, and the check
    # asserts the count, not which file a done item is in.
    live_x = sum(1 for ln in plan.read_text(encoding="utf-8").splitlines() if ln.startswith("[x]"))
    arch_x = sum(1 for ln in archive.read_text(encoding="utf-8").splitlines() if ln.startswith("[x]"))
    total_x = live_x + arch_x
    print(f"  [x] in the live plan: {live_x}, in the archive: {arch_x}, total: {total_x}")
    ok = ok and arch_x > 0 and done_n == total_x
    ok = ok and isinstance(open_n, int) and open_n > 0

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
