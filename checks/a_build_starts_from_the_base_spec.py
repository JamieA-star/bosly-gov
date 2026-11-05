"""A build starts from the base spec.

Produces a spec through write_spec \u2014 not a file read off disk, so it
asserts the writer's output, not yesterday's spec \u2014 and checks that
every standing decision appears in it. Cleans up its probe build.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from routers import build

PROBE = "__base_spec_check__"

def main() -> int:
    d = build._dir(PROBE)
    if d.exists():
        print(f"FAIL: probe build {PROBE} already exists at {d}")
        print("       a previous run did not clean up; remove it and re-run")
        return 1

    try:
        base = build._load_base_spec()
    except FileNotFoundError as e:
        print(f"FAIL: base spec missing: {e}")
        return 1
    if not base:
        print("FAIL: specs/base.md has no '- ' decision lines")
        return 1

    r = build.write_spec(
        PROBE,
        goal="probe: assert the base is inherited",
        decisions=["probe decision"],
        permissions=["probe permission"],
        escape_hatch="park",
    )
    if not r.get("ok"):
        print(f"FAIL: write_spec refused: {r.get('error')}")
        return 1

    spec_path = d / "spec.md"
    if not spec_path.exists():
        print(f"FAIL: write_spec reported ok but {spec_path} is missing")
        return 1
    spec = spec_path.read_text(encoding="utf-8")

    failed = 0
    for line in base:
        if line in spec:
            print(f"ok      {line}")
        else:
            print(f"MISSING {line}")
            failed += 1

    if failed:
        print(f"\nFAIL: {failed} of {len(base)} standing decisions missing")
        return 1
    print(f"\nPASS: all {len(base)} standing decisions in the produced spec")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        d = build._dir(PROBE)
        if d.exists():
            shutil.rmtree(d)
            print(f"cleaned up {d}")
