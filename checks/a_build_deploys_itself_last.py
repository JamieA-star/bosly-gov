"""A build deploys itself before it writes its lesson.

A build that ticks every step and never deploys is a build that is not
live. The steps end with Deploy, then Write the lesson: the deploy makes
the work real, and the lesson is only written for a build that deployed.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routers import build

NAME = "__deploy_step_probe__"
D = build._dir(NAME)

def main() -> int:
    shutil.rmtree(D, ignore_errors=True)
    ok = True
    try:
        build.write_spec(NAME, goal="probe", decisions=["d"],
                         permissions=["p"], escape_hatch="park")
        r = build.new_build(NAME, "ignored",
                            [{"title": "the one step", "check": "x",
                              "check_id": "gov.memory_schema"}])
        steps = build.load_build(NAME)["result"]["steps"]
        ids = [s.get("check_id") for s in steps]
        good = (bool(r.get("ok"))
                and len(ids) == 3
                and ids[-2] == "gov.deploy_smoke_passes"
                and ids[-1] == "gov.a_build_writes_its_lesson")
        print(f"  steps end [deploy, lesson]: {good}  ({ids})")
        ok = ok and good
    finally:
        shutil.rmtree(D, ignore_errors=True)

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
