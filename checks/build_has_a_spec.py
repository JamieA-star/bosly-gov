#!/usr/bin/env python3
"""A build for the night has a spec: goal, decisions, permissions, hatch.

An overnight build cannot ask a question, so the answers are written
first. A build with no spec is a build that will park at 3am with a
question nobody reads.
"""
import shutil
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

NAME = "check-build-spec"
DIR = f"/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds/{NAME}"


def main() -> int:
    print("")
    print("Invariant: a build for the night has a spec")
    print("-" * 52)
    ok = True
    shutil.rmtree(DIR, ignore_errors=True)

    from routers import build
    r = build.write_spec(NAME, "a test goal",
                         ["decision one"], ["may commit"], "park and write why")
    written = r.get("ok")
    print(f"  a spec writes: {written}")
    ok = ok and written
    print(f"  has_spec sees it: {build.has_spec(NAME)}")
    ok = ok and build.has_spec(NAME)

    r2 = build.write_spec(NAME, "", [], [], "")
    refused = not r2.get("ok")
    print(f"  an empty spec is refused: {refused}")
    ok = ok and refused

    shutil.rmtree(DIR, ignore_errors=True)
    print("  cleaned up")
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
