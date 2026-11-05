#!/usr/bin/env python3
"""A tick has evidence, and a step ticks once.

The first build ticked step 0 twice with empty evidence: the check
passed without printing, and the loop ticked a step it had already
ticked. A tick with no evidence is a claim, not a proof; a step that
ticks twice is the loop losing its place.
"""
import shutil
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

NAME = "check-vacuous-tick"
DIR = f"/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds/{NAME}"


def main() -> int:
    print("")
    print("Invariant: a tick has evidence, and a step ticks once")
    print("-" * 52)
    ok = True
    shutil.rmtree(DIR, ignore_errors=True)

    from routers import build
    # new_build refuses a spec without the base: write_spec first.
    build.write_spec(NAME, goal="probe: a tick has evidence",
                     decisions=["probe decision"], permissions=["probe permission"],
                     escape_hatch="park")
    build.new_build(NAME, "t", [{"title": "a", "check": "x"}])

    r = build.tick_step(NAME, 0, evidence="")
    refused_empty = not r.get("ok")
    print(f"  a tick with no evidence is refused: {refused_empty}")
    ok = ok and refused_empty

    r = build.tick_step(NAME, 0, evidence="PASS: the check printed a proof")
    ticked = r.get("ok")
    print(f"  a tick with evidence is accepted: {ticked}")
    ok = ok and ticked

    r = build.tick_step(NAME, 0, evidence="PASS again")
    refused_repeat = not r.get("ok")
    print(f"  a second tick on the same step is refused: {refused_repeat}")
    ok = ok and refused_repeat

    shutil.rmtree(DIR, ignore_errors=True)
    print("  cleaned up")
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
