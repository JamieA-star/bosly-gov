#!/usr/bin/env python3
"""
Bosly Gov v4 - Consent Flow UX State Manager
Python 3.12+

Timeline:
Proposed -> Reviewed -> Approved/Denied -> Applied -> Deployed
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path("/mnt/bosly/bosly-data/governor/consent-flow")
ACTIONS_DIR = BASE_DIR / "actions"
TIMELINE_DIR = BASE_DIR / "timelines"
SESSION_LOG = BASE_DIR / "session-log.jsonl"

ALLOWED_STATES = {"proposed", "reviewed", "approved", "denied", "applied", "deployed"}
ALLOWED_DIFF_MODES = {"unified", "split", "collapsed"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_dirs() -> None:
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    TIMELINE_DIR.mkdir(parents=True, exist_ok=True)
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def _action_path(action_id: str) -> Path:
    return ACTIONS_DIR / f"{action_id}.json"


def _timeline_path(action_id: str) -> Path:
    return TIMELINE_DIR / f"{action_id}.jsonl"


def _new_action_id() -> str:
    return secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:14]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sanitize_files(files: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for f in files or []:
        if not isinstance(f, dict):
            continue
        p = str(f.get("path", "")).strip()
        if not p:
            continue
        out.append(
            {
                "path": p,
                "status": str(f.get("status", "pending")).strip().lower() or "pending",
                "diff": str(f.get("diff", "")),
                "why": str(f.get("why", "")),
                "risk_level": str(f.get("risk_level", "medium")).strip().lower() or "medium",
            }
        )
    return out


def _normalize_diff_mode(v: str | None) -> str:
    m = str(v or "unified").strip().lower()
    return m if m in ALLOWED_DIFF_MODES else "unified"


def _append_timeline(action_id: str, state: str, actor: str = "system", meta: dict[str, Any] | None = None) -> None:
    if state not in ALLOWED_STATES:
        raise ValueError(f"Invalid state: {state}")
    row = {
        "ts": _now_iso(),
        "action_id": action_id,
        "state": state,
        "actor": actor,
        "meta": meta or {},
    }
    _append_jsonl(_timeline_path(action_id), row)
    _append_jsonl(SESSION_LOG, row)


def create_pending_action(action: dict) -> dict:
    _ensure_dirs()

    action_id = str(action.get("action_id", "")).strip() or _new_action_id()
    files = _sanitize_files(action.get("files"))
    if not files:
        p = str(action.get("path", "")).strip()
        if p:
            files = [{"path": p, "status": "pending", "diff": str(action.get("diff", "")), "why": "", "risk_level": "medium"}]

    item = {
        "action_id": action_id,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "state": "proposed",
        "title": str(action.get("title", "Proposed change")).strip(),
        "summary": str(action.get("summary", "")).strip(),
        "why_change": str(action.get("why_change", "")).strip(),
        "risk_level": str(action.get("risk_level", "medium")).strip().lower() or "medium",
        "diff_mode": _normalize_diff_mode(action.get("diff_mode")),
        "session_id": str(action.get("session_id", "")).strip() or None,
        "token": str(action.get("token", "")).strip() or None,
        "files": files,
        "metadata": action.get("metadata", {}) if isinstance(action.get("metadata", {}), dict) else {},
    }

    _write_json(_action_path(action_id), item)
    _append_timeline(action_id, "proposed", actor="system", meta={"files": len(files)})
    return {"ok": True, "action": item}


def get_pending_action(action_id: str) -> dict | None:
    item = _read_json(_action_path(action_id))
    if not item:
        return None
    return item


def list_pending_actions() -> list[dict]:
    _ensure_dirs()
    out: list[dict] = []
    for p in ACTIONS_DIR.glob("*.json"):
        item = _read_json(p)
        if not item:
            continue
        if str(item.get("state", "")).lower() in ("proposed", "reviewed", "approved"):
            out.append(item)
    out.sort(key=lambda x: str(x.get("updated_at", "")), reverse=True)
    return out


def approve_action(action_id: str) -> dict:
    item = _read_json(_action_path(action_id))
    if not item:
        return {"ok": False, "error": "Action not found"}

    if item.get("state") == "denied":
        return {"ok": False, "error": "Denied actions cannot be approved"}

    item["state"] = "approved"
    item["updated_at"] = _now_iso()
    for f in item.get("files", []):
        if f.get("status") == "pending":
            f["status"] = "approved"

    _write_json(_action_path(action_id), item)
    _append_timeline(action_id, "approved", actor="user")
    return {"ok": True, "action": item}


def deny_action(action_id: str) -> dict:
    item = _read_json(_action_path(action_id))
    if not item:
        return {"ok": False, "error": "Action not found"}

    item["state"] = "denied"
    item["updated_at"] = _now_iso()
    for f in item.get("files", []):
        if f.get("status") in ("pending", "approved"):
            f["status"] = "denied"

    _write_json(_action_path(action_id), item)
    _append_timeline(action_id, "denied", actor="user")
    return {"ok": True, "action": item}


def approve_action_files(action_id: str, approved_paths: list[str], denied_paths: list[str] | None = None) -> dict:
    item = _read_json(_action_path(action_id))
    if not item:
        return {"ok": False, "error": "Action not found"}

    approved_set = {str(x).strip() for x in (approved_paths or []) if str(x).strip()}
    denied_set = {str(x).strip() for x in (denied_paths or []) if str(x).strip()}

    changed = 0
    for f in item.get("files", []):
        p = str(f.get("path", "")).strip()
        if p in approved_set:
            f["status"] = "approved"
            changed += 1
        elif p in denied_set:
            f["status"] = "denied"
            changed += 1

    statuses = {str(f.get("status", "pending")) for f in item.get("files", [])}
    if statuses <= {"approved", "applied", "deployed"}:
        item["state"] = "approved"
    elif statuses == {"denied"} or ("approved" not in statuses and "pending" not in statuses):
        item["state"] = "denied"
    else:
        item["state"] = "reviewed"

    item["updated_at"] = _now_iso()
    _write_json(_action_path(action_id), item)
    _append_timeline(
        action_id,
        "reviewed",
        actor="user",
        meta={"partial": True, "changed_files": changed, "approved": list(approved_set), "denied": list(denied_set)},
    )
    return {"ok": True, "action": item}


def mark_action_applied(action_id: str, meta: dict[str, Any] | None = None) -> dict:
    item = _read_json(_action_path(action_id))
    if not item:
        return {"ok": False, "error": "Action not found"}
    item["state"] = "applied"
    item["updated_at"] = _now_iso()
    for f in item.get("files", []):
        if f.get("status") == "approved":
            f["status"] = "applied"
    _write_json(_action_path(action_id), item)
    _append_timeline(action_id, "applied", actor="system", meta=meta or {})
    return {"ok": True, "action": item}


def mark_action_deployed(action_id: str, meta: dict[str, Any] | None = None) -> dict:
    item = _read_json(_action_path(action_id))
    if not item:
        return {"ok": False, "error": "Action not found"}
    item["state"] = "deployed"
    item["updated_at"] = _now_iso()
    for f in item.get("files", []):
        if f.get("status") == "applied":
            f["status"] = "deployed"
    _write_json(_action_path(action_id), item)
    _append_timeline(action_id, "deployed", actor="system", meta=meta or {})
    return {"ok": True, "action": item}


def get_action_timeline(action_id: str) -> list[dict]:
    path = _timeline_path(action_id)
    if not path.exists():
        return []
    out: list[dict] = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            row = json.loads(ln)
            if isinstance(row, dict):
                out.append(row)
        except Exception:
            continue
    return out
