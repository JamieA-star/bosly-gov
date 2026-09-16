#!/usr/bin/env python3
"""
Bosly Gov v4 - Consent Store (with transactional apply + backup cleanup P4)
"""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PENDING_DIR = Path("/mnt/bosly/bosly-data/governor/pending")
PENDING_FILE = PENDING_DIR / "pending.json"
LOG_FILE = PENDING_DIR / "consent-log.jsonl"

ALLOWED_WRITE_ROOTS = [
    Path("/home/bosly_accord/bosly-1.0").resolve(),
    Path("/home/bosly_accord/bosly-keep").resolve(),
    Path("/home/bosly_accord/bosly-gov").resolve(),
]

DENY_PATH_PATTERNS = [
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"(^|/)id_rsa(\.|$)"),
    re.compile(r"(^|/)authorized_keys$"),
    re.compile(r"(^|/)shadow$"),
    re.compile(r"(^|/)passwd$"),
    re.compile(r"(^|/)etc/"),
    # Extended 16 Sept 2026 — standard sensitive set
    re.compile(r"\.pem$"),
    re.compile(r"\.p12$"),
    re.compile(r"\.pfx$"),
    re.compile(r"(^|/)\.ssh/"),
    re.compile(r"(^|/)\.gnupg/"),
    re.compile(r"(^|/)\.aws/credentials$"),
    re.compile(r"(^|/)\.npmrc$"),
    re.compile(r"(^|/)\.pypirc$"),
    re.compile(r"(^|/)\.git/config$"),
    re.compile(r"(^|/)credentials$"),
]

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
PENDING_TTL_HOURS = 24
BACKUP_RETENTION_DAYS = 7
BACKUP_SUFFIX = ".bosly.bak"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _ensure_dirs() -> None:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)


def _short_token(nbytes: int = 6) -> str:
    return secrets.token_urlsafe(nbytes).replace("-", "").replace("_", "")[:10]


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _append_log(event: Dict[str, Any]) -> None:
    _ensure_dirs()
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _read_pending_file() -> Optional[Dict[str, Any]]:
    if not PENDING_FILE.exists():
        return None
    try:
        with PENDING_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None

        created_at = str(data.get("created_at") or "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if _now() - dt > timedelta(hours=PENDING_TTL_HOURS):
                    _append_log({"ts": _now_iso(), "event": "expired", "token": data.get("token")})
                    _clear_pending_file()
                    return None
            except Exception:
                pass

        return data
    except Exception:
        return None


def _clear_pending_file() -> None:
    try:
        if PENDING_FILE.exists():
            PENDING_FILE.unlink()
    except Exception:
        pass


def _is_allowed_path(path_str: str) -> Tuple[bool, str]:
    if not path_str or not isinstance(path_str, str):
        return False, "Missing file path."
    p = Path(path_str)
    if not p.is_absolute():
        return False, f"Path must be absolute: {path_str}"
    try:
        resolved = p.resolve()
    except Exception:
        return False, f"Invalid path: {path_str}"

    for pat in DENY_PATH_PATTERNS:
        if pat.search(str(resolved)):
            return False, f"Blocked sensitive path: {resolved}"

    for root in ALLOWED_WRITE_ROOTS:
        try:
            resolved.relative_to(root)
            return True, ""
        except ValueError:
            continue
    return False, f"Path outside allowed roots: {resolved}"


def _safe_write_file(path_str: str, content: str, mode: str = "overwrite") -> Dict[str, Any]:
    ok, reason = _is_allowed_path(path_str)
    if not ok:
        return {"ok": False, "path": path_str, "error": reason}

    encoded = (content or "").encode("utf-8", errors="replace")
    if len(encoded) > MAX_FILE_SIZE_BYTES:
        return {
            "ok": False,
            "path": path_str,
            "error": f"Content too large ({len(encoded)} bytes > {MAX_FILE_SIZE_BYTES}).",
        }

    target = Path(path_str)
    target.parent.mkdir(parents=True, exist_ok=True)

    backup_path = str(target) + BACKUP_SUFFIX
    try:
        old_content = ""
        if target.exists():
            old_content = target.read_text(encoding="utf-8", errors="replace")
            Path(backup_path).write_text(old_content, encoding="utf-8", errors="replace")

        if mode == "append":
            with target.open("a", encoding="utf-8") as f:
                f.write(content or "")
        else:
            with target.open("w", encoding="utf-8") as f:
                f.write(content or "")
    except Exception as e:
        return {"ok": False, "path": path_str, "error": str(e)}

    return {
        "ok": True,
        "path": path_str,
        "bytes_written": len(encoded),
        "mode": mode,
        "backup_path": backup_path if os.path.exists(backup_path) else None,
    }


def _cleanup_old_backups() -> Dict[str, Any]:
    cutoff_epoch = time.time() - (BACKUP_RETENTION_DAYS * 24 * 60 * 60)
    removed = 0
    errors = 0
    scanned = 0

    roots = [r for r in ALLOWED_WRITE_ROOTS if r.exists() and r.is_dir()]
    for root in roots:
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".next", "dist", "build", "__pycache__"}]
            for f in files:
                if not f.endswith(BACKUP_SUFFIX):
                    continue
                scanned += 1
                p = Path(base) / f
                try:
                    st = p.stat()
                    if st.st_mtime < cutoff_epoch:
                        p.unlink(missing_ok=True)
                        removed += 1
                except Exception:
                    errors += 1

    return {"scanned": scanned, "removed": removed, "errors": errors, "retention_days": BACKUP_RETENTION_DAYS}


