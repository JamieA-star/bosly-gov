#!/usr/bin/env python3
"""Restore bosly-gov's memory.json from a backup archive.

By default writes to the live corpus, after a .bak. With --to <path>,
writes to that path instead and does not touch live — that is the proof
run. Refuses if the restored copy has unciteable ids, or fewer items than
live (unless --force).

Usage:
  restore_corpus.py <data-*.tar.gz> --to /tmp/probe.json     # proof run
  restore_corpus.py <data-*.tar.gz>                          # real restore
  restore_corpus.py <data-*.tar.gz> --force                  # restore fewer
"""
import argparse, json, re, shutil, sys, tarfile
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json")
ID_PATTERN = re.compile(r"^(pattern|decision|fact|incident|session|build)-\d{8}-[a-z0-9][a-z0-9-]*$")

def read_memory(archive: Path) -> list:
    with tarfile.open(archive, "r:gz") as tf:
        members = [m for m in tf.getmembers()
                   if m.name.endswith("copilot-knowledge/bosly-gov/memory.json")]
        if len(members) != 1:
            raise SystemExit(f"FAIL: expected one memory.json, found {len(members)}")
        with tf.extractfile(members[0]) as f:
            return json.load(f)

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("archive")
    p.add_argument("--to", default="")
    p.add_argument("--force", action="store_true")
    a = p.parse_args()

    archive = Path(a.archive)
    if not archive.exists():
        print(f"FAIL: {archive} does not exist"); return 1

    restored = read_memory(archive)
    bad = [e.get("id") for e in restored if not ID_PATTERN.match(str(e.get("id", "")))]
    if bad:
        print(f"FAIL: {len(bad)} restored ids are not citeable: {bad[:3]}"); return 1
    print(f"restored copy is clean: {len(restored)} items")

    if a.to:
        Path(a.to).write_text(json.dumps(restored, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {len(restored)} items to {a.to} (live untouched)")
        return 0

    live = json.load(open(LIVE))
    print(f"live has {len(live)} items; restoring will replace it")
    if len(restored) < len(live) and not a.force:
        print("REFUSING: the backup has fewer items than live. Pass --force to override."); return 1

    bak = LIVE.with_suffix(f".json.bak-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(LIVE, bak)
    LIVE.write_text(json.dumps(restored, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"restored {len(restored)} items; live backup at {bak.name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
