"""routers/filing.py — one place that files what a session produced.

session_summary and ingest_summary both come through here. The point is
one writer, not two: a memory entry, a plan tick, a plan add, a capsule
line. Each is idempotent — the same call twice writes once — because the
model will sometimes call twice and the store must not grow duplicates.

Nothing here decides WHAT to file. The model has read the conversation;
it says what to file, and this writes it. Filing is not judging.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

KNOWLEDGE = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov")
CAPSULES = KNOWLEDGE / "capsules"
MEMORY = KNOWLEDGE / "memory.json"
GOV = Path("/home/bosly_accord/bosly-gov")
PLAN = GOV / "PLAN.md"
NEXT = GOV / "NEXT.md"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---- memory --------------------------------------------------------------

def file_memory(
    entry_id: str,
    item_type: str,
    content: str,
    project_slug: str = "bosly-gov",
    dry_run: bool = True,
) -> Dict[str, Any]:
    """File one memory entry. Skips if the id is already present."""
    if not entry_id or not item_type or not content:
        return {"ok": False, "error": "entry_id, item_type, content required"}
    try:
        d = json.loads(MEMORY.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"memory unreadable: {e}"}
    ids = {e.get("id") for e in d}
    if entry_id in ids:
        return {"ok": True, "skipped": True, "id": entry_id}
    entry = {
        "id": entry_id,
        "project_slug": project_slug,
        "item_type": item_type,
        "content": content,
        "metadata_json": {},
        "created_at": _now(),
        "updated_at": _now(),
    }
    if dry_run:
        return {"ok": True, "would_write": entry, "skipped": False}
    d.append(entry)
    MEMORY.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "written": entry_id}


# ---- plan ----------------------------------------------------------------

def _find_item(text: str, item_id: str) -> Optional[int]:
    """Index of the line starting the item's marker, or None."""
    for i, line in enumerate(text.splitlines(keepends=True)):
        stripped = line.lstrip()
        if stripped.startswith("[ ] ") or stripped.startswith("[~] ") or stripped.startswith("[x] "):
            rest = stripped[4:].lstrip()
            if rest.startswith("[LIVE] "):
                rest = rest[7:]
            if rest.startswith(item_id + " ") or rest.startswith(item_id + "\u2014") or rest.startswith(item_id + " —"):
                return i
    return None


def file_plan_tick(item_id: str, note: str = "", dry_run: bool = True) -> Dict[str, Any]:
    """Flip an open item to [x] in PLAN.md and NEXT.md, with a note."""
    out: Dict[str, Any] = {"ok": True, "id": item_id, "files": {}}
    for path in (PLAN, NEXT):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            out["files"][path.name] = {"error": str(e)}
            out["ok"] = False
            continue
        lines = text.splitlines(keepends=True)
        idx = _find_item(text, item_id)
        if idx is None:
            out["files"][path.name] = {"skipped": True, "reason": "not found"}
            continue
        line = lines[idx]
        if "[x] " in line:
            out["files"][path.name] = {"skipped": True, "reason": "already done"}
            continue
        newline = line.replace("[ ] ", "[x] ", 1).replace("[~] ", "[x] ", 1)
        if dry_run:
            out["files"][path.name] = {"would_tick": newline.strip()[:120]}
            continue
        lines[idx] = newline
        if note:
            lines.insert(idx + 1, "    " + note.strip() + "\n")
        path.write_text("".join(lines), encoding="utf-8")
        out["files"][path.name] = {"ticked": True}
    return out


# ---- capsule -------------------------------------------------------------

def file_capsule(line: str, date: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
    """Append a line to today's capsule, or create it if absent.

    The convention is YYYY-MM-DD-<slug>.md. If a capsule exists for the
    date, the line is appended to the NEWEST one; otherwise a new file is
    created with the session heading.
    """
    if not line or not line.strip():
        return {"ok": False, "error": "line required"}
    day = date or _today()
    existing = sorted(CAPSULES.glob(f"{day}-*.md")) if CAPSULES.exists() else []
    if existing:
        path = existing[-1]
        if dry_run:
            return {"ok": True, "would_append": str(path), "line": line[:120]}
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + line.strip() + "\n")
        return {"ok": True, "appended": str(path)}
    path = CAPSULES / f"{day}-session.md"
    if dry_run:
        return {"ok": True, "would_create": str(path), "line": line[:120]}
    CAPSULES.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Capsule — {day}\n\n**Session name:** (filed by the butler)\n\n---\n\n"
        + line.strip() + "\n",
        encoding="utf-8",
    )
    return {"ok": True, "created": str(path)}
