#!/usr/bin/env python3
"""
Bosly Gov v4 - LLM Router
Streaming-first router with tiered context and aggressive tool-call stripping.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, Generator, Tuple

from routers.context_engine import WORKSPACE_ROOT, get_context
from routers.direct_llm import call_llm_direct, stream_llm_direct
from routers.file_access_router import read_file_lines, set_repo_root
from routers.token_budget import (
    estimate_tokens,
    build_budget,
    allocate_budget,
    trim_to_budget,
)
from routers.intent_classifier import classify_intent
from routers.prompt_compactor import (
    deduplicate_turns,
    compact_text,
    relevance_rank,
    strip_boilerplate,
)
from routers.error_types import (
    ValidationError,
    LLMTimeoutError,
    ContextLoadError,
    MemoryStoreError,
    FileAccessError,
    UnknownError,
)
from routers.provenance import make_provenance_entry, attach_provenance

try:
    from routers.consent_store import create_pending_action
except Exception:
    create_pending_action = None

LLM_TIMEOUT_SECONDS = 120
DEFAULT_LLM_SCRIPT = "/usr/local/bin/bosly-call-llm.py"
DEFAULT_PROMPT_FILE = "/usr/local/bin/bosly-prompt-oneline.txt"

DEVELOPER_COPILOT_SYSTEM_PROMPT = """You are Bosly Developer Copilot.

HARD MODE RULES (non-negotiable):
1) You MUST answer directly in plain text/markdown.
2) You MUST NOT output JSON objects, action objects, tool calls, function calls, XML calls, or pseudo-commands.
3) Do NOT emit strings like {"action":...}, {"tool":...}, <tool_call>, function_call, TOOL:, RUN:, or bash command plans.
4) If context is missing, say exactly what file is needed and continue with best-effort guidance.
5) Never include chain-of-thought. Give concise final reasoning only.
6) If user asks for code, provide code directly (markdown fences allowed).
7) Never invent access to tools. You have NO runtime tools in this mode.

If you accidentally start outputting a tool call, immediately stop and continue with a direct natural-language answer.

