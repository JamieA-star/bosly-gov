"""routers/pickup.py — the Executive notices new scout files.

WHAT THIS DOES. When the scout script runs (weekly, cron) it writes
a CSV. The Executive does not run on a timer; it checks whether the
CSV is newer than the last time it read it. If it is, it reads the
rows and returns a brief. If it isn't, it returns None and the
Executive says nothing about it.

WHY A FILE-TIMESTAMP CHECK, NOT A TIMER. The Executive should not
hold a scheduler. It should notice when there is something new. A
small state file records the last read; a timestamp compare is the
whole logic. The cron does the running; the Executive does the
noticing.

WHERE IT LIVES:
  the CSV:     /mnt/bosly/bosly-data/.data/governor/lead-scout.csv
  the state:   /mnt/bosly/bosly-data/.data/governor/lead-scout.state.json

The state file holds {"last_read_mtime": <float>} — the mtime of the
CSV the last time the Executive read it. If the CSV's mtime is
later, there is something new.

THE BRIEF. When there is something new, this returns a short text
block describing the new rows. The server prepends it to the model's
system context, so the Executive opens the conversation by telling
the founder what it found. It does not act on the leads; it tells
the founder they exist.

TESTING: set BOSLY_SCOUT_CSV and BOSLY_SCOUT_STATE to override the
paths. The self-test does exactly that.

Run: python3 routers/pickup.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_CSV = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout.csv")
DEFAULT_STATE = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout.state.json")


def _csv_path() -> Path:
    return Path(os.environ.get("BOSLY_SCOUT_CSV", str(DEFAULT_CSV)))


def _state_path() -> Path:
    return Path(os.environ.get("BOSLY_SCOUT_STATE", str(DEFAULT_STATE)))


def _read_state() -> Dict[str, Any]:
    p = _state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(state: Dict[str, Any]) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _read_csv(path: Path) -> List[Dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def maybe_pickup() -> Optional[str]:
    """Return a brief if the CSV is newer than the last read, else None.

    Does not modify the CSV. Updates the state file only when it has
    successfully read the new file — so a half-written CSV from a
    crashed scout is not recorded as 'seen'.
    """
    csv_path = _csv_path()
    if not csv_path.exists():
        return None

    try:
        mtime = csv_path.stat().st_mtime
    except Exception:
        return None

    state = _read_state()
    last = state.get("last_read_mtime", 0)
    if mtime <= float(last or 0):
        return None

    rows = _read_csv(csv_path)
    if not rows:
        # Empty file: record the mtime so we don't re-read a zero
        # result every message, but do not claim candidates.
        _write_state({"last_read_mtime": mtime, "last_count": 0})
        return None

    # Build a short, honest brief. First 5 names; count the rest.
    names = [r.get("name") or "(unnamed)" for r in rows[:5]]
    more = len(rows) - len(names)
    lines = [
        "[Scout file update — new since your last check]",
        f"{len(rows)} new candidate(s) in lead-scout.csv.",
        "First few:",
    ]
    for r in rows[:5]:
        bits = [r.get("name") or "(unnamed)"]
        if r.get("city"):
            bits.append(r["city"])
        if r.get("category"):
            bits.append(r["category"])
        lines.append("  - " + " — ".join(bits))
    if more > 0:
        lines.append(f"  ... and {more} more.")
    lines.append(
        "When the founder's message arrives, mention the new candidates "
        "briefly. Do not act on them until asked."
    )
    brief = "\n".join(lines)

    # Only now record the mtime — the file was read successfully.
    _write_state({"last_read_mtime": mtime, "last_count": len(rows)})
    return brief


# ---------------------------------------------------------------------------
# Self-test — writes a temp CSV and a temp state, no real files touched
# ---------------------------------------------------------------------------

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
                for line in detail.splitlines():
                    print(f"      {line}")

    tmp = tempfile.mkdtemp()
    csv_path = Path(tmp) / "lead-scout.csv"
    state_path = Path(tmp) / "lead-scout.state.json"
    os.environ["BOSLY_SCOUT_CSV"] = str(csv_path)
    os.environ["BOSLY_SCOUT_STATE"] = str(state_path)

    try:
        # No CSV yet: nothing to pick up.
        check("no CSV → None", maybe_pickup() is None)

        # Write a CSV with three rows.
        csv_path.write_text(
            "name,category,lat,lon,street,city,postcode,phone,osm_id,has_website\n"
            "Hair by Jane,hairdresser,,,High St,Hexham,NE46 1AA,,node/1,no\n"
            "Café Corner,cafe,,,Market St,Hexham,NE46 2BB,,node/2,no\n"
            "The Barbers,barber,,,Fore St,Hexham,NE46 3CC,,node/3,no\n",
            encoding="utf-8",
        )
        # Ensure mtime is newer than nothing (state file absent)
        brief = maybe_pickup()
        check("first pickup returns a brief", brief is not None,
              detail=f"brief={brief!r}")
        check("brief mentions the count", brief and "3 new candidate" in brief,
              detail=str(brief))
        check("brief names the first one", brief and "Hair by Jane" in brief,
              detail=str(brief))
        check("brief does not claim to act",
              brief and "Do not act" in brief,
              detail=str(brief))

        # Second call: state file says we already read it.
        check("second pickup returns None", maybe_pickup() is None)

        # Touch the CSV to a newer mtime.
        import time
        time.sleep(0.05)
        csv_path.write_text(
            csv_path.read_text() + "New Place,cafe,,,Side St,Hexham,NE46 4DD,,node/4,no\n",
            encoding="utf-8",
        )
        brief = maybe_pickup()
        check("new mtime returns a new brief", brief is not None,
              detail=f"brief={brief!r}")
        check("new brief counts 4", brief and "4 new candidate" in brief,
              detail=str(brief))

        # Empty CSV: no brief, but state is recorded so it doesn't spam.
        csv_path.write_text("name,category,lat,lon,street,city,postcode,phone,osm_id,has_website\n",
                            encoding="utf-8")
        time.sleep(0.05)
        check("empty CSV returns None", maybe_pickup() is None)
        check("empty CSV recorded count 0",
              json.loads(state_path.read_text())["last_count"] == 0)
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)
        os.environ.pop("BOSLY_SCOUT_CSV", None)
        os.environ.pop("BOSLY_SCOUT_STATE", None)

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_selftest())
