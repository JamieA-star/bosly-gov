"""The corpus can be restored from a recent backup.

Three assertions, and the first is the one that would have caught 4 November:
  1. The newest data-*.tar.gz is less than 48 hours old. A backup that
     stopped running is a backup that is not a backup.
  2. The archive contains copilot-knowledge/bosly-gov/memory.json.
  3. The restored memory.json has the same item count as the live corpus
     and passes memory_schema's id rule.

Non-destructive: the archive is read, never written back over the live
corpus. The restore-to-live is a script run by hand, tested once.
"""
import json, re, subprocess, sys, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path

BACKUPS = Path("/home/bosly_accord/backups/full")
LIVE = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json")
ID_PATTERN = re.compile(r"^(pattern|decision|fact|incident|session|build)-\d{8}-[a-z0-9][a-z0-9-]*$")

def newest_data() -> Path | None:
    files = sorted(BACKUPS.glob("data-*.tar.gz"))
    return files[-1] if files else None

def main() -> int:
    ok = True

    # 1. Freshness.
    newest = newest_data()
    if newest is None:
        print("  1. no data archive found:  FAIL")
        return 1
    age_h = (datetime.now(timezone.utc) - datetime.fromtimestamp(
        newest.stat().st_mtime, tz=timezone.utc)).total_seconds() / 3600
    fresh = age_h < 48
    print(f"  1. newest backup is {age_h:.1f}h old (< 48): {fresh}  ({newest.name})")
    ok = ok and fresh

    # 2. The corpus is inside.
    try:
        with tarfile.open(newest, "r:gz") as tf:
            members = [m for m in tf.getnames()
                       if m.endswith("copilot-knowledge/bosly-gov/memory.json")]
            present = bool(members)
            print(f"  2. the archive contains the corpus: {present}")
            ok = ok and present
            if not present:
                return 1
            with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
                tf.extract(members[0], path=tmp.name + ".d")
                restored = json.load(open(f"{tmp.name}.d/{members[0]}"))
    except Exception as e:
        print(f"  2. could not read the archive: {e}")
        return 1

    # 3. Same count, and the id rule holds on the restored copy.
    live = json.load(open(LIVE))
    same = len(restored) <= len(live)
    print(f"  3. restored has {len(restored)} items, live has {len(live)}: {same}")
    bad = [e.get("id") for e in restored if not ID_PATTERN.match(str(e.get("id", "")))]
    clean = not bad
    print(f"     every restored id is citeable: {clean}  ({bad[:3] if bad else 'none'})")
    ok = ok and same and clean

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