def _extract_file_ops(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    ops: List[Dict[str, Any]] = []
    raw_ops = payload.get("file_ops")

    if isinstance(raw_ops, list):
        for op in raw_ops:
            if not isinstance(op, dict):
                continue
            path = str(op.get("path", "")).strip()
            content = op.get("content", "")
            mode = str(op.get("mode", "overwrite")).strip().lower()
            if mode not in ("overwrite", "append"):
                mode = "overwrite"
            if path:
                ops.append({"path": path, "content": str(content), "mode": mode})
        if ops:
            return ops

    proposed = str(payload.get("proposed_text", "") or "")
    if not proposed:
        return ops

    pattern = re.compile(r"(?ms)^\s*FILE:\s*(?P<path>/[^\n]+)\n\s*<<<\n(?P<content>.*?)\n\s*>>>\s*$")
    for match in pattern.finditer(proposed):
        path = match.group("path").strip()
        content = match.group("content")
        ops.append({"path": path, "content": content, "mode": "overwrite"})
    return ops


def _public_pending_view(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = data.get("payload", {}) if isinstance(data.get("payload"), dict) else {}
    file_ops = _extract_file_ops(payload)

    return {
        "token": data.get("token"),
        "created_at": data.get("created_at"),
        "expires_at": data.get("expires_at"),
        "summary": data.get("summary") or "Pending action awaiting consent.",
        "type": data.get("type"),
        "request_id": data.get("request_id"),
        "has_file_ops": bool(file_ops),
        "file_ops_preview": [{"path": op.get("path"), "mode": op.get("mode", "overwrite")} for op in file_ops[:10]],
        "meta": payload.get("meta", {}) if isinstance(payload.get("meta"), dict) else {},
    }


def create_pending_action(payload: Dict[str, Any]) -> Dict[str, str]:
    _ensure_dirs()
    token = _short_token()
    created_at = _now()
    expires_at = created_at + timedelta(hours=PENDING_TTL_HOURS)

    record = {
        "token": token,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "type": str(payload.get("type", "pending_action")),
        "summary": str(payload.get("summary", "Pending action awaiting consent.")),
        "request_id": str(payload.get("request_id", "")),
        "payload": payload,
    }

    _atomic_write_json(PENDING_FILE, record)
    _append_log({
        "ts": _now_iso(),
        "event": "created",
        "token": token,
        "summary": record["summary"],
        "request_id": record["request_id"],
    })
    return {"token": token}


def get_pending_action() -> Optional[Dict[str, Any]]:
    data = _read_pending_file()
    if not data:
        return None
    return _public_pending_view(data)


def approve_pending_action(token: str) -> Dict[str, Any]:
    data = _read_pending_file()
    if not data:
        return {"ok": False, "error": "No pending action."}
    if str(data.get("token")) != str(token):
        return {"ok": False, "error": "Invalid token."}

    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        return {"ok": False, "error": "Invalid pending payload."}

    file_ops = _extract_file_ops(payload)
    if not file_ops:
        _clear_pending_file()
        _append_log({
            "ts": _now_iso(),
            "event": "approved_noop",
            "token": token,
            "reason": "No safe file operations parsed.",
        })
        return {
            "ok": False,
            "action": "approve",
            "token": token,
            "error": "No executable safe file operations found in pending action.",
            "cleared": True,
        }

    results: List[Dict[str, Any]] = []
    backups: List[Dict[str, Any]] = []
    all_ok = True

    # Pre-validation + snapshot
    for op in file_ops:
        path_str = op.get("path", "")
        ok, reason = _is_allowed_path(path_str)
        if not ok:
            results.append({"ok": False, "path": path_str, "error": reason})
            all_ok = False
            continue
        target = Path(path_str)
        prev_exists = target.exists()
        prev_content = ""
        if prev_exists:
            try:
                prev_content = target.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                results.append({"ok": False, "path": path_str, "error": f"Failed reading existing file for backup: {e}"})
                all_ok = False
                continue
        backups.append({"path": path_str, "existed": prev_exists, "content": prev_content})

    if not all_ok:
        _clear_pending_file()
        cleanup = _cleanup_old_backups()
        _append_log({
            "ts": _now_iso(),
            "event": "approved_failed_precheck",
            "token": token,
            "results": results,
            "backup_cleanup": cleanup,
        })
        return {
            "ok": False,
            "action": "approve",
            "token": token,
            "executed": 0,
            "results": results,
            "rolled_back": True,
            "backup_cleanup": cleanup,
            "cleared": True,
        }

    # Apply all writes
    apply_failed = False
    failure_reason = ""
    for op in file_ops:
        result = _safe_write_file(path_str=op["path"], content=op["content"], mode=op.get("mode", "overwrite"))
        results.append(result)
        if not result.get("ok"):
            apply_failed = True
            all_ok = False
            failure_reason = str(result.get("error") or "write failed")
            break

    rolled_back = False
    if apply_failed:
        rolled_back = True
        for b in backups:
            p = Path(b["path"])
            try:
                if b["existed"]:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(b["content"], encoding="utf-8", errors="replace")
                else:
                    if p.exists():
                        p.unlink()
            except Exception as e:
                results.append({"ok": False, "path": b["path"], "error": f"Rollback failed: {e}"})

    _clear_pending_file()
    cleanup = _cleanup_old_backups()
    _append_log({
        "ts": _now_iso(),
        "event": "approved",
        "token": token,
        "ok": all_ok,
        "file_ops_count": len(file_ops),
        "rolled_back": rolled_back,
        "backup_cleanup": cleanup,
        "results": results,
    })

    return {
        "ok": all_ok,
        "action": "approve",
        "token": token,
        "executed": len(file_ops) if all_ok else 0,
        "results": results,
        "rolled_back": rolled_back,
        "backup_cleanup": cleanup,
        "error": None if all_ok else failure_reason,
        "cleared": True,
    }


def deny_pending_action(token: str) -> Dict[str, Any]:
    data = _read_pending_file()
    if not data:
        return {"ok": False, "error": "No pending action."}
    if str(data.get("token")) != str(token):
        return {"ok": False, "error": "Invalid token."}

    _clear_pending_file()
    _append_log({
        "ts": _now_iso(),
        "event": "denied",
        "token": token,
        "request_id": data.get("request_id", ""),
    })
    return {"ok": True, "action": "deny", "token": token, "cleared": True}
