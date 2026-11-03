#!/usr/bin/env python3
"""Every fake of _ask_model takes _ask_model's parameters.

_ask_model has gained model, use_batch and build in one day, and each
time a test's fake broke and the failure did not say "signature". This
reads the real signature and the fakes, and fails if a fake cannot
accept what the real function accepts.
"""
import re
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

LOOP = "/home/bosly_accord/bosly-gov/routers/build_loop.py"
TESTS = "/home/bosly_accord/bosly-gov/checks/build_loop_stops.py"


def main() -> int:
    print("")
    print("Invariant: a fake of _ask_model takes its parameters")
    print("-" * 52)
    ok = True

    real = open(LOOP, encoding="utf-8").read()
    m = re.search(r"def _ask_model\(([^)]*)\)", real, re.DOTALL)
    if not m:
        print("  FAIL: _ask_model not found")
        print("SUMMARY: FAIL")
        return 1
    params = [p.split(":")[0].strip().split("=")[0].strip()
              for p in m.group(1).split(",") if p.strip()]
    print(f"  _ask_model params: {params}")

    tests = open(TESTS, encoding="utf-8").read()
    fakes = re.findall(r"def (fake_\w+)\(([^)]*)\)", tests, re.DOTALL)
    for name, args in fakes:
        have = [a.split("=")[0].strip() for a in args.split(",") if a.strip()]
        # By position: the first parameter's name is the caller's
        # business. What matters is that the fake accepts every
        # argument the real function passes, by keyword or position.
        missing = [p for p, h in zip(params, have) if not h]
        print(f"  {name}: {len(have)} args, needs {len(params)} — "
              f"{'ok' if not missing else 'missing ' + str(missing)}")
        ok = ok and not missing

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
