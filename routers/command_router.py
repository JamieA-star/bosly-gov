#!/usr/bin/env python3
"""
Bosly Gov v4 - Command Router
Detects built-in command intent and executes mapped scripts.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

COMMAND_TIMEOUT_SECONDS = 120

SCRIPT_MAP = {
    "health": "/usr/local/bin/bosly-health",
    "diagnose": "/usr/local/bin/bosly-diagnose-v5.py",
    "deploy": "/usr/local/bin/bosly-deploy",
    "housekeep": "/usr/local/bin/bosly-housekeep",
    "audit": "/usr/local/bin/bosly-audit",
    "backup": "/usr/local/bin/bosly-backup-full.sh",
    "evolve": "/usr/local/bin/bosly-evolve",
    "smoke": "/usr/local/bin/bosly-smoke-test",
    "analytics": "/usr/local/bin/bosly-analytics",
}

DEPLOY_FALLBACK = ["/home/ubuntu/deploy-bosly-safe.sh"]

def _normalize(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _contains_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text) for p in patterns)

def _detect_command(message: str) -> Optional[str]:
    m = _normalize(message)
    if not m:
        return None

    # Only treat as a command if it's short and command-like (under 20 chars or explicit)
    # This prevents long questions containing "health" or "audit" from triggering commands
    is_short = len(m) <= 25
    is_explicit = any(m.startswith(prefix) for prefix in ("run ", "execute ", "do a ", "do an ", "perform ", "start "))
    
    if not (is_short or is_explicit):
        return None

    # Backup: only match exact commands, never partial
    if m in ("backup", "run backup", "create backup", "create a backup", "take backup", "take a backup"):
        return "backup"
    explicit_patterns = [
        ("health", r"\bhealth\b"),
        ("diagnose", r"\bdiagnos(e|is|tic)?\b"),
        ("deploy", r"\bdeploy(ment|ing)?\b"),
        ("housekeep", r"\bhouse ?keep(ing)?\b|\bcleanup\b|\bclean up\b"),
        ("audit", r"\baudit\b"),
        ("evolve", r"\bevolve\b|\bimprov(e|ement)\b"),
        ("smoke", r"\bsmoke\b|\bsmoke ?test\b|\bquick test\b"),
        ("analytics", r"\banalytics\b|\busage\b|\bstats\b"),
    ]
    for cmd, pat in explicit_patterns:
        if re.search(pat, m):
            return cmd
    if _contains_any(m, [r"how('s| is) (the )?(server|system)", r"\bstatus\b", r"\bhealthy\b"]):
        return "health"
    if _contains_any(m, [r"\bwhat('?s| is) wrong\b", r"\bdebug\b", r"\binvestigate\b", r"\bdiagnose\b"]):
        return "diagnose"
    if _contains_any(m, [r"\bpush to prod\b", r"\brelease\b", r"\bship\b", r"\bgo live\b"]):
        return "deploy"
    if _contains_any(m, [r"\bclean\b", r"\btidy\b", r"\bmaintenance\b", r"\bhousekeeping\b"]):
        return "housekeep"
    if _contains_any(m, [r"\bsecurity check\b", r"\bcompliance\b", r"\bscore\b", r"\bauditing\b"]):
        return "audit"
    # Backup only matches exact command above
    if _contains_any(m, [r"\boptimi[sz]e\b", r"\bmake it better\b", r"\bevolution\b"]):
        return "evolve"
    if _contains_any(m, [r"\bsanity check\b", r"\bquick verification\b", r"\bsmoke\b"]):
        return "smoke"
    return None

_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\b\s*[:=]\s*([^\s\"']+)"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9\-\._~\+\/]+=*"),
    re.compile(r"\bsk-[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

_ENV_SECRET_KEYS = {
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "GITHUB_TOKEN", "DATABASE_URL",
}


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences for browser display."""
    return re.sub(r"\033\[[0-9;]*[a-zA-Z]", "", text)

