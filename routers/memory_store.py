#!/usr/bin/env python3
"""
Bosly Gov v4 - Memory Store (Phase 3)
Stores completed session outcomes and retrieves similar prior fixes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

MEMORY_DIR = Path("/mnt/bosly/bosly-data/.data/governor/memory")
MEMORY_FILE = MEMORY_DIR / "fix-memory.jsonl"
MAX_MEMORY_ROWS = 5000


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()[:16]

def _build_memory_entry_id(session_id: str, terminal_status: str, diff_hash: str) -> str:
    raw = f"{session_id}|{terminal_status}|{diff_hash}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:24]


def save_memory_entry(entry: Dict[str, Any]) -> None:
    _ensure()
    row = dict(entry)
    sid = str(row.get("session_id") or "")
    term = str(row.get("terminal_status") or "")
    diff_hash = str(row.get("diff_hash") or "")
    row["memory_entry_id"] = _build_memory_entry_id(sid, term, diff_hash)
    row.setdefault("saved_at", utc_now_iso())

    existing = _load_rows()
    existing_ids = {str(r.get("memory_entry_id") or "") for r in existing if isinstance(r, dict)}
    if row["memory_entry_id"] in existing_ids:
        return

    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # soft truncation when file grows too large
    try:
        lines = MEMORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > MAX_MEMORY_ROWS:
            keep = lines[-MAX_MEMORY_ROWS:]
            MEMORY_FILE.write_text("\n".join(keep) + "\n", encoding="utf-8")
    except Exception:
        pass


def _load_rows() -> List[Dict[str, Any]]:
    if not MEMORY_FILE.exists():
        return []
    out: List[Dict[str, Any]] = []
    try:
        for ln in MEMORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    except Exception:
        return []
    return out


def _tokenize(s: str) -> set:
    import re
    tokens = re.findall(r"[a-zA-Z0-9_]{3,}", _norm(s))
    return set(tokens)


def _score(query_file: str, query_error: str, row: Dict[str, Any]) -> float:
    score = 0.0
    file_q = _norm(query_file)
    err_q = _norm(query_error)

    row_file = _norm(str(row.get("file") or ""))
    row_err = _norm(str(row.get("error_signature") or ""))

    if file_q and row_file:
        if file_q == row_file:
            score += 6.0
        elif file_q.split("/")[-1] == row_file.split("/")[-1]:
            score += 4.0
        elif file_q.split(".")[0] in row_file:
            score += 2.0

    tq = _tokenize(err_q)
    tr = _tokenize(row_err)
    if tq and tr:
        inter = len(tq & tr)
        union = len(tq | tr)
        score += 8.0 * (inter / union if union else 0.0)

    if row.get("overall_passed") is True:
        score += 1.5
    if row.get("attempts_count"):
        try:
            ac = int(row.get("attempts_count"))
            if ac <= 2:
                score += 0.8
        except Exception:
            pass

    return score


def find_similar_fixes(file_rel: str, error_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    rows = _load_rows()
    scored = []
    for r in rows:
        s = _score(file_rel, error_text, r)
        if s <= 0:
            continue
        scored.append((s, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[Dict[str, Any]] = []
    for s, r in scored[: max(1, min(limit, 20))]:
        out.append({
            "score": round(s, 4),
            "session_id": r.get("session_id"),
            "file": r.get("file"),
            "error_signature": r.get("error_signature"),
            "attempts_count": r.get("attempts_count"),
            "overall_passed": r.get("overall_passed"),
            "diff_hash": r.get("diff_hash"),
            "summary": r.get("summary"),
            "saved_at": r.get("saved_at"),
        })
    return out


def build_memory_entry_from_session(session: Dict[str, Any]) -> Dict[str, Any]:
    inp = session.get("input") or {}
    result = session.get("result") or {}
    artifacts = session.get("artifacts") or {}
    attempts = session.get("attempts") or []

    initial_errors = artifacts.get("initial_errors") or []
    err_sig = "\n".join(initial_errors[:25]) if isinstance(initial_errors, list) else str(initial_errors)

    diff_text = str(result.get("proposed_diff") or "")
    terminal_status = str(session.get("status") or "")
    summary = f"{session.get('status')} / {session.get('state')} / attempts={len(attempts)}"

    return {
        "session_id": session.get("session_id"),
        "terminal_status": terminal_status,
        "file": inp.get("file"),
        "error_signature": err_sig[:4000],
        "attempts_count": len(attempts) if isinstance(attempts, list) else 0,
        "overall_passed": ((result.get("check_results") or {}).get("overall_passed") if isinstance(result.get("check_results"), dict) else None),
        "diff_hash": _hash_text(diff_text),
        "summary": summary,
    }
