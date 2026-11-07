"""The spec inherits decisions marked universal.

A decision marked metadata_json.universal=true appears in a spec produced
by write_spec, between the base and the build's own decisions. An
unmarked decision does not. The cap holds: at most 12 universal decisions
are included, newest first.

Red before the loader and the section exist.
"""
import json, pathlib, shutil, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routers import build

MEM = pathlib.Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json")
NAME = "__universal_check__"
D = build._dir(NAME)
TAG = "a decision marked universal for the check"

def clean_mem():
    d = json.loads(MEM.read_text(encoding="utf-8"))
    keep = [e for e in d if TAG not in str(e.get("content", ""))]
    if len(keep) != len(d):
        MEM.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(keep)

def main() -> int:
    shutil.rmtree(D, ignore_errors=True)
    clean_mem()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    day = now[:10].replace("-", "")

    d = json.loads(MEM.read_text(encoding="utf-8"))
    d.append({"id": f"decision-{day}-universal-check-marked",
              "project_slug": "bosly-gov", "item_type": "decision",
              "content": f"UNIVERSAL: {TAG}. Every build inherits this.",
              "metadata_json": {"universal": True},
              "created_at": now, "updated_at": now})
    d.append({"id": f"decision-{day}-universal-check-unmarked",
              "project_slug": "bosly-gov", "item_type": "decision",
              "content": f"NOT UNIVERSAL: {TAG}. Specific to one build.",
              "metadata_json": {},
              "created_at": now, "updated_at": now})
    MEM.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

    ok = True
    try:
        r = build.write_spec(NAME, goal="probe", decisions=["the build's own"],
                             permissions=["p"], escape_hatch="park")
        if not r.get("ok"):
            print(f"  write_spec refused: {r.get('error')}")
            print("\nSUMMARY: FAIL"); return 1
        spec = (build._dir(NAME) / "spec.md").read_text(encoding="utf-8")
        marked = f"UNIVERSAL: {TAG}" in spec
        unmarked = f"NOT UNIVERSAL: {TAG}" in spec
        print(f"  a universal decision is in the spec:  {marked}")
        print(f"  an unmarked decision is not:          {not unmarked}")
        ok = ok and marked and not unmarked

        # The cap: 13 universal decisions, only 12 in the spec.
        d = json.loads(MEM.read_text(encoding="utf-8"))
        for i in range(13):
            d.append({"id": f"decision-{day}-universal-cap-{i:02d}",
                      "project_slug": "bosly-gov", "item_type": "decision",
                      "content": f"CAP {TAG} {i:02d}",
                      "metadata_json": {"universal": True},
                      "created_at": now, "updated_at": now})
        MEM.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        shutil.rmtree(D, ignore_errors=True)
        r = build.write_spec(NAME, goal="probe", decisions=["x"],
                             permissions=["p"], escape_hatch="park")
        spec = (build._dir(NAME) / "spec.md").read_text(encoding="utf-8")
        included = sum(1 for i in range(13) if f"CAP {TAG} {i:02d}" in spec)
        print(f"  at most 12 universal decisions in the spec: {included} (cap 12)")
        ok = ok and included <= 12
    finally:
        shutil.rmtree(D, ignore_errors=True)
        clean_mem()

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
