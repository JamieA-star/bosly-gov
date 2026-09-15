#!/usr/bin/env python3
"""
Bosly Gov v4 - Web Backend Server
(Updated with P1 failure digest endpoint)
"""
from __future__ import annotations

import json
import logging
import mimetypes
import posixpath
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse, unquote, parse_qs

try:
    from routers.command_router import route_command
except Exception as e:
    route_command = None
    _command_import_error = e
else:
    _command_import_error = None

try:
    from routers.llm_router import route_llm, route_llm_stream
except Exception as e:
    route_llm = None
    route_llm_stream = None
    _llm_import_error = e
else:
    _llm_import_error = None

try:
    from routers.memory_consolidator import consolidate_messages
except Exception as e:
    consolidate_messages = None
    _consolidator_import_error = e
else:
    _consolidator_import_error = None

try:
    from routers.deploy_after_fix import deploy_after_approval
except Exception as e:
    deploy_after_approval = None
    _deploy_import_error = e
else:
    _deploy_import_error = None

try:
    from routers.consent_store import get_pending_action, approve_pending_action, deny_pending_action
except Exception as e:
    get_pending_action = None
    approve_pending_action = None
    deny_pending_action = None
    _consent_import_error = e
else:
    _consent_import_error = None

try:
    from routers.observability import (
        record_interaction,
        get_metrics as get_observability_metrics,
        get_recent_interactions,
        get_eval_tasks,
        run_eval,
    )
except Exception as e:
    record_interaction = None
    get_observability_metrics = None
    get_recent_interactions = None
    get_eval_tasks = None
    run_eval = None
    _observability_import_error = e
else:
    _observability_import_error = None

try:
    from routers.metrics_router import get_metrics
except Exception as e:
    get_metrics = None
    _metrics_import_error = e
else:
    _metrics_import_error = None

try:
    from routers.memory_store import find_similar_fixes
except Exception as e:
    find_similar_fixes = None
    _memory_import_error = e
else:
    _memory_import_error = None

try:
    from routers.session_digest_router import get_failure_digest
except Exception as e:
    get_failure_digest = None
    _digest_import_error = e
else:
    _digest_import_error = None
try:
    from routers.file_access_router import handle_api_file_read, handle_api_file_search
except Exception as e:
    handle_api_file_read = None
    handle_api_file_search = None
    _file_access_import_error = e
else:
    _file_access_import_error = None

try:
    from routers.context_orchestrator import run_chat_once, run_chat_stream
except Exception as e:
    run_chat_once = None
    run_chat_stream = None
    _orchestrator_import_error = e
else:
    _orchestrator_import_error = None

try:
    from routers.project_graph import (
        build_graph,
        add_node as graph_add_node,
        add_edge as graph_add_edge,
        query_graph,
        get_related_entities,
        get_project_summary,
    )
except Exception as e:
    _project_graph_import_error = e
else:
    _project_graph_import_error = None

try:
    from routers.consent_flow import (
        create_pending_action as ux_create_pending_action,
        get_pending_action as ux_get_pending_action,
        approve_action as ux_approve_action,
        deny_action as ux_deny_action,
        list_pending_actions as ux_list_pending_actions,
        get_action_timeline as ux_get_action_timeline,
        approve_action_files as ux_approve_action_files,
    )
except Exception as e:
    _consent_flow_import_error = e
else:
    _consent_flow_import_error = None

try:
    from routers.error_types import (
        BoslyError,
        ValidationError,
        UnknownError,
        normalize_exception,
    )
except Exception as e:
    _error_types_import_error = e
else:
    _error_types_import_error = None

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 3102,
    "llm_script_path": "/usr/local/bin/bosly-call-llm.py",
    "prompt_path": "/usr/local/bin/bosly-prompt-oneline.txt",
    "commands_glob": "/usr/local/bin/bosly-*",
    "log_level": "INFO",
}

@dataclass
class AppState:
    config: Dict[str, Any]
    started_at: float
    version: str = "4.4.0"

def load_config() -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if not CONFIG_PATH.exists():
        return config
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            config.update(data)
    except Exception as e:
        logging.warning("Failed to load config.json, using defaults: %s", e)
    requested_host = str(config.get("host", "127.0.0.1")).strip()
    if requested_host not in ("127.0.0.1", "localhost", "::1"):
        logging.warning("Host '%s' is not allowed. Forcing localhost (127.0.0.1).", requested_host)
        config["host"] = "127.0.0.1"
    if config.get("host") == "localhost":
        config["host"] = "127.0.0.1"
    try:
        port = int(config.get("port", 3102))
    except Exception:
        port = 3102
    if port < 1 or port > 65535:
        port = 3102
    config["port"] = port
    return config

PROJECTS_BASE = Path("/mnt/bosly/bosly-data/copilot-knowledge")
ACCORD_PATH = Path("/mnt/bosly/bosly-data/.data/governor/bosly-accord.md")


def _validate_slug(slug: str) -> bool:
    if not slug or len(slug) > 50:
        return False
    return all(c.isalnum() or c == "-" for c in slug) and slug == slug.lower()


