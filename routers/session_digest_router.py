#!/usr/bin/env python3
"""
Bosly Gov v4 - Session Failure Digest Router (P1)
Provides a clean summary of why a session failed or ended with deploy failure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

SESSIONS_DIR = Path("/mnt/bosly/bosly-data/.data/governor/agent-sessions/sessions")


def _tail_text(path: Path, max_chars: int = 2500) -> str:
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    txt = txt.strip()
    if len(txt) <= max_chars:
        return txt
    return txt[-max_chars:]


def _load_session(session_id: str) -> Optional[Dict[str, Any]]:
    p = SESSIONS_DIR / f"{session_id}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _find_last_failed_check(session: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = session.get("artifacts") if isinstance(session.get("artifacts"), dict) else {}
    last_val = artifacts.get("last_validation") if isinstance(artifacts.get("last_validation"), dict) else {}

    checks = last_val.get("checks_run") if isinstance(last_val.get("checks_run"), list) else []
    failed_checks = [c for c in checks if isinstance(c, dict) and c.get("passed") is False]
    if not failed_checks:
        return {}

    last = failed_checks[-1]
    artifact_dir = Path(str(last_val.get("artifact_dir") or "")).resolve() if last_val.get("artifact_dir") else None
    stderr_tail = ""
    if artifact_dir and artifact_dir.exists():
        stderr_name = str(last.get("stderr_log") or "")
        if stderr_name:
            stderr_path = artifact_dir / stderr_name
            if stderr_path.exists():
                stderr_tail = _tail_text(stderr_path, max_chars=2500)

    return {
        "name": last.get("name"),
        "stage": last.get("stage"),
        "code": last.get("code"),
        "summary": last.get("summary"),
        "stderr_tail": stderr_tail,
        "validation_run_id": last_val.get("run_id"),
        "artifact_dir": str(last_val.get("artifact_dir") or ""),
    }


def _collect_error_messages(session: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    if session.get("error"):
        out.append(str(session.get("error")))

    result = session.get("result") if isinstance(session.get("result"), dict) else {}
    deploy = result.get("deploy") if isinstance(result.get("deploy"), dict) else {}
    if deploy and deploy.get("success") is False:
        err = str(deploy.get("stderr") or "").strip()
        if err:
            out.append(f"Deploy stderr: {err[:1000]}")

    events = session.get("events") if isinstance(session.get("events"), list) else []
    for ev in events[-30:]:
        if not isinstance(ev, dict):
            continue
        kind = str(ev.get("kind") or "")
        if kind in {"error", "failed", "attempt_failed", "deploy_failed", "apply_failed"}:
            msg = str(ev.get("message") or "").strip()
            if msg:
                out.append(msg)
    # de-dup preserve order
    seen = set()
    dedup = []
    for m in out:
        if m in seen:
            continue
        seen.add(m)
        dedup.append(m)
    return dedup[:20]


def get_failure_digest(session_id: str) -> Dict[str, Any]:
    session_id = (session_id or "").strip()
    if not session_id:
        return {"ok": False, "error": "Missing session_id."}

    session = _load_session(session_id)
    if not session:
        return {"ok": False, "error": f"Session not found: {session_id}"}

    status = str(session.get("status") or "")
    state = str(session.get("state") or "")
    result = session.get("result") if isinstance(session.get("result"), dict) else {}

    last_failed_check = _find_last_failed_check(session)
    errors = _collect_error_messages(session)

    return {
        "ok": True,
        "session_id": session_id,
        "status": status,
        "state": state,
        "failed_stage": result.get("failed_stage"),
        "error": session.get("error"),
        "last_failed_check": last_failed_check,
        "error_messages": errors,
        "summary": {
            "terminal": status in {"failed", "done_with_deploy_failure", "done"},
            "is_failure_like": status in {"failed", "done_with_deploy_failure"},
            "has_validation_failure": bool(last_failed_check),
            "has_deploy_failure": bool(result.get("failed_stage") == "deploy"),
        },
    }
