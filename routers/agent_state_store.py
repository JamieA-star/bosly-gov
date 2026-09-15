#!/usr/bin/env python3
"""
Bosly Gov v4 - Agent State Store
Persistent session state + event log for Phase 2.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

STORE_ROOT = Path("/mnt/bosly/bosly-data/.data/governor/agent-sessions")
SESSIONS_DIR = STORE_ROOT / "sessions"
INDEX_FILE = STORE_ROOT / "index.jsonl"

_LOCK = threading.Lock()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_dirs() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    STORE_ROOT.mkdir(parents=True, exist_ok=True)


def _safe_session_id() -> str:
    return f"ags-{uuid.uuid4().hex[:16]}"


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"

def _session_lock_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.lock"

@contextmanager
def _session_file_lock(session_id: str):
    _ensure_dirs()
    lock_path = _session_lock_path(session_id)
    with lock_path.open("a+", encoding="utf-8") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _append_index(entry: Dict[str, Any]) -> None:
    _ensure_dirs()
    with INDEX_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def create_session(initial: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_dirs()
    session_id = _safe_session_id()
    now = utc_now_iso()
    record = {
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "status": "created",
        "state": "created",
        "input": initial,
        "plan": [],
        "attempts": [],
        "events": [],
        "artifacts": {},
        "result": {},
        "error": None,
    }
    with _LOCK:
        _atomic_write_json(_session_path(session_id), record)
        _append_index({
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "status": "created",
            "state": "created",
            "file": str(initial.get("file") or ""),
        })
    return record


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    p = _session_path(session_id)
    if not p.exists():
        return None
    try:
        with _session_file_lock(session_id):
            if not p.exists():
                return None
            return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def save_session(record: Dict[str, Any]) -> Dict[str, Any]:
    sid = str(record.get("session_id") or "").strip()
    if not sid:
        raise ValueError("Missing session_id.")
    record["updated_at"] = utc_now_iso()
    with _LOCK:
        with _session_file_lock(sid):
            _atomic_write_json(_session_path(sid), record)
            _append_index({
            "session_id": sid,
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "status": record.get("status"),
            "state": record.get("state"),
            "file": ((record.get("input") or {}).get("file") if isinstance(record.get("input"), dict) else ""),
        })
    return record


def append_event(record: Dict[str, Any], kind: str, message: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if "events" not in record or not isinstance(record.get("events"), list):
        record["events"] = []
    record["events"].append({
        "ts": utc_now_iso(),
        "kind": kind,
        "message": message,
        "data": data or {},
    })
    return record

def mutate_session(session_id: str, mutator):
    """Atomic read-modify-write helper under per-session lock."""
    with _LOCK:
        with _session_file_lock(session_id):
            p = _session_path(session_id)
            if not p.exists():
                return None
            try:
                rec = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return None
            if not isinstance(rec, dict):
                return None
            updated = mutator(rec) or rec
            if not isinstance(updated, dict):
                updated = rec
            updated["updated_at"] = utc_now_iso()
            _atomic_write_json(p, updated)
            _append_index({
                "session_id": session_id,
                "created_at": updated.get("created_at"),
                "updated_at": updated.get("updated_at"),
                "status": updated.get("status"),
                "state": updated.get("state"),
                "file": ((updated.get("input") or {}).get("file") if isinstance(updated.get("input"), dict) else ""),
            })
            return updated


def list_recent_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Return latest entry per unique session_id (deduped), newest first.
    """
    _ensure_dirs()
    if not INDEX_FILE.exists():
        return []

    try:
        lines = INDEX_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []

    dedup: Dict[str, Dict[str, Any]] = {}
    ordered_ids: List[str] = []

    # iterate newest->oldest and keep first occurrence of each session_id
    for ln in reversed(lines):
        if not ln.strip():
            continue
        try:
            row = json.loads(ln)
        except Exception:
            continue
        if not isinstance(row, dict):
            continue

        sid = str(row.get("session_id") or "").strip()
        if not sid:
            continue
        if sid in dedup:
            continue

        dedup[sid] = row
        ordered_ids.append(sid)

        if len(ordered_ids) >= max(1, min(limit, 200)):
            break

    return [dedup[sid] for sid in ordered_ids]
