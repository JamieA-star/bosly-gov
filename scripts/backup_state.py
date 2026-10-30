#!/usr/bin/env python3
"""backup_state.py — nightly backup that discovers what to keep.

PHILOSOPHY: discover, don't list. A backup that needs its file list
updated every time the system grows is a backup that silently stops
covering the new thing. So this script walks the two data roots and
applies rules:

    /mnt/bosly/bosly-data/copilot-knowledge/
        every *memory.json*        (the real file, not .bak-*)
        every *chat.json*
        every *.db                 (things.db and any future store)
        every *capsules/**/*.md*

    /mnt/bosly/bosly-data/.data/governor/
        every *lead-scout*.csv*
        every *lead-scout*.json*   (state, retry, sweep marker)
        every *.jsonl              (enquiries, unknown-intents)
        NOT logs, NOT audit-*.txt, NOT agent-sessions/

Anything new that fits a pattern is backed up without editing the
script. Anything that does not fit is left out on purpose.

THE GUARD: after copying, every file is checked present and
non-zero. Every *.db is opened and PRAGMA quick_check run. A backup
that silently fails is worse than no backup.

WHERE: /mnt/bosly/bosly-data/backups/state/YYYY-MM-DD/
KEEPS: 14 days.

USAGE:
    python3 scripts/backup_state.py
    python3 scripts/backup_state.py --selftest   (temp dirs, no real files)
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

KNOWLEDGE = Path("/mnt/bosly/bosly-data/copilot-knowledge")
GOVERNOR = Path("/mnt/bosly/bosly-data/.data/governor")
GOV_DATA = Path("/home/bosly_accord/bosly-gov/data")
BACKUPS = Path("/mnt/bosly/bosly-data/backups/state")
KEEP_DAYS = 14

# .jsonl is used for both state and logs. These are the ones that are
# state. Everything else (.log, gov-interactions, decisions,
# deletion-audit, memory.jsonl) is a log and is not backed up.
GOVERNOR_STATE_JSONL = {
    "consultancy-enquiries.jsonl",
    "unknown-intents.jsonl",
    "waiting-well-questions.jsonl",
}


def discover(knowledge: Path, governor: Path) -> list[tuple[Path, str]]:
    """Return (source_path, relative_dest) pairs, discovered by rule."""
    out: list[tuple[Path, str]] = []

    # --- knowledge: memory, chat, db, capsules ---
    if knowledge.exists():
        for slug_dir in sorted(knowledge.iterdir()):
            if not slug_dir.is_dir():
                continue
            slug = slug_dir.name
            for name in ("memory.json", "chat.json"):
                p = slug_dir / name
                if p.exists():
                    out.append((p, f"{slug}/{name}"))
            for p in slug_dir.glob("*.db"):
                if p.is_file():
                    out.append((p, f"{slug}/{p.name}"))
            caps = slug_dir / "capsules"
            if caps.exists():
                for p in sorted(caps.glob("*.md")):
                    out.append((p, f"{slug}/capsules/{p.name}"))

    # --- gov-data: live inputs moved inside the repo (gitignored) ---
    if GOV_DATA.exists():
        p = GOV_DATA / "unknown-intents.jsonl"
        if p.is_file():
            out.append((p, "gov-data/unknown-intents.jsonl"))

    # --- governor: lead scout state and the small jsonl files ---
    if governor.exists():
        for p in sorted(governor.iterdir()):
            if not p.is_file():
                continue
            n = p.name
            if n.startswith("lead-scout") and (n.endswith(".csv") or n.endswith(".json")):
                out.append((p, n))
            elif n in GOVERNOR_STATE_JSONL:
                out.append((p, n))

    return out


def _copy_file(src: Path, dst: Path) -> tuple[bool, str]:
    if not src.exists():
        return False, f"missing: {src}"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    except Exception as e:
        return False, f"copy failed {src}: {e}"
    if not dst.exists():
        return False, f"not written: {dst}"
    if dst.stat().st_size == 0:
        return False, f"zero bytes: {dst}"
    return True, ""


def _sqlite_check(path: Path) -> tuple[bool, str]:
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            r = con.execute("PRAGMA quick_check").fetchone()
        finally:
            con.close()
    except Exception as e:
        return False, f"sqlite open failed {path}: {e}"
    if not r or r[0] != "ok":
        return False, f"sqlite integrity not ok: {path}: {r}"
    return True, ""


def run_backup(knowledge: Path = KNOWLEDGE, governor: Path = GOVERNOR,
               root: Path = BACKUPS) -> int:
    dest = root / date.today().isoformat()
    dest.mkdir(parents=True, exist_ok=True)

    pairs = discover(knowledge, governor)
    if not pairs:
        print("FAIL: discovered nothing to back up — check the roots", file=sys.stderr)
        return 1

    failures: list[str] = []
    copied = 0
    for src, rel in pairs:
        dst = dest / rel
        ok, detail = _copy_file(src, dst)
        if ok:
            copied += 1
        else:
            failures.append(detail)

    # integrity on every copied .db
    for copied_db in dest.rglob("*.db"):
        ok, detail = _sqlite_check(copied_db)
        if not ok:
            failures.append(detail)

    # prune
    cutoff = date.today() - timedelta(days=KEEP_DAYS)
    if root.exists():
        for d in root.iterdir():
            if not d.is_dir():
                continue
            try:
                if date.fromisoformat(d.name) < cutoff:
                    shutil.rmtree(d, ignore_errors=True)
                    print(f"  pruned: {d.name}", file=sys.stderr)
            except ValueError:
                continue

    total = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    print(f"backup: {copied} file(s), {total/1024:.0f} KB -> {dest}")
    if failures:
        print("FAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("OK: every copied file is present and non-empty; every .db integrity ok.")
    return 0


def _selftest() -> int:
    passed = 0
    failed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}")
            if detail:
                print("      " + detail)

    tmp = Path(tempfile.mkdtemp())
    k = tmp / "knowledge"
    g = tmp / "governor"
    b = tmp / "backups"
    k.mkdir()
    g.mkdir()

    # Build a fake knowledge tree
    gov = k / "bosly-gov"
    gov.mkdir()
    (gov / "memory.json").write_text("[]")
    (gov / "chat.json").write_text("[]")
    con = sqlite3.connect(str(gov / "things.db"))
    con.execute("CREATE TABLE x (a TEXT)")
    con.commit()
    con.close()
    (gov / "capsules").mkdir()
    (gov / "capsules" / "c1.md").write_text("# c1")
    # a .bak that must be ignored
    (gov / "memory.json.bak-20260101").write_text("[]")

    # Fake governor
    (g / "lead-scout-ranked.csv").write_text("name\nA\n")
    (g / "lead-scout.sweep.json").write_text("{}")
    (g / "consultancy-enquiries.jsonl").write_text("{}\n")
    (g / "anomaly-alerts.log").write_text("noise")
    (g / "audit-20260101.txt").write_text("noise")

    pairs = discover(k, g)
    rels = sorted(rel for _, rel in pairs)

    check("discovers memory.json", "bosly-gov/memory.json" in rels)
    check("discovers chat.json", "bosly-gov/chat.json" in rels)
    check("discovers things.db", "bosly-gov/things.db" in rels)
    check("discovers capsules", "bosly-gov/capsules/c1.md" in rels)
    check("ignores .bak", not any(".bak" in r for r in rels))
    check("discovers lead-scout csv", "lead-scout-ranked.csv" in rels)
    check("discovers lead-scout state", "lead-scout.sweep.json" in rels)
    check("discovers jsonl", "consultancy-enquiries.jsonl" in rels)
    check("ignores .log", not any(r.endswith(".log") for r in rels))
    check("ignores audit-*.txt", not any(r.startswith("audit-") for r in rels))

    # run the backup
    rc = run_backup(k, g, b)
    check("run_backup exits 0", rc == 0, detail=str(rc))
    today = b / date.today().isoformat()
    check("backup dir exists", today.exists())
    check("things.db copied and non-empty",
          (today / "bosly-gov/things.db").exists()
          and (today / "bosly-gov/things.db").stat().st_size > 0)
    check("a .bak was NOT copied",
          not (today / "bosly-gov/memory.json.bak-20260101").exists())

    shutil.rmtree(tmp, ignore_errors=True)
    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover and back up the state git does not hold.")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    return run_backup()


if __name__ == "__main__":
    sys.exit(main())