def _get_project_path(slug: str) -> Path:
    return PROJECTS_BASE / slug


def _get_report_path(slug: str, year: str) -> Path:
    return _get_project_path(slug) / "reports" / f"{year}.md"


def _get_chat_path(slug: str) -> Path:
    return _get_project_path(slug) / "chat.json"


def _get_memory_path(slug: str) -> Path:
    return _get_project_path(slug) / "memory.json"


import re as _re


def _redact_sensitive(text: str) -> str:
    """Remove anything that looks like a secret before sending to LLM."""
    if not text:
        return text

    patterns = [
        # API keys
        (r"(sk|pk|rk)_[a-zA-Z0-9]{16,}", "[REDACTED_API_KEY]"),
        # AWS keys
        (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
        # Generic KEY=VALUE where value looks secret
        (r"(?i)(password|secret|token|key|api[_-]?key)\s*=\s*[^\s\n]+", "[REDACTED_CREDENTIAL]"),
        # Bearer tokens
        (r"Bearer\s+[a-zA-Z0-9._-]+", "[REDACTED_TOKEN]"),
        # Private keys
        (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
        # Long hex/base64 strings (likely secrets)
        (r"\b[a-f0-9]{32,}\b", "[REDACTED_HEX]"),
    ]

    for pattern, replacement in patterns:
        text = _re.sub(pattern, replacement, text)

    return text


def _read_json_file(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def _write_json_file(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0") or "0")
    if content_length == 0:
        return {}
    raw = handler.rfile.read(content_length)
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON: {e}")
    if not isinstance(data, dict):
        raise ValueError("JSON payload must be an object.")
    return data

def safe_static_path(url_path: str) -> Optional[Path]:
    if url_path in ("/", ""):
        target = STATIC_DIR / "index.html"
        return target if target.exists() else None
    normalized = posixpath.normpath(unquote(url_path))
    normalized = normalized.lstrip("/")
    if normalized.startswith("api/"):
        return None
    candidate = (STATIC_DIR / normalized).resolve()
    try:
        candidate.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return None
    if candidate.exists() and candidate.is_file():
        return candidate
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file
    return None

class BoslyHandler(BaseHTTPRequestHandler):
    server_version = "BoslyGovV4/1.4"

    def _state(self) -> AppState:
        return self.server.app_state

    def log_message(self, fmt: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)

    def _send_json(self, payload: Dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_envelope(self, err: BoslyError) -> None:
        self._send_json(err.to_envelope(), status=err.status)

    def _send_file(self, file_path: Path) -> None:
        ctype, _ = mimetypes.guess_type(str(file_path))
        if not ctype:
            ctype = "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8" if ctype.startswith("text/") else ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _start_sse(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _write_sse(self, event: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False)
        blob = f"event: {event}\ndata: {payload}\n\n".encode("utf-8")
        self.wfile.write(blob)
        self.wfile.flush()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            self.handle_api_health()
            return
        if path == "/api/pending":
            self.handle_api_pending()
            return
        if path == "/api/context/current-file":
            self.handle_current_file()
            return
        if path == "/api/metrics":
            self.handle_api_metrics()
            return
        if path == "/api/memory/similar":
            self.handle_api_memory_similar(parsed.query)
            return
        if path == "/api/session/failure-digest":
            self.handle_api_failure_digest(parsed.query)
        if path == "/api/files/read":
            if handle_api_file_read is None:
                self._send_json(
                    {"ok": False, "error": f'file_access_router unavailable: {_file_access_import_error}'},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            handle_api_file_read(self)
            return
        if path == "/api/files/search":
            if handle_api_file_search is None:
                self._send_json(
                    {"ok": False, "error": f'file_access_router unavailable: {_file_access_import_error}'},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            handle_api_file_search(self, parsed.query)
        if path == "/api/consent/actions":
            self.handle_api_consent_actions_list()
            return
        if path.startswith("/api/consent/actions/") and path.endswith("/timeline"):
            parts = path.split("/")
            if len(parts) == 6:
                self.handle_api_consent_timeline(parts[4])
                return
        if path.startswith("/api/consent/actions/"):
            parts = path.split("/")
            if len(parts) == 5:
                self.handle_api_consent_action_get(parts[4])
        if path.startswith("/api/graph/"):
            parts = path.split("/")
            if len(parts) == 5 and parts[4] == "build":
                self.handle_api_graph_build(parts[3])
                return
            if len(parts) == 5 and parts[4] == "node":
                self.handle_api_graph_add_node(parts[3])
                return
            if len(parts) == 5 and parts[4] == "edge":
                self.handle_api_graph_add_edge(parts[3])
        if path == "/api/observability/metrics":
            self.handle_api_observability_metrics()
            return
        if path == "/api/observability/interactions":
            self.handle_api_observability_interactions(parsed.query)
            return
        if path == "/api/observability/eval/tasks":
            self.handle_api_observability_eval_tasks()
            return
        if path.startswith("/api/graph/"):
            parts = path.split("/")
            if len(parts) == 5 and parts[4] == "summary":
                self.handle_api_graph_summary(parts[3])
                return
            if len(parts) == 5 and parts[4] == "query":
                self.handle_api_graph_query(parts[3], parsed.query)
                return
            if len(parts) == 6 and parts[4] == "related":
                self.handle_api_graph_related(parts[3], unquote(parts[5]))
                return
        if path == "/api/projects":
            self._handle_projects_list()
            return
        if path.startswith("/api/project/"):
            parts = path.split("/")
            if len(parts) >= 5 and parts[4] == "reports" and len(parts) == 5:
                self._handle_project_reports_list(parts[3])
                return
            if len(parts) >= 6 and parts[4] == "report" and len(parts) == 6:
                self._handle_project_report_get(parts[3], parts[5])
                return
            if len(parts) >= 5 and parts[4] == "chat" and len(parts) == 5:
                self._handle_project_chat_get(parts[3])
                return
            if len(parts) >= 5 and parts[4] == "memory" and len(parts) == 5:
                self._handle_project_memory_get(parts[3])
                return
        file_path = safe_static_path(path)
        if file_path:
            try:
                self._send_file(file_path)
            except Exception as e:
                logging.exception("Failed serving static file: %s", e)
                self._send_json({"ok": False, "error": "Failed to serve static file."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json({"ok": False, "error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/chat":
            self.handle_api_chat()
            return
        if path == "/api/chat/stream":
            self.handle_api_chat_stream()
            return
        if path == "/api/consent":
            self.handle_api_consent()
            return
        if path == "/api/fix":
            self.handle_api_fix()
            return
        if path == "/api/projects":
            self._handle_project_create()
            return
        if path.startswith("/api/project/"):
            parts = path.split("/")
            if len(parts) >= 6 and parts[4] == "report" and parts[5] == "new" and len(parts) == 6:
                self._handle_project_report_new(parts[3])
        if path == "/api/consent/actions":
            self.handle_api_consent_action_create()
            return
        if path.startswith("/api/consent/actions/") and path.endswith("/approve"):
            parts = path.split("/")
            if len(parts) == 6:
                self.handle_api_consent_action_approve(parts[4])
                return
        if path.startswith("/api/consent/actions/") and path.endswith("/deny"):
            parts = path.split("/")
            if len(parts) == 6:
                self.handle_api_consent_action_deny(parts[4])
                return
        if path.startswith("/api/consent/actions/") and path.endswith("/review"):
            parts = path.split("/")
            if len(parts) == 6:
                self.handle_api_consent_action_review(parts[4])
                return
        if path.startswith("/api/graph/"):
            parts = path.split("/")
            if len(parts) == 5 and parts[4] == "build":
                self.handle_api_graph_build(parts[3])
                return
            if len(parts) == 5 and parts[4] == "node":
                self.handle_api_graph_add_node(parts[3])
                return
            if len(parts) == 5 and parts[4] == "edge":
                self.handle_api_graph_add_edge(parts[3])
                return
        if path == "/api/observability/interaction":
            self.handle_api_observability_record()
            return
        if path == "/api/observability/eval/run":
            self.handle_api_observability_eval_run()
            return
        if path.startswith("/api/project/"):
            parts = path.split("/")
            if len(parts) >= 5 and parts[4] == "chat" and len(parts) == 5:
                self._handle_project_chat_post(parts[3])
                return
            if len(parts) >= 6 and parts[4] == "chat" and parts[5] == "stream" and len(parts) == 6:
                self._handle_project_chat_stream(parts[3])
                return
        self._send_json({"ok": False, "error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/project/"):
            parts = path.split("/")
            if len(parts) >= 6 and parts[4] == "report" and len(parts) == 6:
                self._handle_project_report_put(parts[3], parts[5])
                return
        self._send_json({"ok": False, "error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def handle_current_file(self) -> None:
        try:
            from routers.fix_router import handle_current_file as hcf
            hcf(self)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_fix(self) -> None:
        try:
            from routers.fix_router import handle_fix as hf
            hf(self)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_metrics(self) -> None:
        if get_metrics is None:
            self._send_json({"ok": False, "error": f"metrics_router unavailable: {_metrics_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            self._send_json(get_metrics(limit=500), status=HTTPStatus.OK)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_memory_similar(self, query: str) -> None:
        if find_similar_fixes is None:
            self._send_json({"ok": False, "error": f"memory_store unavailable: {_memory_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        q = parse_qs(query or "")
        file_rel = (q.get("file", [""])[0] or "").strip()
        error_text = (q.get("error", [""])[0] or "").strip()
        try:
            limit = int((q.get("limit", ["5"])[0] or "5").strip())
        except Exception:
            limit = 5
        limit = max(1, min(limit, 20))
        try:
            items = find_similar_fixes(file_rel=file_rel, error_text=error_text, limit=limit)
            self._send_json({"ok": True, "items": items}, status=HTTPStatus.OK)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_failure_digest(self, query: str) -> None:
        if get_failure_digest is None:
            self._send_json({"ok": False, "error": f"session_digest_router unavailable: {_digest_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        q = parse_qs(query or "")
        session_id = (q.get("session_id", [""])[0] or "").strip()
        if not session_id:
            self._send_json({"ok": False, "error": "Missing session_id query param."}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            out = get_failure_digest(session_id=session_id)
            self._send_json(out, status=HTTPStatus.OK if out.get("ok") else HTTPStatus.NOT_FOUND)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_health(self) -> None:
        state = self._state()
        uptime_s = int(time.time() - state.started_at)
        router_errors = {}
        if _command_import_error:
            router_errors["command_router"] = str(_command_import_error)
        if _llm_import_error:
            router_errors["llm_router"] = str(_llm_import_error)
        if _consent_import_error:
            router_errors["consent_store"] = str(_consent_import_error)
        if _metrics_import_error:
            router_errors["metrics_router"] = str(_metrics_import_error)
        if _memory_import_error:
            router_errors["memory_store"] = str(_memory_import_error)
        if _digest_import_error:
            router_errors["session_digest_router"] = str(_digest_import_error)

        self._send_json({
            "ok": True,
            "status": "healthy",
            "service": "bosly-gov-v4",
            "version": state.version,
            "uptime_seconds": uptime_s,
            "host": state.config.get("host"),
            "port": state.config.get("port"),
            "static_dir": str(STATIC_DIR),
            "router_status": {
                "command_router_loaded": route_command is not None,
                "llm_router_loaded": route_llm is not None,
                "llm_stream_loaded": route_llm_stream is not None,
                "consent_store_loaded": get_pending_action is not None and approve_pending_action is not None and deny_pending_action is not None,
                "metrics_router_loaded": get_metrics is not None,
                "memory_store_loaded": find_similar_fixes is not None,
                "session_digest_router_loaded": get_failure_digest is not None,
                "errors": router_errors,
            },
        })

    def handle_api_pending(self) -> None:
        if get_pending_action is None:
            self._send_json({"ok": False, "error": "consent_store not available."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            pending = get_pending_action()
            self._send_json({"ok": True, "pending": pending})
        except Exception as e:
            logging.exception("Failed reading pending action: %s", e)
            self._send_json({"ok": False, "error": "Failed to read pending action."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_chat(self) -> None:
        state = self._state()
        if route_command is None or route_llm is None:
            self._send_json({"ok": False, "error": "Router modules are unavailable."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
        except ValueError as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        message = (payload.get("message") or "").strip()
        if not message:
            self._send_error_envelope(ValidationError("Field 'message' is required."))
            return

        request_id = f"req-{int(time.time() * 1000)}"
        try:
            command_result = route_command(message=message, config=state.config, request_id=request_id)
        except Exception as e:
            logging.exception("command_router failure: %s", e)
            self._send_json({"ok": False, "error": "Command routing failed.", "detail": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if isinstance(command_result, dict) and command_result.get("handled") is True:
            command_result.setdefault("ok", True)
            command_result.setdefault("mode", "command")
            command_result["request_id"] = request_id
            self._send_json(command_result, status=HTTPStatus.OK)
            return

        try:
            status_code, llm_result = run_chat_once({"message": message, "request_id": request_id}, state.config)
        except Exception as e:
            logging.exception("llm_router failure: %s", e)
            self._send_error_envelope(normalize_exception(e, request_id=request_id))
            return

        if not isinstance(llm_result, dict):
            self._send_json({"ok": False, "error": "Invalid response from llm_router."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        llm_result.setdefault("ok", True)
        llm_result.setdefault("mode", "llm")
        llm_result["request_id"] = request_id
        self._send_json(llm_result, status=HTTPStatus(status_code or 200))

    def handle_api_chat_stream(self) -> None:
        state = self._state()
        if route_command is None or route_llm_stream is None:
            self._send_json({"ok": False, "error": "Streaming router unavailable."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
        except ValueError as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        message = (payload.get("message") or "").strip()
        if not message:
            self._send_json({"ok": False, "error": "Field 'message' is required."}, status=HTTPStatus.BAD_REQUEST)
            return

        request_id = f"req-{int(time.time() * 1000)}"

        try:
            command_result = route_command(message=message, config=state.config, request_id=request_id)
        except Exception as e:
            logging.exception("command_router failure: %s", e)
            self._send_json({"ok": False, "error": "Command routing failed.", "detail": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if isinstance(command_result, dict) and command_result.get("handled") is True:
            command_result.setdefault("ok", True)
            command_result.setdefault("mode", "command")
            command_result["request_id"] = request_id
            self._send_json(command_result, status=HTTPStatus.OK)
            return

        self._start_sse()
        try:
            self._write_sse("meta", {"ok": True, "mode": "llm", "request_id": request_id})
            for ev in route_llm_stream({"message": message, "request_id": request_id}, state.config):
                et = str(ev.get("type") or "")
                if et == "context":
                    self._write_sse("context", ev.get("context", {}))
                elif et == "token":
                    self._write_sse("token", {"text": ev.get("text", "")})
                elif et == "error":
                    self._write_sse("error", {"ok": False, "error": ev.get("error", "Stream error")})
                    break
                elif et == "done":
                    result = ev.get("result", {})
                    if isinstance(result, dict):
                        result.setdefault("ok", True)
                        result.setdefault("mode", "llm")
                        result["request_id"] = request_id
                    self._write_sse("done", result if isinstance(result, dict) else {"ok": True})
                    break
        except BrokenPipeError:
            logging.info("SSE client disconnected (request_id=%s)", request_id)
        except Exception as e:
            logging.exception("SSE stream failure: %s", e)
            try:
                self._write_sse("error", {"ok": False, "error": "Streaming failed", "detail": str(e)})
            except Exception:
                pass

    def handle_api_consent(self) -> None:
        if approve_pending_action is None or deny_pending_action is None:
            self._send_json({"ok": False, "error": "consent_store not available."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
        except ValueError as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return
        action = str(payload.get("action", "")).strip().lower()
        token = str(payload.get("token", "")).strip()
        if not action and "approve" in payload:
            action = "approve" if bool(payload.get("approve")) else "deny"
        if action not in ("approve", "deny"):
            self._send_json({"ok": False, "error": "Field 'action' must be 'approve' or 'deny'."}, status=HTTPStatus.BAD_REQUEST)
            return
        if not token:
            self._send_json({"ok": False, "error": "Field 'token' is required."}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            if action == "approve":
                result = approve_pending_action(token=token)
                # If approval wrote files, run deploy pipeline
                if result.get("ok") and result.get("executed", 0) > 0 and deploy_after_approval is not None:
                    file_paths = [r.get("path", "") for r in result.get("results", []) if r.get("path")]
                    deploy_result = deploy_after_approval(file_paths=file_paths, process_name="bosly")
                    result["deploy"] = deploy_result
                    if not deploy_result.get("ok"):
                        result["ok"] = False
                        result["error"] = deploy_result.get("error", "Deploy failed")
            else:
                result = deny_pending_action(token=token)
            if not isinstance(result, dict):
                result = {"ok": True, "action": action, "token": token}
            result.setdefault("ok", True)
            result.setdefault("mode", "consent")
            self._send_json(result, status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("Consent action failed: %s", e)
            self._send_json({"ok": False, "error": "Consent action failed.", "detail": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_projects_list(self) -> None:
        try:
            projects = []
            if PROJECTS_BASE.exists():
                for item in PROJECTS_BASE.iterdir():
                    if item.is_dir() and _validate_slug(item.name):
                        projects.append(item.name)
            self._send_json({"ok": True, "projects": sorted(projects)})
        except Exception as e:
            logging.exception("Failed to list projects: %s", e)
            self._send_json({"ok": False, "error": "Failed to list projects"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_create(self) -> None:
        try:
            data = parse_json_body(self)
            name = str(data.get("name", "")).strip()
            if not _validate_slug(name):
                self._send_json({"ok": False, "error": "Invalid project name. Use lowercase letters, numbers, hyphens only, max 50 chars."}, status=HTTPStatus.BAD_REQUEST)
                return
            project_path = _get_project_path(name)
            if project_path.exists():
                self._send_json({"ok": False, "error": "Project already exists"}, status=HTTPStatus.CONFLICT)
                return
            (project_path / "reports").mkdir(parents=True)
            current_year = str(time.localtime().tm_year)
            report_path = _get_report_path(name, current_year)
            report_path.write_text(f"# {name} — {current_year} Report Diary\n\n", encoding="utf-8")
            _write_json_file(_get_chat_path(name), [])
            _write_json_file(_get_memory_path(name), [])
            self._send_json({"ok": True, "project": name, "year": current_year})
        except Exception as e:
            logging.exception("Failed to create project: %s", e)
            self._send_json({"ok": False, "error": "Failed to create project"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_reports_list(self, slug: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        reports_dir = _get_project_path(slug) / "reports"
        if not reports_dir.exists():
            self._send_json({"ok": False, "error": "Project not found"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            reports = []
            for item in reports_dir.iterdir():
                if item.is_file() and item.suffix == ".md":
                    reports.append(item.stem)
            self._send_json({"ok": True, "reports": sorted(reports, reverse=True)})
        except Exception as e:
            logging.exception("Failed to list reports: %s", e)
            self._send_json({"ok": False, "error": "Failed to list reports"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_report_get(self, slug: str, year: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not year.isdigit() or len(year) != 4:
            self._send_json({"ok": False, "error": "Invalid year"}, status=HTTPStatus.BAD_REQUEST)
            return
        report_path = _get_report_path(slug, year)
        if not report_path.exists():
            self._send_json({"ok": False, "error": "Report not found"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            content = report_path.read_text(encoding="utf-8")
            self._send_json({"ok": True, "content": content})
        except Exception as e:
            logging.exception("Failed to read report: %s", e)
            self._send_json({"ok": False, "error": "Failed to read report"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_report_put(self, slug: str, year: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not year.isdigit() or len(year) != 4:
            self._send_json({"ok": False, "error": "Invalid year"}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            data = parse_json_body(self)
            content = str(data.get("content", ""))
            report_path = _get_report_path(slug, year)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(content, encoding="utf-8")
            self._send_json({"ok": True})
        except Exception as e:
            logging.exception("Failed to save report: %s", e)
            self._send_json({"ok": False, "error": "Failed to save report"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_report_new(self, slug: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            reports_dir = _get_project_path(slug) / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            existing_years = []
            for item in reports_dir.iterdir():
                if item.is_file() and item.suffix == ".md" and item.stem.isdigit():
                    existing_years.append(int(item.stem))
            current_year = time.localtime().tm_year
            next_year = str(max(existing_years) + 1) if existing_years else str(current_year)
            report_path = _get_report_path(slug, next_year)
            if report_path.exists():
                self._send_json({"ok": False, "error": f"Report {next_year} already exists"}, status=HTTPStatus.CONFLICT)
                return
            report_path.write_text(f"# {slug} — {next_year} Report Diary\n\n", encoding="utf-8")
            self._send_json({"ok": True, "year": next_year})
        except Exception as e:
            logging.exception("Failed to create new report: %s", e)
            self._send_json({"ok": False, "error": "Failed to create new report"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_memory_get(self, slug: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        memory_data = _read_json_file(_get_memory_path(slug))
        self._send_json({"ok": True, "memory": memory_data})

    def _handle_project_chat_get(self, slug: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        messages = _read_json_file(_get_chat_path(slug))
        self._send_json({"ok": True, "messages": messages})

    def handle_api_consent_actions_list(self) -> None:
        if ux_list_pending_actions is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json({"ok": True, "actions": ux_list_pending_actions()})

    def handle_api_consent_action_get(self, action_id: str) -> None:
        if ux_get_pending_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        item = ux_get_pending_action(action_id)
        if not item:
            self._send_json({"ok": False, "error": "Action not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": True, "action": item})

    def handle_api_consent_timeline(self, action_id: str) -> None:
        if ux_get_action_timeline is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json({"ok": True, "timeline": ux_get_action_timeline(action_id)})

    def handle_api_consent_action_create(self) -> None:
        if ux_create_pending_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
            self._send_json(ux_create_pending_action(payload), status=HTTPStatus.OK)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_api_consent_action_approve(self, action_id: str) -> None:
        if ux_approve_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json(ux_approve_action(action_id), status=HTTPStatus.OK)

    def handle_api_consent_action_deny(self, action_id: str) -> None:
        if ux_deny_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json(ux_deny_action(action_id), status=HTTPStatus.OK)

    def handle_api_consent_action_review(self, action_id: str) -> None:
        if ux_approve_action_files is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
            approved = payload.get("approved_paths", [])
            denied = payload.get("denied_paths", [])
            self._send_json(ux_approve_action_files(action_id, approved, denied), status=HTTPStatus.OK)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_api_consent_actions_list(self) -> None:
        if ux_list_pending_actions is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json({"ok": True, "actions": ux_list_pending_actions()})

    def handle_api_consent_action_get(self, action_id: str) -> None:
        if ux_get_pending_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        item = ux_get_pending_action(action_id)
        if not item:
            self._send_json({"ok": False, "error": "Action not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": True, "action": item})

    def handle_api_consent_timeline(self, action_id: str) -> None:
        if ux_get_action_timeline is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json({"ok": True, "timeline": ux_get_action_timeline(action_id)})

    def handle_api_consent_action_create(self) -> None:
        if ux_create_pending_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
            self._send_json(ux_create_pending_action(payload), status=HTTPStatus.OK)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_api_consent_action_approve(self, action_id: str) -> None:
        if ux_approve_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json(ux_approve_action(action_id), status=HTTPStatus.OK)

    def handle_api_consent_action_deny(self, action_id: str) -> None:
        if ux_deny_action is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json(ux_deny_action(action_id), status=HTTPStatus.OK)

    def handle_api_consent_action_review(self, action_id: str) -> None:
        if ux_approve_action_files is None:
            self._send_json({"ok": False, "error": f"consent_flow unavailable: {_consent_flow_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            payload = parse_json_body(self)
            approved = payload.get("approved_paths", [])
            denied = payload.get("denied_paths", [])
            self._send_json(ux_approve_action_files(action_id, approved, denied), status=HTTPStatus.OK)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def _graph_unavailable(self) -> bool:
        if not all([build_graph, graph_add_node, graph_add_edge, query_graph, get_related_entities, get_project_summary]):
            self._send_json(
                {"ok": False, "error": f"project_graph unavailable: {_project_graph_import_error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return True
        return False

    def handle_api_graph_build(self, slug: str) -> None:
        if self._graph_unavailable():
            return
        try:
            out = build_graph(slug)
            self._send_json(out, status=HTTPStatus.OK if out.get("ok") else HTTPStatus.BAD_REQUEST)
        except Exception as e:
            logging.exception("graph build failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_graph_add_node(self, slug: str) -> None:
        if self._graph_unavailable():
            return
        try:
            payload = parse_json_body(self)
            node_type = str(payload.get("node_type", "")).strip()
            node_id = str(payload.get("node_id", "")).strip()
            props = payload.get("properties", {}) if isinstance(payload.get("properties", {}), dict) else {}
            props["project_slug"] = slug
            out = graph_add_node(node_type=node_type, node_id=node_id, properties=props)
            self._send_json(out, status=HTTPStatus.OK if out.get("ok") else HTTPStatus.BAD_REQUEST)
        except Exception as e:
            logging.exception("graph add node failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_graph_add_edge(self, slug: str) -> None:
        if self._graph_unavailable():
            return
        try:
            payload = parse_json_body(self)
            from_node = str(payload.get("from_node", "")).strip()
            to_node = str(payload.get("to_node", "")).strip()
            relation = str(payload.get("relation", "")).strip()
            weight = float(payload.get("weight", 1.0) or 1.0)
            out = graph_add_edge(from_node=from_node, to_node=to_node, relation=relation, weight=weight)
            self._send_json(out, status=HTTPStatus.OK if out.get("ok") else HTTPStatus.BAD_REQUEST)
        except Exception as e:
            logging.exception("graph add edge failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_graph_query(self, slug: str, query: str) -> None:
        if self._graph_unavailable():
            return
        try:
            q = parse_qs(query or "")
            text = (q.get("q", [""])[0] or "").strip()
            items = query_graph(text, slug)
            self._send_json({"ok": True, "items": items}, status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("graph query failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_graph_related(self, slug: str, entity_id: str) -> None:
        if self._graph_unavailable():
            return
        try:
            items = get_related_entities(entity_id, slug)
            self._send_json({"ok": True, "items": items}, status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("graph related failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_graph_summary(self, slug: str) -> None:
        if self._graph_unavailable():
            return
        try:
            out = get_project_summary(slug)
            self._send_json(out, status=HTTPStatus.OK if out.get("ok") else HTTPStatus.BAD_REQUEST)
        except Exception as e:
            logging.exception("graph summary failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _observability_unavailable(self) -> bool:
        needed = [record_interaction, get_observability_metrics, get_recent_interactions, get_eval_tasks, run_eval]
        if not all(needed):
            self._send_json(
                {"ok": False, "error": f"observability unavailable: {_observability_import_error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return True
        return False

    def handle_api_observability_record(self) -> None:
        if self._observability_unavailable():
            return
        try:
            payload = parse_json_body(self)
            request_id = str(payload.get("request_id", "")).strip()
            data = payload.get("data", {})
            if not request_id:
                self._send_json({"ok": False, "error": "request_id is required"}, status=HTTPStatus.BAD_REQUEST)
                return
            if not isinstance(data, dict):
                self._send_json({"ok": False, "error": "data must be an object"}, status=HTTPStatus.BAD_REQUEST)
                return
            record_interaction(request_id=request_id, data=data)
            self._send_json({"ok": True})
        except Exception as e:
            logging.exception("record interaction failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_observability_metrics(self) -> None:
        if self._observability_unavailable():
            return
        try:
            self._send_json(get_observability_metrics(), status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("get observability metrics failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_observability_interactions(self, query: str) -> None:
        if self._observability_unavailable():
            return
        try:
            q = parse_qs(query or "")
            limit_raw = str((q.get("limit", ["100"])[0] or "100")).strip()
            try:
                limit = int(limit_raw)
            except Exception:
                limit = 100
            items = get_recent_interactions(limit=limit)
            self._send_json({"ok": True, "items": items}, status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("get recent interactions failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_observability_eval_tasks(self) -> None:
        if self._observability_unavailable():
            return
        try:
            self._send_json({"ok": True, "tasks": get_eval_tasks()}, status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("get eval tasks failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_api_observability_eval_run(self) -> None:
        if self._observability_unavailable():
            return
        try:
            self._send_json(run_eval(), status=HTTPStatus.OK)
        except Exception as e:
            logging.exception("run eval failed: %s", e)
            self._send_json({"ok": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_project_chat_post(self, slug: str) -> None:
        if not _validate_slug(slug):
            self._send_json({"ok": False, "error": "Invalid project slug"}, status=HTTPStatus.BAD_REQUEST)
            return
        if route_llm is None:
            self._send_json({"ok": False, "error": "LLM router unavailable"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            data = parse_json_body(self)
            user_message = str(data.get("message", "")).strip()
            if not user_message:
                self._send_error_envelope(ValidationError("Message is required"))
                return

            # Load context files
            accord_content = ACCORD_PATH.read_text(encoding="utf-8") if ACCORD_PATH.exists() else ""
            reports_dir = _get_project_path(slug) / "reports"
            report_files = sorted(
                [p for p in reports_dir.glob("*.md") if p.stem.isdigit()],
                key=lambda p: int(p.stem),
                reverse=True,
            ) if reports_dir.exists() else []
            if report_files:
                full_report = report_files[0].read_text(encoding="utf-8")
                # Only load the most recent 30000 chars — enough for recent context without overwhelming
                report_content = full_report[-8000:] if len(full_report) > 8000 else full_report
            else:
                report_content = ""
            memory_data = _read_json_file(_get_memory_path(slug))
            raw_chat = _read_json_file(_get_chat_path(slug))
            # Normalise: chat may be stored as {"chat": [...]} or as plain [...]
            if isinstance(raw_chat, dict):
                chat_history = raw_chat.get("chat", [])
            elif isinstance(raw_chat, list):
                chat_history = raw_chat
            else:
                chat_history = []

            recent_chat = chat_history[-50:] if len(chat_history) > 50 else chat_history
            recent_chat_text = "\n".join(
                f"{m.get('role', 'unknown')}: {m.get('message', m.get('content', ''))}"
                for m in recent_chat
                if isinstance(m, dict)
            )

            # Redact sensitive info before sending to LLM
            report_content = _redact_sensitive(report_content)
            memory_data_str = _redact_sensitive(json.dumps(memory_data, indent=2))
            recent_chat_text = _redact_sensitive(recent_chat_text)

            context_header = (
                f"[Project: {slug}]\n"
                f"[Governance Accord:]\n{accord_content[:3000]}\n\n"
                f"[Current Report:]\n{report_content[:5000]}\n\n"
                f"[Memory:]\n{json.dumps(memory_data, indent=2)[:2000]}\n\n"
                f"[Recent chat:]\n{recent_chat_text[:3000]}\n\n"
                f"User message: {user_message}"
            )

            request_id = f"req-{int(time.time() * 1000)}"
            status_code, llm_result = run_chat_once({"message": user_message, "project": slug, "request_id": request_id}, self._state().config)

            if not isinstance(llm_result, dict):
                self._send_json({"ok": False, "error": "Invalid LLM response"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return

            reply = str(
                llm_result.get("answer")
                or llm_result.get("assistant_response")
                or llm_result.get("response")
                or llm_result.get("message")
                or llm_result.get("content")
                or ""
            ).strip()

            if not reply:
                self._send_json({"ok": False, "error": "Empty LLM response"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return

            # Append to chat history
            updated_chat = chat_history + [
                {"role": "user", "message": user_message},
                {"role": "assistant", "message": reply},
            ]

            # Consolidate if over 50
            if len(updated_chat) > 50:
                overflow = updated_chat[:-50]
                updated_chat = updated_chat[-50:]
                if overflow and consolidate_messages is not None:
                    overflow_texts = [
                        f"{m.get('role', 'unknown')}: {m.get('message') or m.get('text') or m.get('content', '')}"
                        for m in overflow
                        if isinstance(m, dict)
                    ]
                    consolidated = consolidate_messages(overflow_texts)
                    if isinstance(memory_data, list):
                        memory_data.append(consolidated)
                    else:
                        memory_data = [consolidated]
                    _write_json_file(_get_memory_path(slug), memory_data)

            _write_json_file(_get_chat_path(slug), updated_chat)
            self._send_json({"ok": True, "reply": reply})

        except Exception as e:
            logging.exception("Failed to process project chat: %s", e)
            self._send_error_envelope(normalize_exception(e))


def run() -> None:
    config = load_config()
    log_level_name = str(config.get("log_level", "INFO")).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    if not STATIC_DIR.exists():
        logging.warning("Static directory does not exist: %s", STATIC_DIR)
    host = config["host"]
    port = config["port"]
    app_state = AppState(config=config, started_at=time.time())
    server = ThreadingHTTPServer((host, port), BoslyHandler)
    server.app_state = app_state
    logging.info("Bosly Gov v4 server starting on http://%s:%s", host, port)
    logging.info("Serving static files from: %s", STATIC_DIR)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutdown requested by user.")
    finally:
        server.server_close()
        logging.info("Server stopped.")

if __name__ == "__main__":
    run()

    def _handle_project_chat_stream(self, slug: str) -> None:
        if run_chat_stream is None:
            self._send_json({"ok": False, "error": f"context_orchestrator unavailable: {_orchestrator_import_error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        try:
            data = parse_json_body(self)
            user_message = str(data.get("message", "")).strip()
            if not user_message:
                self._send_json({"ok": False, "error": "Message is required"}, status=HTTPStatus.BAD_REQUEST)
                return
            self._start_sse()
            for ev in run_chat_stream({"message": user_message, "project": slug}, self._state().config):
                et = str(ev.get("type") or "token")
                if et == "meta":
                    self._write_sse("meta", {k: v for k, v in ev.items() if k != "type"})
                elif et == "context":
                    self._write_sse("context", ev.get("context", {}))
                elif et == "token":
                    self._write_sse("token", {"text": ev.get("text", "")})
                elif et == "error":
                    self._write_sse("error", {"ok": False, "error": ev.get("error", "Stream error")})
                    break
                elif et == "done":
                    self._write_sse("done", ev.get("result", {}))
                    break
        except BrokenPipeError:
            logging.info("Project SSE client disconnected")
        except Exception as e:
            logging.exception("Project SSE stream failure: %s", e)
            try:
                self._write_sse("error", {"ok": False, "error": "Streaming failed", "detail": str(e)})
            except Exception:
                pass
