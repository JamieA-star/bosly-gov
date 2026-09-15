#!/usr/bin/env python3
"""
Bosly Gov v4 - Fix Router (Phase 3)
Extends Phase 2 API with auto_deploy/deploy_after_fix pass-through.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any, Dict

from routers.agent_router import (
    start_fix_session,
    start_feature_session,
    get_session_view,
    resume_session,
    recent_sessions,
)

PROJECT_ROOT = "/home/bosly_accord/bosly-1.0"
CONTEXT_PATH = "/tmp/bosly-context.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(handler, code: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as e:
        raise ValueError(f"Invalid JSON body: {e}")
    if not isinstance(data, dict):
        raise ValueError("JSON payload must be an object.")
    return data


def handle_current_file(handler) -> None:
    try:
        if not os.path.exists(CONTEXT_PATH):
            _json(handler, HTTPStatus.OK, {"ok": True, "current_file": None})
            return
        with open(CONTEXT_PATH, "r", encoding="utf-8", errors="replace") as f:
            ctx = json.load(f)
        current = None
        if isinstance(ctx, dict):
            current = ctx.get("current_file")
        _json(handler, HTTPStatus.OK, {"ok": True, "current_file": current})
    except Exception as e:
        _json(handler, HTTPStatus.OK, {"ok": True, "current_file": None, "error": str(e)})


def handle_fix(handler) -> None:
    try:
        data = _read_json_body(handler)
    except ValueError as e:
        _json(handler, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(e)})
        return

    mode = str(data.get("mode") or "").strip().lower()

    if mode == "get_session":
        sid = str(data.get("session_id") or "").strip()
        if not sid:
            _json(handler, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Missing session_id."})
            return
        res = get_session_view(sid)
        _json(handler, HTTPStatus.OK if res.get("ok") else HTTPStatus.NOT_FOUND, res)
        return

    if mode == "resume":
        sid = str(data.get("session_id") or "").strip()
        action = str(data.get("action") or "").strip().lower()
        if not sid:
            _json(handler, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Missing session_id."})
            return
        if action not in {"approve", "deny", "continue"}:
            _json(handler, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "action must be approve|deny|continue"})
            return
        res = resume_session(session_id=sid, action=action)
        _json(handler, HTTPStatus.OK if res.get("ok") else HTTPStatus.UNPROCESSABLE_ENTITY, res)
        return

    if mode == "recent":
        try:
            limit = int(data.get("limit", 25))
        except Exception:
            limit = 25
        limit = max(1, min(limit, 200))
        res = recent_sessions(limit=limit)
        _json(handler, HTTPStatus.OK, res)
        return

    # start new session
    # Supports:
    # - fix mode (default)
    # - feature mode: mode="feature" + feature_description
    if mode == "feature":
        file_rel = str(data.get("file") or "").strip()
        feature_description = str(data.get("feature_description") or "").strip()
        if not file_rel:
            _json(handler, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Missing file for feature mode."})
            return
        if not feature_description:
            _json(handler, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Missing feature_description for feature mode."})
            return
        res = start_feature_session(data)
    else:
        res = start_fix_session(data)
    status = HTTPStatus.OK if res.get("ok") else HTTPStatus.UNPROCESSABLE_ENTITY
    _json(handler, status, res)
