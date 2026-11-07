"""A build writes its own lesson, in the corpus, in the same shape.

Three assertions:
  1. record_lesson writes an entry whose id names the build.
  2. The entry is item_type "build" and passes memory_schema's id rule.
  3. The corpus still passes memory_schema after the write.

Red before record_lesson exists. Green after. The probe entry is removed
in a finally, so a failed run does not leave the corpus dirty.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routers import build

MEM = pathlib.Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json")
PROBE_BUILD = "__lesson_probe__"
ID_PATTERN = re.compile(r"^(pattern|decision|fact|incident|session|build)-\d{8}-[a-z0-9][a-z0-9-]*$")

def remove_probe():
    d = json.loads(MEM.read_text(encoding="utf-8"))
    # The stem is sanitised, so the id will not contain the underscores.
    keep = [e for e in d if "lesson-probe" not in str(e.get("id", ""))]
    if len(keep) != len(d):
        MEM.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")

def main() -> int:
    remove_probe()
    ok = True

    r = build.record_lesson(
        PROBE_BUILD,
        "A build writes its lesson as a generalisation, not a story. "
        "The entry is dated, named for the build, and typed build.",
        item_type="build",
    )
    good = bool(r.get("ok"))
    print(f"  1. record_lesson writes an entry: {good}  ({r.get('error') or r.get('result')})")
    ok = ok and good

    d = json.loads(MEM.read_text(encoding="utf-8"))
    # Look for the id the function returned, not the name it was given:
    # the id is sanitised, so the name will not appear in it.
    entry_id = (r.get("result") or {}).get("id", "")
    entries = [e for e in d if e.get("id") == entry_id]
    good = (len(entries) == 1
            and entries[0].get("item_type") == "build"
            and ID_PATTERN.match(str(entries[0].get("id", ""))) is not None)
    print(f"  2. the entry is typed build and citeable: {good}  "
          f"({entries[0].get('id') if entries else 'none'})")
    ok = ok and good

    # 3. The corpus still passes the schema.
    import subprocess
    schema = subprocess.run([sys.executable, str(ROOT / "checks" / "memory_schema.py")],
                            capture_output=True, text=True)
    good = schema.returncode == 0
    print(f"  3. memory_schema still passes after the write: {good}")
    ok = ok and good

    remove_probe()
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        remove_probe()
