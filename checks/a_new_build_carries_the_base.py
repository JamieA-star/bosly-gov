"""A build created by new_build carries the base spec.

Shape 2: new_build is the door, the gate in run_build is the backstop.
Cases 1-3 are red before the build, green after. Case 4 is green today
and must stay green: the base rule must not swallow the restart rule.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routers import build

NAME = "__new_build_check__"
D = build._dir(NAME)
STEPS = [{"title": "a", "check": "x", "check_id": "gov.memory_schema"}]

def main() -> int:
    ok = True

    # 1. No spec -> refused, names write_spec.
    shutil.rmtree(D, ignore_errors=True)
    r = build.new_build(NAME, "a short spec", STEPS)
    good = (not r.get("ok")) and ("write_spec" in str(r.get("error", "")))
    print(f"  no spec refused, names write_spec: {good}  ({r.get('error')})")
    ok = ok and good

    # 2. Base-less spec -> refused the same way.
    shutil.rmtree(D, ignore_errors=True)
    D.mkdir(parents=True, exist_ok=True)
    (D / "spec.md").write_text("# Build spec\n\n## The goal\nprobe\n", encoding="utf-8")
    r = build.new_build(NAME, "a short spec", STEPS)
    good = (not r.get("ok")) and ("base" in str(r.get("error", "")).lower())
    print(f"  base-less spec refused: {good}  ({r.get('error')})")
    ok = ok and good

    # 3. A base-carrying spec -> accepted.
    shutil.rmtree(D, ignore_errors=True)
    build.write_spec(NAME, goal="probe", decisions=["d"], permissions=["p"], escape_hatch="park")
    r = build.new_build(NAME, "ignored", STEPS)
    good = bool(r.get("ok"))
    print(f"  base-carrying spec accepted: {good}  ({r.get('ok') and r.get('result')})")
    ok = ok and good

    # 4. Second call -> "already exists", not "no base". Regression guard.
    r = build.new_build(NAME, "ignored", STEPS)
    good = (not r.get("ok")) and ("already exists" in str(r.get("error", "")))
    print(f"  second call refused as already-exists: {good}  ({r.get('error')})")
    ok = ok and good

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(D, ignore_errors=True)
