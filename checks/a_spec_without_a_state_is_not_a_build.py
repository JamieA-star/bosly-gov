"""A spec without a state is not a build.

write_spec writes a directory and a spec.md; new_build writes state.json.
Between them is a directory that looks like a build and isn't. load_build
must refuse it with a message naming the state \u2014 not raise, and not
claim the name does not exist.

This check would have caught the KeyError that crashed the universal-
decisions check: the caller assumed load_build succeeded.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routers import build

NAME = "__spec_no_state__"
D = build._dir(NAME)

def main() -> int:
    shutil.rmtree(D, ignore_errors=True)
    ok = True
    try:
        r = build.write_spec(NAME, goal="probe", decisions=["d"],
                             permissions=["p"], escape_hatch="park")
        if not r.get("ok"):
            print(f"  FAIL: write_spec refused: {r.get('error')}"); return 1
        has_spec = (D / "spec.md").exists()
        no_state = not (D / "state.json").exists()
        print(f"  a spec exists and no state: {has_spec and no_state}")
        ok = ok and has_spec and no_state

        lb = build.load_build(NAME)
        refused = (not lb.get("ok"))
        names_state = "state.json" in str(lb.get("error", ""))
        print(f"  load_build refuses it: {refused}")
        print(f"  the error names the state: {names_state}  ({lb.get('error')})")
        ok = ok and refused and names_state

        raised = False
        try:
            build.load_build(NAME)["result"]["spec"]
        except KeyError:
            raised = True
        print(f"  indexing into the refusal raises KeyError (a caller must check ok): {raised}")
    finally:
        shutil.rmtree(D, ignore_errors=True)

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