You are coding copilot for Bosly (Next.js 15, TypeScript, React, Prisma, PostgreSQL, Tailwind).
Follow Bosly Accord principles: calm, predictable, safe, maintainable.
"""

_TOOLISH_PATTERNS = [
    re.compile(r"(?is)```(?:json|javascript)?\s*\{[\s\S]{0,5000}?(?:\"action\"|\"tool\"|\"function_call\"|\"arguments\")\s*:[\s\S]{0,5000}?\}\s*```"),
    re.compile(r"(?im)^\s*\{[\s\S]{0,1200}?(?:\"action\"|\"tool\"|\"function_call\"|\"arguments\")\s*:[\s\S]{0,1200}?\}\s*$"),
    re.compile(r"(?im)^\s*(TOOL|RUN|ACTION)\s*:\s*.*$"),
    re.compile(r"(?is)<tool_call>[\s\S]*?</tool_call>"),
    re.compile(r"(?is)</?think>"),
]

_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\b\s*[:=]\s*([^\s\"']+)"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9\-\._~\+\/]+=*"),
    re.compile(r"\bsk-[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

_ENV_SECRET_KEYS = {
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN",
    "DATABASE_URL",
    "CLAUDE_API_KEY",
}

_MUTATION_PATTERNS = [
    r"(?im)^\s*RUN:\s*",
    r"(?i)\bcat\s*>\s*[^ \n]+\s*<<",
    r"(?i)\btee\s+[^ \n]+",
    r"(?i)\b>\s*[^ \n]+\.(ts|tsx|js|jsx|py|sh|json|md|css|yml|yaml)\b",
    r"(?i)\b>>\s*[^ \n]+\.(ts|tsx|js|jsx|py|sh|json|md|css|yml|yaml)\b",
    r"(?i)\bsed\s+-i\b",
    r"(?i)\bperl\s+-pi\b",
    r"(?i)\bapply_patch\b",
]

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

def _strip_toolish_output(text: str) -> str:
    if not text:
        return ""
    out = text
    for pat in _TOOLISH_PATTERNS:
        out = pat.sub("", out)
    # line-level second pass
    lines = out.splitlines()
    keep = []
    for line in lines:
        s = line.strip()
        if s.startswith("{") and s.endswith("}") and any(k in s for k in ['"action"', '"tool"', '"function_call"', '"arguments"']):
            continue
        if re.match(r"(?i)^\s*(TOOL|RUN|ACTION)\s*:", s):
            continue
        keep.append(line)
    out = "\n".join(keep).strip()
    return out

def _clean_llm_response(text: str) -> str:
    txt = _sanitize_text(text or "")
    txt = _strip_toolish_output(txt)
    txt = txt.strip()
    if not txt:
        return "I can answer directly, but I need one more specific file or snippet to proceed."
    return txt

def _read_prompt(prompt_path: str) -> str:
    try:
        with open(prompt_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""

def _call_llm_fallback_script(llm_script: str, user_message: str) -> Tuple[int, str, str]:
    proc = subprocess.run([llm_script, user_message], capture_output=True, text=True, timeout=LLM_TIMEOUT_SECONDS, check=False)
    return proc.returncode, proc.stdout or "", proc.stderr or ""

def _detect_mutation_intent(answer: str) -> bool:
    if not answer:
        return False
    return any(re.search(p, answer) for p in _MUTATION_PATTERNS)

def _extract_first_file_path(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"(?im)^\s*FILE:\s*(.+?)\s*$", text)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = re.search(r"(?im)^\s*Path:\s*(.+?)\s*$", text)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return None

def _resolve_target_path(candidate: str | None) -> str | None:
    if not candidate:
        return None
    raw = candidate.strip().strip('"').strip("'")
    if not raw:
        return None
    full = os.path.abspath(os.path.join(WORKSPACE_ROOT, raw))
    if not full.startswith(os.path.abspath(WORKSPACE_ROOT) + os.sep):
        return None
    return full

def _make_pending_action(answer: str, user_message: str) -> Dict[str, object] | None:
    if create_pending_action is None:
        return None
    rel_path = _extract_first_file_path(answer)
    abs_path = _resolve_target_path(rel_path) if rel_path else None
    title = f"Proposed modification: {rel_path}" if rel_path else "Proposed file modification"
    action = {
        "type": "file_modify",
        "title": title,
        "description": "Assistant proposed commands/content that may modify files.",
        "user_message": user_message,
        "assistant_response": answer,
        "target_path": abs_path,
        "target_path_relative": rel_path,
    }
    try:
        action_id = create_pending_action(action)
    except Exception:
        return None
    return {
        "requires_consent": True,
        "consent_action_id": action_id,
        "message": "This response may modify files. Approval required before execution.",
        "assistant_response": answer,
    }

FILE_CONTEXT_INSTRUCTIONS = """
FILE CONTEXT CONTRACT (high priority):
- The user message may contain one or more FILE_SNIPPET blocks.
- Each FILE_SNIPPET block contains REAL source code content already loaded by the backend.
- You MUST read and use those snippets when answering.
- Do NOT claim missing context for any file that appears in a FILE_SNIPPET block.
- If the answer depends on lines not included in provided ranges, say exactly what additional range is needed.
- When referencing snippet evidence, cite as: path:start-end (example: components/x.tsx:1-120).
"""


def _build_system_prompt(context_text: str, base_prompt: str) -> str:
    parts = [
        DEVELOPER_COPILOT_SYSTEM_PROMPT.strip(),
        "",
        FILE_CONTEXT_INSTRUCTIONS.strip(),
        "",
        "Context from workspace:",
        context_text.strip() if context_text else "(no context available)",
    ]
    if base_prompt:
        parts.extend(["", "Additional local prompt guidance:", base_prompt.strip()])
    return "\n".join(parts).strip()

_FILE_HINT_RE = re.compile(
    r"""(?ix)
    (?:
      (?:file|in|from|at|open|read|check|review|look\s+at|show)\s*[:\s]+
    )?
    (?P<path>
      [A-Za-z0-9_\-./]+
      \.
      (?:ts|tsx|js|jsx|py|json|md|css|html|yml|yaml|sh|prisma)
    )
    """
)

_AREA_HINTS = {
    "auth": ["auth", "login", "signin", "jwt", "oauth", "session"],
    "api": ["api", "endpoint", "route", "handler", "request", "response"],
    "db": ["db", "database", "prisma", "sql", "migration", "schema"],
    "ui": ["ui", "component", "react", "page", "layout", "frontend"],
}


def extract_file_intents(user_message: str) -> dict[str, Any]:
    """
    Detect direct file-path intent and loose code-area intent from user text.

    Behavior:
    - If one or more explicit file paths are present, treat them as authoritative.
    - Do not broaden to area-based retrieval when explicit paths exist.
    - Supports .tsx and other common source extensions.
    """
    text = (user_message or "").strip()
    low = text.lower()

    # Strict explicit-path regex:
    # - allows nested dirs
    # - requires extension (including .tsx)
    # - avoids trailing punctuation
    path_re = re.compile(
        r"""(?ix)
        (?<![\w./-])                              # clean left boundary
        (?P<path>
          (?:[\w.-]+/)*[\w.-]+\.
          (?:ts|tsx|js|jsx|py|json|md|css|scss|html|yml|yaml|sh|prisma)
        )
        (?![\w./-])                               # clean right boundary
        """
    )

    found_paths: list[str] = []
    seen: set[str] = set()
    for m in path_re.finditer(text):
        raw = (m.group("path") or "").strip()

        # Trim common wrappers/punctuation around paths
        cleaned = raw.strip("`'\"()[]{}<>.,;:")
        cleaned = cleaned.lstrip("./").replace("\\", "/")

        # ignore obviously malformed captures
        if not cleaned or cleaned.endswith("/"):
            continue

        # de-dup while preserving order
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            found_paths.append(cleaned)

    explicit_path_mode = len(found_paths) > 0

    # Only infer areas when no explicit file path was provided
    areas: list[str] = []
    if not explicit_path_mode:
        for area, kws in _AREA_HINTS.items():
            if any(kw in low for kw in kws):
                areas.append(area)

    code_markers = [
        "error in", "bug in", "fix", "refactor", "function", "class", "module",
        "file", "line", "lines", "stack trace", "traceback", "import", "type error"
    ]

    is_code_request = bool(
        explicit_path_mode or areas or any(k in low for k in code_markers)
    )
    wants_lines = bool(re.search(r"\bline[s]?\b|\bL\d+\b", text, re.IGNORECASE))

    return {
        "is_code_request": is_code_request,
        "paths": found_paths,                  # authoritative when non-empty
        "areas": areas,                        # empty when explicit path provided
        "wants_lines": wants_lines,
        "explicit_path_mode": explicit_path_mode,
    }


def read_on_demand_context(user_message: str) -> dict[str, Any]:
    intent = extract_file_intents(user_message)
    out: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "snippets": [],
        "provenance": [],
        "errors": [],
    }
    if not intent.get("is_code_request"):
        return out

    target_paths: list[str] = list(intent.get("paths") or [])

    if intent.get("explicit_path_mode"):
        target_paths = list(intent.get("paths") or [])
    else:
        target_paths = list(intent.get("paths") or []) + list(intent.get("areas") or [])
    target_paths = target_paths[:5]

    for rel_path in target_paths:
        res = read_file_lines(rel_path=rel_path, start=1, end=500)
        if not res.get("ok"):
            out["errors"].append(f"{rel_path}: {res.get('error', 'read failed')}")
            continue

        snippet_obj = {
            "path": res.get("path", rel_path),
            "start_line": int(res.get("start_line", 1) or 1),
            "end_line": int(res.get("end_line", 1) or 1),
            "snippet": str(res.get("snippet", "")),
            "reason": "explicit_file_mention",
        }
        out["snippets"].append(snippet_obj)
        out["provenance"].append(
            make_provenance_entry(
                path=snippet_obj["path"],
                start=snippet_obj["start_line"],
                end=snippet_obj["end_line"],
                reason=snippet_obj["reason"],
            )
        )

    return out


def _format_file_snippet_block(path: str, start_line: int, end_line: int, snippet: str, reason: str = "explicit_file_mention") -> str:
    safe_path = (path or "").strip()
    s = int(start_line or 1)
    e = int(end_line or s)
    r = (reason or "context").strip()
    content = (snippet or "").rstrip()
    return (
        f"<FILE_SNIPPET path=\"{safe_path}\" start_line=\"{s}\" end_line=\"{e}\" reason=\"{r}\">\n"
        f"{content}\n"
        f"</FILE_SNIPPET>"
    )


def route_llm(payload: Dict[str, object], config: Dict[str, object]) -> Tuple[int, Dict[str, object]]:
    user_message = str(payload.get("message", "")).strip()

    # --- Adaptive Context Budgeting ---
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    intent = classify_intent(user_message)
    total_ctx = int(config.get("context_window_tokens", 16000) or 16000)
    reserve_output = int(config.get("reserve_output_tokens", 3000) or 3000)
    budget = build_budget(total_ctx=total_ctx, reserve_output=reserve_output)
    alloc = allocate_budget(intent=intent, available_tokens=budget["available_input"])

    # --- NEW: read-on-demand code context ---
    # Set the active repo root based on the project slug so file reads
    # resolve against the correct codebase (bosly-accord vs bosly-keep).
    project_slug = str(payload.get("project", "")).strip() or None
    set_repo_root(project_slug)
    rod = read_on_demand_context(user_message)
    rod_snippets = rod.get("snippets", []) if isinstance(rod, dict) else []
    rod_provenance = rod.get("provenance", []) if isinstance(rod, dict) else []
    rod_errors = rod.get("errors", []) if isinstance(rod, dict) else []

    if rod_snippets:
        blocks: list[str] = []
        for sn in rod_snippets:
            blocks.append(
                _format_file_snippet_block(
                    path=str(sn.get("path", "")),
                    start_line=int(sn.get("start_line", 1) or 1),
                    end_line=int(sn.get("end_line", 1) or 1),
                    snippet=str(sn.get("snippet", "")),
                    reason=str(sn.get("reason", "explicit_file_mention")),
                )
            )

        user_message = (
            "USER_QUESTION:\n"
            f"{user_message}\n\n"
            "LOADED_FILE_CONTEXT:\n"
            "The following FILE_SNIPPET blocks are preloaded source of truth:\n\n"
            + "\n\n".join(blocks)
        )

        if rod_errors:
            user_message += "\n\nFILE_CONTEXT_NOTES:\n" + "\n".join(f"- {x}" for x in rod_errors)

    # --- Prompt Compaction ---
    recent_chat_messages = locals().get("recent_chat_messages", []) or []
    report_content = str(locals().get("report_content", "") or "")
    memory_data_str = str(locals().get("memory_data_str", "") or "")
    accord_content = str(locals().get("accord_content", "") or "")
    rod_snippets = list(locals().get("rod_snippets", []) or [])

    dedup_chat = deduplicate_turns(recent_chat_messages)
    raw_chat_text = "\n".join(
        f"{m.get('role','unknown')}: {m.get('message', m.get('content', m.get('text','')))}"
        for m in dedup_chat if isinstance(m, dict)
    )

    accord_clean = strip_boilerplate(accord_content)
    report_clean = strip_boilerplate(report_content)
    memory_clean = strip_boilerplate(memory_data_str)
    chat_clean = strip_boilerplate(raw_chat_text)

    ranked_snippets = relevance_rank(rod_snippets, user_message)
    ranked_snippets = ranked_snippets[:6]
    file_snippets_text = "\n\n".join(
        f"<FILE_SNIPPET path=\"{s.get('path','')}\" start_line=\"{s.get('start_line',1)}\" end_line=\"{s.get('end_line',1)}\" reason=\"{s.get('reason','context')}\">\n{s.get('snippet','')}\n</FILE_SNIPPET>"
        for s in ranked_snippets
    )

    raw_tokens = {
        "accord": estimate_tokens(accord_content, model),
        "report": estimate_tokens(report_content, model),
        "memory": estimate_tokens(memory_data_str, model),
        "recent_chat": estimate_tokens(raw_chat_text, model),
        "file_snippets": estimate_tokens(file_snippets_text, model),
        "user_message": estimate_tokens(user_message, model),
    }

    report_compact = compact_text(report_clean, max_tokens=max(64, alloc["report"]), model=model)
    memory_compact = compact_text(memory_clean, max_tokens=max(64, alloc["memory"]), model=model)
    chat_compact = compact_text(chat_clean, max_tokens=max(64, alloc["recent_chat"]), model=model)

    accord_trim = trim_to_budget(accord_clean, alloc["accord"], model)
    report_trim = trim_to_budget(report_compact, alloc["report"], model)
    memory_trim = trim_to_budget(memory_compact, alloc["memory"], model)
    chat_trim = trim_to_budget(chat_compact, alloc["recent_chat"], model)
    files_trim = trim_to_budget(file_snippets_text, alloc["file_snippets"], model)
    user_trim = trim_to_budget(user_message, alloc["user_message"], model)

    used_by_source = {
        "accord": estimate_tokens(accord_trim, model),
        "report": estimate_tokens(report_trim, model),
        "memory": estimate_tokens(memory_trim, model),
        "recent_chat": estimate_tokens(chat_trim, model),
        "file_snippets": estimate_tokens(files_trim, model),
        "user_message": estimate_tokens(user_trim, model),
    }

    prompt_compaction_stats = {
        "raw_tokens_by_source": raw_tokens,
        "final_tokens_by_source": used_by_source,
        "tokens_saved_by_source": {
            k: max(0, int(raw_tokens.get(k, 0)) - int(used_by_source.get(k, 0)))
            for k in raw_tokens.keys()
        },
        "tokens_saved_total": sum(
            max(0, int(raw_tokens.get(k, 0)) - int(used_by_source.get(k, 0)))
            for k in raw_tokens.keys()
        ),
        "chat_turns_before_dedup": len(recent_chat_messages),
        "chat_turns_after_dedup": len(dedup_chat),
        "snippets_before_rank": len(rod_snippets),
        "snippets_after_rank": len(ranked_snippets),
    }

    if not user_message:
        return 400, {"ok": False, "error": "Missing message"}

    llm_script = str(config.get("llm_script_path") or DEFAULT_LLM_SCRIPT)
    prompt_path = str(config.get("prompt_path") or DEFAULT_PROMPT_FILE)

    context_text, context_meta = get_context(user_message=user_message)
    base_prompt = _read_prompt(prompt_path)
    system_prompt = _build_system_prompt(context_text, base_prompt)

    rc, out, err = call_llm_direct(system_prompt=system_prompt, user_message=user_message, timeout=LLM_TIMEOUT_SECONDS)
    if rc != 0:
        rc2, out2, err2 = _call_llm_fallback_script(llm_script=llm_script, user_message=user_message)
        if rc2 != 0:
            return 500, {"ok": False, "error": _sanitize_text(err2 or err or "LLM invocation failed")}
        out = out2
        err = err2

    answer = _clean_llm_response((out or "").strip())
    if not answer:
        return 500, {"ok": False, "error": _sanitize_text(err or "Empty LLM response")}

    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message[:500],
            "answer_preview": answer[:500],
            "answer_length": len(answer),
            "mode": "claude" if os.environ.get("CLAUDE_API_KEY") else "civo",
            "context_tier": context_meta.get("tier", "light"),
        }
        log_path = "/mnt/bosly/bosly-data/.data/governor/gov-interactions.jsonl"
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass

    result: Dict[str, object] = {
        "ok": True,
        "answer": answer,
        "context_tier": context_meta.get("tier", "light"),
        "current_file": context_meta.get("current_file", ""),
        "context_files": context_meta.get("context_files", []),
    }

    # --- Adaptive Context Budgeting Audit ---
    used_by_source = {
        "accord": estimate_tokens("", model),
        "report": estimate_tokens("", model),
        "memory": estimate_tokens("", model),
        "recent_chat": estimate_tokens("", model),
        "file_snippets": estimate_tokens("", model),
        "user_message": estimate_tokens(user_message, model),
    }
    result["context_audit"] = {
        "model": model,
        "intent": intent,
        "token_budget": {
            "total_ctx": budget["total_ctx"],
            "reserve_output": budget["reserve_output"],
            "available_input": budget["available_input"],
            "allocation": alloc,
        },
        "token_used_by_source": used_by_source,
        "dropped_sources": [],
    }
    result["prompt_compaction_stats"] = prompt_compaction_stats

    attach_provenance(result, rod_provenance)

    if _detect_mutation_intent(answer):
        pending = _make_pending_action(answer, user_message)
        if pending:
            result.update(pending)

    return 200, result

def route_llm_stream(payload: Dict[str, object], config: Dict[str, object]) -> Generator[Dict[str, object], None, None]:
    user_message = str(payload.get("message", "")).strip()
    if not user_message:
        yield {"type": "error", "error": "Missing message"}
        return

    prompt_path = str(config.get("prompt_path") or DEFAULT_PROMPT_FILE)
    context_text, context_meta = get_context(user_message=user_message)
    base_prompt = _read_prompt(prompt_path)
    system_prompt = _build_system_prompt(context_text, base_prompt)

    yield {"type": "context", "context": context_meta}

    chunks: list[str] = []
    for ev in stream_llm_direct(system_prompt=system_prompt, user_message=user_message, timeout=LLM_TIMEOUT_SECONDS):
        t = str(ev.get("type") or "")
        if t == "token":
            token = _sanitize_text(str(ev.get("text") or ""))
            token = _strip_toolish_output(token)
            if not token:
                continue
            chunks.append(token)
            yield {"type": "token", "text": token}
        elif t == "error":
            yield {"type": "error", "error": _sanitize_text(str(ev.get("error") or "LLM stream error"))}
            return
        elif t == "done":
            break

    final = _clean_llm_response("".join(chunks))
    result = {
        "ok": True,
        "answer": final,
        "context_tier": context_meta.get("tier", "light"),
        "current_file": context_meta.get("current_file", ""),
        "context_files": context_meta.get("context_files", []),
    }

    if _detect_mutation_intent(final):
        pending = _make_pending_action(final, user_message)
        if pending:
            result.update(pending)

    yield {"type": "done", "result": result}


# Back-compat wrappers for context_orchestrator
def route_llm_low_level(payload: Dict, config: Dict) -> Tuple[int, Dict]:
    return route_llm(payload, config)


def route_llm_stream_low_level(payload: Dict, config: Dict) -> Generator[Dict, None, None]:
    yield from route_llm_stream(payload, config)