def _sanitize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    for pat in _SECRET_PATTERNS:
        cleaned = pat.sub(lambda m: f"{m.group(1) if m.lastindex and m.lastindex >= 1 else 'SECRET'}=[REDACTED]", cleaned)
    for key in _ENV_SECRET_KEYS:
        val = os.environ.get(key)
        if val and len(val) >= 6 and val in cleaned:
            cleaned = cleaned.replace(val, "[REDACTED]")
    return cleaned

def _resolve_command_argv(command_name: str) -> Tuple[List[str], str]:
    if command_name == "deploy":
        deploy_script = SCRIPT_MAP["deploy"]
        if os.path.exists(deploy_script) and os.access(deploy_script, os.X_OK):
            return [deploy_script], deploy_script
        return DEPLOY_FALLBACK, " ".join(DEPLOY_FALLBACK)
    script = SCRIPT_MAP[command_name]
    return [script], script

def _inline_health_check() -> Tuple[int, str, str]:
    lines = []
    errs = []
    checks = [
        ("/usr/local/bin/bosly-call-llm.py", "llm_script"),
        ("/usr/local/bin/bosly-audit", "audit_script"),
        ("/usr/local/bin/bosly-housekeep", "housekeep_script"),
    ]
    for path, label in checks:
        ok = os.path.exists(path) and os.access(path, os.X_OK)
        lines.append(f"{label}: {'ok' if ok else 'missing'} ({path})")
        if not ok:
            errs.append(f"missing: {path}")
    code = 0 if not errs else 2
    return code, "\n".join(lines), "\n".join(errs)

def _execute_command(command_name: str) -> Dict[str, object]:
    start = time.perf_counter()
    if command_name == "health":
        health_script = SCRIPT_MAP["health"]
        if not (os.path.exists(health_script) and os.access(health_script, os.X_OK)):
            code, out, err = _inline_health_check()
            duration_ms = int((time.perf_counter() - start) * 1000)
            return {
                "command": command_name, "script": "[inline-health-check]",
                "stdout": _sanitize_text(out), "stderr": _sanitize_text(err),
                "code": code, "duration_ms": duration_ms,
            }
    argv, script_label = _resolve_command_argv(command_name)
    if len(argv) == 1 and argv[0].startswith("/"):
        if not os.path.exists(argv[0]):
            duration_ms = int((time.perf_counter() - start) * 1000)
            return {
                "command": command_name, "script": script_label,
                "stdout": "", "stderr": f"Script not found: {argv[0]}",
                "code": 127, "duration_ms": duration_ms,
            }
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECONDS, check=False, env=os.environ.copy())
        code = int(proc.returncode)
        stdout = _sanitize_text(_strip_ansi(proc.stdout or ""))
        # Strip ANSI escape codes for browser display
        import re as _re
        stdout = _re.sub(r"\x1b\[[0-9;]*m", "", stdout)
        # Strip ANSI escape codes for browser display
        import re as _re
        stdout = _re.sub(r"\x1b\[[0-9;]*m", "", stdout)
        stderr = _sanitize_text(proc.stderr or "")
    except subprocess.TimeoutExpired:
        code = 124
        stdout = ""
        stderr = f"Command timed out after {COMMAND_TIMEOUT_SECONDS}s"
    except Exception as e:
        code = 1
        stdout = ""
        stderr = f"Execution error: {e}"
    duration_ms = int((time.perf_counter() - start) * 1000)
    return {
        "command": command_name, "script": script_label,
        "stdout": stdout, "stderr": stderr, "code": code, "duration_ms": duration_ms,
    }

def route_command(message: str, config: dict, request_id: str) -> dict:
    cmd = _detect_command(message)
    if not cmd:
        return {"handled": False}
    result = _execute_command(cmd)
    return {
        "handled": True, "mode": "command", "request_id": request_id,
        "command": result["command"], "script": result["script"],
        "stdout": result["stdout"], "stderr": result["stderr"],
        "code": result["code"], "duration_ms": result["duration_ms"],
    }
