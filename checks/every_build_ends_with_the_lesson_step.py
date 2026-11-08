"""Every build ends with the lesson step.

A build created with arbitrary steps has its last step set to the lesson:
write what you learned to the corpus. The rule is at the door, so no
caller can forget it and no build can finish without it.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routers import build

NAME = "__lesson_step_probe__"
D = build._dir(NAME)

def main() -> int:
    shutil.rmtree(D, ignore_errors=True)
    ok = True
    try:
        build.write_spec(NAME, goal="probe", decisions=["d"], permissions=["p"], escape_hatch="park")
        r = build.new_build(NAME, "ignored",
                            [{"title": "the one step", "check": "x",
                              "check_id": "gov.memory_schema"}])
        steps = build.load_build(NAME)["result"]["steps"]
        ids = [s.get("check_id") for s in steps]
        # The door appends the fixed tail: deploy, then the lesson. Assert the
        # shape, not a count, so adding a step at the door does not silently
        # break this check -- and removing one does not silently pass it.
        good = (bool(r.get("ok"))
                and ids[-2:] == ["gov.deploy_smoke_passes",
                                 "gov.a_build_writes_its_lesson"])
        print(f"  steps end [deploy, lesson]: {good}  ({ids})")
        ok = ok and good
    finally:
        shutil.rmtree(D, ignore_errors=True)
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
