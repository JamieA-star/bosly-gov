#!/usr/bin/env python3
"""
Bosly Gov v4 - File Access Router

Safe file-read and file-search endpoints for direct repository access.
Python 3.12+
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote

from routers.snippet_cache import (
    evict_expired,
    get_cache_key,
    get_cached_snippet,
    set_cached_snippet,
)

PROJECT_REPO_ROOTS = {
    "bosly-accord": Path("/home/bosly_accord/bosly-1.0").resolve(),
    "bosly-keep": Path("/home/bosly_accord/bosly-keep").resolve(),
    "bosly-gov": Path("/home/bosly_accord/bosly-gov").resolve(),
}

# Default to Accord for backward compatibility (non-project chat routes)
REPO_ROOT = PROJECT_REPO_ROOTS["bosly-accord"]


def set_repo_root(slug: str | None) -> None:
    """Set the active repo root based on project slug.

    Called by the LLM router before reading files so that per-project
    chat endpoints resolve paths against the correct codebase.
    """
    global REPO_ROOT
    if slug and slug in PROJECT_REPO_ROOTS:
        REPO_ROOT = PROJECT_REPO_ROOTS[slug]


def get_repo_root() -> Path:
    """Return the currently active repo root."""
    return REPO_ROOT

MAX_FILE_SIZE_BYTES = 200 * 1024
MAX_LINE_RANGE = 500
MAX_SEARCH_RESULTS = 100
MAX_REGEX_PATTERN_LEN = 500
MAX_PATH_FILTER_LEN = 500

DENY_DIR_NAMES = {
    "node_modules",
    ".next",
    ".git",
    "__pycache__",
    ".turbo",
    "dist",
    "build",
}
DENY_FILE_REGEXES = [
    re.compile(r"(^|/)\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"(^|/).*\.pem$", re.IGNORECASE),
    re.compile(r"(^|/).*\.key$", re.IGNORECASE),
    re.compile(r"(^|/)id_rsa(\..+)?$", re.IGNORECASE),
    re.compile(r"(^|/)id_ed25519(\..+)?$", re.IGNORECASE),
    re.compile(r"(^|/).*secret.*$", re.IGNORECASE),
    re.compile(r"(^|/).*token.*$", re.IGNORECASE),
    re.compile(r"(^|/).*credentials.*$", re.IGNORECASE),
]


def _json(handler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _norm_rel_path(path: str) -> str:
    p = (path or "").strip().replace("\\", "/")
    while "//" in p:
        p = p.replace("//", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


def is_allowed_repo_path(path: str) -> tuple[bool, str]:
    rel = _norm_rel_path(path)
    if not rel:
        return False, "Path is required."
    if os.path.isabs(rel):
        return False, "Absolute paths are not allowed."
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if not parts:
        return False, "Invalid path."
    if any(part == ".." for part in parts):
        return False, "Path traversal is not allowed."
    if any(part in DENY_DIR_NAMES for part in parts):
        return False, "Path is in a restricted directory."
    rel_joined = "/".join(parts)
    lower_rel = rel_joined.lower()
    for rx in DENY_FILE_REGEXES:
        if rx.search(lower_rel):
            return False, "Path is restricted by security policy."
    return True, "ok"


def safe_resolve_repo_path(rel_path: str) -> Path | None:
    allowed, _ = is_allowed_repo_path(rel_path)
    if not allowed:
        return None
    rel = _norm_rel_path(rel_path).lstrip("/")
    candidate = (REPO_ROOT / rel).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError:
        return None
    current = REPO_ROOT
    for part in rel.split("/"):
        if not part or part == ".":
            continue
        current = current / part
        try:
            if current.exists() and current.is_symlink():
                target = current.resolve()
                target.relative_to(REPO_ROOT)
        except Exception:
            return None
    return candidate


def _coerce_line_range(start: int | None, end: int | None) -> tuple[int | None, int | None, str | None]:
    if start is not None:
        try:
            start = int(start)
        except Exception:
            return None, None, "Invalid start line."
        if start < 1:
            return None, None, "Start line must be >= 1."
    if end is not None:
        try:
            end = int(end)
        except Exception:
            return None, None, "Invalid end line."
        if end < 1:
            return None, None, "End line must be >= 1."
    if start is not None and end is not None and end < start:
        return None, None, "End line must be >= start line."
    if start is not None and end is not None:
        if (end - start + 1) > MAX_LINE_RANGE:
            return None, None, f"Line range too large (max {MAX_LINE_RANGE})."
    return start, end, None


def read_file_lines(rel_path: str, start: int | None, end: int | None) -> dict:
    allowed, reason = is_allowed_repo_path(rel_path)
    if not allowed:
        return {"ok": False, "error": reason}
    file_path = safe_resolve_repo_path(rel_path)
    if file_path is None:
        return {"ok": False, "error": "Unsafe or invalid path."}
    if not file_path.exists() or not file_path.is_file():
        return {"ok": False, "error": "File not found."}
    try:
        size = file_path.stat().st_size
    except Exception:
        return {"ok": False, "error": "Unable to stat file."}
    if size > MAX_FILE_SIZE_BYTES:
        return {"ok": False, "error": f"File too large (>{MAX_FILE_SIZE_BYTES} bytes)."}
    start, end, range_err = _coerce_line_range(start, end)
    if range_err:
        return {"ok": False, "error": range_err}
    rel_resolved = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
    mtime = file_path.stat().st_mtime
    key = get_cache_key(rel_resolved, start, end, mtime)
    cached = get_cached_snippet(key)
    if cached is not None:
        out = dict(cached)
        out["cache_hit"] = True
        return out
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "error": f"Failed to read file: {e}"}
    lines = text.splitlines()
    total_lines = len(lines)
    if start is None and end is None:
        s_idx = 0
        e_idx = min(total_lines, MAX_LINE_RANGE)
    else:
        s_idx = (start - 1) if start is not None else 0
        e_idx = end if end is not None else min(total_lines, s_idx + MAX_LINE_RANGE)
    s_idx = max(0, min(s_idx, total_lines))
    e_idx = max(s_idx, min(e_idx, total_lines))
    snippet_lines = lines[s_idx:e_idx]
    snippet = "\n".join(snippet_lines)
    result = {
        "ok": True,
        "path": rel_resolved,
        "start_line": s_idx + 1 if total_lines > 0 else 1,
        "end_line": e_idx,
        "total_lines": total_lines,
        "size_bytes": size,
        "snippet": snippet,
        "truncated": (e_idx - s_idx) < total_lines,
        "cache_hit": False,
    }
    set_cached_snippet(key, result, ttl_s=300)
    return result


def _is_denied_path_obj(path_obj: Path) -> bool:
    try:
        rel = str(path_obj.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except Exception:
        return True
    parts = rel.split("/")
    if any(p in DENY_DIR_NAMES for p in parts):
        return True
    low = rel.lower()
    return any(rx.search(low) for rx in DENY_FILE_REGEXES)


def search_files_glob(pattern: str, limit: int = 100) -> dict:
    patt = (pattern or "").strip()
    if not patt:
        return {"ok": False, "error": "Pattern is required."}
    if os.path.isabs(patt) or ".." in patt.replace("\\", "/").split("/"):
        return {"ok": False, "error": "Unsafe glob pattern."}
    try:
        limit = int(limit)
    except Exception:
        limit = 20
    limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    matches: list[str] = []
    scanned = 0
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in DENY_DIR_NAMES]
        root_path = Path(root)
        for name in files:
            scanned += 1
            p = root_path / name
            if _is_denied_path_obj(p):
                continue
            rel = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
            if fnmatch.fnmatch(rel, patt):
                matches.append(rel)
                if len(matches) >= limit:
                    return {"ok": True, "pattern": patt, "matches": matches, "truncated": True, "scanned_files": scanned}
    return {"ok": True, "pattern": patt, "matches": matches, "truncated": False, "scanned_files": scanned}


def search_files_regex(pattern: str, path_filter: str | None, limit: int = 100) -> dict:
    patt = (pattern or "").strip()
    if not patt:
        return {"ok": False, "error": "Regex pattern is required."}
    if len(patt) > MAX_REGEX_PATTERN_LEN:
        return {"ok": False, "error": "Regex pattern too long."}
    pf = _norm_rel_path(path_filter or "")
    if pf and len(pf) > MAX_PATH_FILTER_LEN:
        return {"ok": False, "error": "Path filter too long."}
    if pf and (os.path.isabs(pf) or ".." in pf.split("/")):
        return {"ok": False, "error": "Unsafe path_filter."}
    try:
        rx = re.compile(patt, re.IGNORECASE)
    except re.error as e:
        return {"ok": False, "error": f"Invalid regex: {e}"}
    try:
        limit = int(limit)
    except Exception:
        limit = 20
    limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    matches: list[str] = []
    scanned = 0
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in DENY_DIR_NAMES]
        root_path = Path(root)
        for name in files:
            scanned += 1
            p = root_path / name
            if _is_denied_path_obj(p):
                continue
            rel = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
            if pf and not rel.startswith(pf):
                continue
            if rx.search(rel):
                matches.append(rel)
                if len(matches) >= limit:
                    return {
                        "ok": True,
                        "pattern": patt,
                        "path_filter": pf or None,
                        "matches": matches,
                        "truncated": True,
                        "scanned_files": scanned,
                    }
    return {
        "ok": True,
        "pattern": patt,
        "path_filter": pf or None,
        "matches": matches,
        "truncated": False,
        "scanned_files": scanned,
    }


def handle_api_file_read(handler) -> None:
    try:
        parsed = parse_qs((unquote(handler.path.split("?", 1)[1]) if "?" in handler.path else ""))
    except Exception:
        parsed = {}
    rel_path = ((parsed.get("path", [""])[0]) or "").strip()
    start_raw = ((parsed.get("start", [""])[0]) or "").strip()
    end_raw = ((parsed.get("end", [""])[0]) or "").strip()
    start = int(start_raw) if start_raw.isdigit() else None
    end = int(end_raw) if end_raw.isdigit() else None
    evict_expired()
    result = read_file_lines(rel_path=rel_path, start=start, end=end)
    status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
    _json(handler, status, result)


def handle_api_file_search(handler, query: str) -> None:
    q = parse_qs(query or "")
    mode = str((q.get("mode", ["glob"])[0] or "glob")).strip().lower()
    pattern = str((q.get("pattern", [""])[0] or "")).strip()
    path_filter = str((q.get("path_filter", [""])[0] or "")).strip() or None
    limit_raw = str((q.get("limit", [str(MAX_SEARCH_RESULTS)])[0] or str(MAX_SEARCH_RESULTS))).strip()
    try:
        limit = int(limit_raw)
    except Exception:
        limit = MAX_SEARCH_RESULTS
    evict_expired()
    if mode == "glob":
        result = search_files_glob(pattern=pattern, limit=limit)
    elif mode == "regex":
        result = search_files_regex(pattern=pattern, path_filter=path_filter, limit=limit)
    else:
        result = {"ok": False, "error": "Invalid mode. Use 'glob' or 'regex'."}
    status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
    _json(handler, status, result)
