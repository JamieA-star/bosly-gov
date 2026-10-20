"""routers/ecosystem.py — one reader for the whole ecosystem.

WHAT THIS IS. A single tool that returns the state of the ecosystem,
section by section. The Executive calls it when the founder asks
"what's going on?" or before it acts, and gets a structured picture
instead of re-reading five sources.

SECTIONS (developer mode, 20 Oct):
    plan      the plan's in-progress items
    things    active clients, leads, drafts, projects
    scout     this week's ranked list, if there is one
    capsules  the latest capsule
    accord    NOT YET — needs the session token (gov.executive_access)

Each section is read on its own and returns what it finds, honestly.
A section that cannot be read says so; it is not silently empty.

THE GUARD: fixed sources, fixed queries, structured output. The
model asks for a section; it does not pass a path or SQL. Every
section catches its own errors and reports them in the result.

PRODUCT MODE (later): the same sections, scoped to one user's
Accord profile. Not built. See gov.executive_access.

USAGE:
    python3 routers/ecosystem.py --selftest
    python3 routers/ecosystem.py --section plan
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

GOV = Path("/home/bosly_accord/bosly-gov")
PLAN = GOV / "PLAN.md"
GOVERNOR = Path("/mnt/bosly/bosly-data/.data/governor")
RANKED = GOVERNOR / "lead-scout-ranked.csv"
CAPSULES = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/capsules")


# ---------------------------------------------------------------------------
# Section readers
# ---------------------------------------------------------------------------

def _read_plan() -> Dict[str, Any]:
    """The plan's in-progress items."""
    if not PLAN.exists():
        return {"error": "PLAN.md not found"}
    text = PLAN.read_text(encoding="utf-8")
    # Last updated line
    m = re.search(r"Last updated:\s*(\d+\s+\w+\s+\d{4})", text)
    updated = m.group(1) if m else ""
    # In-progress entries: lines starting [~]
    items = []
    for line in text.splitlines():
        if line.startswith("[~]"):
            name = line[3:].strip().split("—")[0].strip()
            rest = line[3:].strip()
            items.append({"name": name, "line": rest[:140]})
    return {"in_progress": items, "count": len(items), "last_updated": updated}


def _read_things() -> Dict[str, Any]:
    """Active things, by kind."""
    try:
        sys.path.insert(0, str(GOV))
        from routers.things import find_things
    except Exception as e:
        return {"error": f"things store unavailable: {e}"}
    out: Dict[str, Any] = {}
    for kind in ("client", "lead", "draft", "project", "idea"):
        try:
            r = find_things(kind=kind, status="active", limit=20)
        except Exception as e:
            out[kind] = {"error": str(e)[:120]}
            continue
        if not r.get("ok"):
            out[kind] = {"error": r.get("error", "unknown")}
            continue
        rows = r["result"]["things"]
        out[kind] = [
            {"title": t.get("title", ""), "status": t.get("status", "")}
            for t in rows
        ]
    return out


def _read_scout() -> Dict[str, Any]:
    """This week's ranked list, if the file exists."""
    if not RANKED.exists():
        return {"present": False}
    try:
        with RANKED.open(newline="", encoding="utf-8") as f:
            rows = [dict(r) for r in csv.DictReader(f)]
    except Exception as e:
        return {"error": f"could not read ranked CSV: {e}"}
    top = rows[:5]
    return {
        "present": True,
        "count": len(rows),
        "call_list": sum(1 for r in rows if (r.get("call_list") or "") == "yes"),
        "top": [
            {
                "name": r.get("name", ""),
                "city": r.get("city", ""),
                "score": r.get("fit_score", ""),
                "route": r.get("contact_route", "") or r.get("route", ""),
                "call": r.get("call_list", ""),
            }
            for r in top
        ],
    }


def _read_capsules() -> Dict[str, Any]:
    """The latest capsule's title and date."""
    if not CAPSULES.exists():
        return {"error": "capsules directory not found"}
    files = sorted(CAPSULES.glob("*.md"), reverse=True)
    if not files:
        return {"present": False}
    latest = files[0]
    try:
        lines = latest.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return {"error": f"could not read {latest.name}: {e}"}
    title = next((l.lstrip("# ").strip() for l in lines if l.startswith("#")), latest.name)
    return {
        "count": len(files),
        "latest": latest.name,
        "title": title,
        "latest_date": latest.stem[:10],
    }


# ---------------------------------------------------------------------------
# The tool
# ---------------------------------------------------------------------------

SECTIONS = {
    "plan": _read_plan,
    "things": _read_things,
    "scout": _read_scout,
    "capsules": _read_capsules,
}


def ecosystem_state(section: str = "all") -> Dict[str, Any]:
    """Read the ecosystem state. section is 'all' or a section name."""
    if section != "all" and section not in SECTIONS:
        return {
            "ok": False,
            "error": f"unknown section {section!r}; known: {sorted(SECTIONS)} or 'all'",
        }
    wanted = SECTIONS.keys() if section == "all" else [section]
    out: Dict[str, Any] = {}
    for name in wanted:
        try:
            out[name] = SECTIONS[name]()
        except Exception as e:
            out[name] = {"error": f"{name} raised: {e}"}
    # Accord is honest, not missing.
    if section == "all" or section == "accord":
        out["accord"] = {"error": "not yet — needs the session token (gov.executive_access)"}
    return {"ok": True, "result": out}


# ---------------------------------------------------------------------------
# Self-test — each reader on real files, no network
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
                print("      " + detail)

    # unknown section
    r = ecosystem_state(section="nope")
    check("unknown section refused", not r["ok"])

    # plan
    r = ecosystem_state(section="plan")
    check("plan returns ok", r["ok"])
    check("plan has in_progress list", isinstance(r["result"]["plan"].get("in_progress"), list),
          detail=str(r["result"]["plan"])[:200])
    check("plan count > 0", r["result"]["plan"].get("count", 0) > 0,
          detail=str(r["result"]["plan"].get("count")))

    # things
    r = ecosystem_state(section="things")
    check("things returns ok", r["ok"])
    check("things has lead key", "lead" in r["result"]["things"],
          detail=str(r["result"]["things"])[:200])

    # scout
    r = ecosystem_state(section="scout")
    check("scout returns ok", r["ok"])
    check("scout reports presence", "present" in r["result"]["scout"],
          detail=str(r["result"]["scout"])[:200])

    # capsules
    r = ecosystem_state(section="capsules")
    check("capsules returns ok", r["ok"])
    check("capsules count >= 4", r["result"]["capsules"].get("count", 0) >= 4,
          detail=str(r["result"]["capsules"])[:200])

    # all
    r = ecosystem_state(section="all")
    check("all returns ok", r["ok"])
    check("all has all sections",
          all(k in r["result"] for k in ("plan", "things", "scout", "capsules", "accord")),
          detail=str(sorted(r["result"].keys())))
    check("accord says token pending",
          "token" in r["result"]["accord"].get("error", ""),
          detail=str(r["result"]["accord"]))

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Read the ecosystem state.")
    ap.add_argument("--section", default="all")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    r = ecosystem_state(section=args.section)
    print(json.dumps(r, indent=2)[:4000])
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
