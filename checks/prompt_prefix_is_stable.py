#!/usr/bin/env python3
"""The system prompt is a stable cache prefix; the state rides on the message.

A prompt cache is a prefix match. The date, the ecosystem and the repos
used to live in the system prompt, and each changed on a schedule, so
every call re-billed the whole 15KB. They are out now. This check fails
if anything that changes gets back into the prefix.

What it proves, and what it does not: the prefix is stable and the date
is gone; the context block CARRIES the state. It does not assert that a
utime changes the context block — a utime is not a state change, and the
ecosystem summary is a function of the plan, not of its clock. That was
the first version's bug.

Run:
    python3 checks/prompt_prefix_is_stable.py
"""
import os
import sys
import time

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

PLAN = "/home/bosly_accord/bosly-gov/PLAN.md"


def main() -> int:
    print("")
    print("Invariant: the system prompt is a stable cache prefix")
    print("-" * 52)
    ok = True

    try:
        from routers.tool_loop import _read_prompt, _context_block
    except Exception as e:
        print(f"  FAIL: cannot import the prompt functions: {e}")
        print("SUMMARY: FAIL")
        return 1

    a = _read_prompt()
    b = _read_prompt()
    same = a == b
    print(f"  two reads are identical: {same}")
    ok = ok and same

    no_date = "Today is" not in a
    print(f"  the date is not in the system prompt: {no_date}")
    ok = ok and no_date

    if os.path.exists(PLAN):
        p1 = _read_prompt()
        time.sleep(0.01)
        os.utime(PLAN, None)
        p2 = _read_prompt()
        stable = p1 == p2
        print(f"  prompt unchanged after a PLAN.md touch: {stable}")
        ok = ok and stable
    else:
        print("  NOTE: PLAN.md not found; skipped the touch test")

    c = _context_block()
    has_date = "Today is" in c
    has_eco = "=== THE ECOSYSTEM" in c
    has_repo = "=== THE REPOS" in c
    print(f"  context carries the date: {has_date}")
    print(f"  context carries the ecosystem: {has_eco}")
    print(f"  context carries the repos: {has_repo}")
    ok = ok and has_date and has_eco and has_repo

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
