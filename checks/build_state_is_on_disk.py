#!/usr/bin/env python3
"""A build's state is on disk, and it survives the model.

The model cannot carry state between two calls, so a build that runs for
hours must live on disk: a spec, a step list, and a state file that says
where it got to, what it finished, and what it needs. Three endings —
done, stuck, needs_founder — and the third is what makes unattended
work safe.

This check creates a throwaway build, ticks a step, parks it, reads it
back, and removes it. No model call.
"""
import shutil
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

NAME = "check-build-state"
DIR = f"/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds/{NAME}"


def main() -> int:
    print("")
    print("Invariant: a build's state is on disk and it survives")
    print("-" * 52)
    ok = True
    shutil.rmtree(DIR, ignore_errors=True)

    try:
        from routers import build
    except Exception as e:
        print(f"  FAIL: cannot import build: {e}")
        print("SUMMARY: FAIL")
        return 1

    r = build.new_build(NAME, "test", [{"title": "a", "check": "x"}, {"title": "b", "check": "y"}])
    created = r.get("ok")
    print(f"  created: {created}")
    ok = ok and created

    again = build.new_build(NAME, "test", [{"title": "a", "check": "x"}])
    refused = not again.get("ok")
    print(f"  a second create is refused: {refused}")
    ok = ok and refused

    build.tick_step(NAME, 0, evidence="done with evidence")
    st = build.load_build(NAME).get("result", {}).get("state", {})
    ticked = st.get("current") == 1 and len(st.get("done", [])) == 1
    print(f"  a step ticks with evidence: {ticked}")
    ok = ok and ticked

    build.park_for_founder(NAME, "Which way?", ["A", "B"])
    st = build.load_build(NAME).get("result", {}).get("state", {})
    parked = st.get("status") == "needs_founder" and st.get("question") == "Which way?"
    print(f"  a build parks with its question: {parked}")
    ok = ok and parked

    shutil.rmtree(DIR, ignore_errors=True)
    print("  cleaned up")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
