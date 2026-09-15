#!/usr/bin/env python3
"""
Bosly Gov v4 - Unified Context Orchestrator

Unifies /api/chat and /api/project/<slug>/chat pipelines.
Python 3.12+
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Generator, Tuple

from routers.file_access_router import read_file_lines, set_repo_root
from routers.intent_classifier import classify_intent, intent_confidence
from routers.llm_router import route_llm_low_level, route_llm_stream_low_level
from routers.provenance import attach_provenance, make_provenance_entry
from routers.token_budget import allocate_budget, build_budget, estimate_tokens, trim_to_budget
from routers.answer_verifier import verify_answer
from routers.memory_first import retrieve_memory_answer

PROJECTS_BASE = Path("/mnt/bosly/bosly-data/copilot-knowledge")
ACCORD_PATH = Path("/mnt/bosly/bosly-data/.data/governor/bosly-accord.md")


def _read_json_file(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _write_json_file(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


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


def _extract_explicit_paths(text: str) -> list[str]:
    import re
    rx = re.compile(
        r"""(?ix)(?<![\w./-])((?:[\w.-]+/)*[\w.-]+\.(?:ts|tsx|js|jsx|py|json|md|css|html|yml|yaml|sh|prisma))(?![\w./-])"""
    )
    out: list[str] = []
    seen: set[str] = set()
    for m in rx.finditer(text or ""):
        p = m.group(1).strip().strip("`'\"()[]{}<>.,;:").lstrip("./")
        k = p.lower()
        if p and k not in seen:
            seen.add(k)
            out.append(p)
    return out[:5]


def load_project_state(slug: str) -> dict:
    if not _validate_slug(slug):
        return {"ok": False, "error": "Invalid project slug"}

    chat = _read_json_file(_get_chat_path(slug))
    memory = _read_json_file(_get_memory_path(slug))

    reports_dir = _get_project_path(slug) / "reports"
    latest_report = ""
    latest_year = None
    if reports_dir.exists():
        years = sorted([p.stem for p in reports_dir.glob("*.md") if p.stem.isdigit()], reverse=True)
        if years:
            latest_year = years[0]
            rp = _get_report_path(slug, latest_year)
            if rp.exists():
                latest_report = rp.read_text(encoding="utf-8", errors="replace")

    accord = ACCORD_PATH.read_text(encoding="utf-8", errors="replace") if ACCORD_PATH.exists() else ""

    return {
        "ok": True,
        "slug": slug,
        "chat": chat if isinstance(chat, list) else (chat.get("chat", []) if isinstance(chat, dict) else []),
        "memory": memory,
        "latest_report_year": latest_year,
        "latest_report": latest_report,
        "accord": accord,
    }


def build_context(request: dict, config: dict) -> dict:
    message = str(request.get("message") or "").strip()
    project = str(request.get("project") or "").strip() or None
    # Set the active repo root based on project so file reads resolve correctly.
    set_repo_root(project)
    model = str(config.get("model") or "claude-sonnet-5")

    intent = classify_intent(message)
    intent_conf = intent_confidence(message)

    total_ctx = int(config.get("context_window_tokens", 16000) or 16000)
    reserve_output = int(config.get("reserve_output_tokens", 3000) or 3000)
    budget = build_budget(total_ctx, reserve_output)
    alloc = allocate_budget(intent, budget["available_input"])

    state = None
    chat_text = ""
    report_text = ""
    memory_text = ""
    accord_text = ""

    if project:
        state = load_project_state(project)
        if state.get("ok"):
            recent_chat = state["chat"][-50:] if len(state["chat"]) > 50 else state["chat"]
            chat_text = "\n".join(
                f"{m.get('role','unknown')}: {m.get('message', m.get('content',''))}"
                for m in recent_chat if isinstance(m, dict)
            )
            report_text = str(state.get("latest_report") or "")
            memory_text = json.dumps(state.get("memory", []), ensure_ascii=False, indent=2)
            accord_text = str(state.get("accord") or "")

    snippets: list[dict] = []
    provenance: list[dict] = []
    for p in _extract_explicit_paths(message):
        r = read_file_lines(p, 1, 220)
        if not r.get("ok"):
            continue
        sn = {
            "path": r.get("path", p),
            "start_line": int(r.get("start_line", 1) or 1),
            "end_line": int(r.get("end_line", 1) or 1),
            "snippet": str(r.get("snippet", "")),
            "reason": "explicit_file_mention",
        }
        snippets.append(sn)
        provenance.append(make_provenance_entry(sn["path"], sn["start_line"], sn["end_line"], sn["reason"]))

    snippets_text = "\n\n".join(
        f"<FILE_SNIPPET path=\"{s['path']}\" start_line=\"{s['start_line']}\" end_line=\"{s['end_line']}\" reason=\"{s['reason']}\">\n{s['snippet']}\n</FILE_SNIPPET>"
        for s in snippets
    )

    accord_trim = trim_to_budget(accord_text, alloc["accord"], model)
    report_trim = trim_to_budget(report_text, alloc["report"], model)
    memory_trim = trim_to_budget(memory_text, alloc["memory"], model)
    chat_trim = trim_to_budget(chat_text, alloc["recent_chat"], model)
    files_trim = trim_to_budget(snippets_text, alloc["file_snippets"], model)
    user_trim = trim_to_budget(message, alloc["user_message"], model)

    token_used_by_source = {
        "accord": estimate_tokens(accord_trim, model),
        "report": estimate_tokens(report_trim, model),
        "memory": estimate_tokens(memory_trim, model),
        "recent_chat": estimate_tokens(chat_trim, model),
        "file_snippets": estimate_tokens(files_trim, model),
        "user_message": estimate_tokens(user_trim, model),
    }

    dropped_sources = []
    if accord_text and not accord_trim:
        dropped_sources.append("accord")
    if report_text and not report_trim:
        dropped_sources.append("report")
    if memory_text and not memory_trim:
        dropped_sources.append("memory")
    if chat_text and not chat_trim:
        dropped_sources.append("recent_chat")
    if snippets_text and not files_trim:
        dropped_sources.append("file_snippets")

    context = {
        "project": project,
        "intent": intent,
        "intent_confidence": intent_conf,
        "model": model,
        "budget": budget,
        "allocation": alloc,
        "token_used_by_source": token_used_by_source,
        "dropped_sources": dropped_sources,
        "sources": {
            "accord": accord_trim,
            "report": report_trim,
            "memory": memory_trim,
            "recent_chat": chat_trim,
            "file_snippets": files_trim,
            "user_message": user_trim,
        },
        "provenance": provenance,
    }
    return context


def compose_prompt_from_context(context: dict) -> str:
    s = context["sources"]
    return (
        f"[Intent: {context.get('intent','general')}]\n"
        f"[Project]\n{context.get('project') or '(none)'}\n\n"
        f"[Governance Accord]\n{s.get('accord','')}\n\n"
        f"[Current Report]\n{s.get('report','')}\n\n"
        f"[Memory]\n{s.get('memory','')}\n\n"
        f"[Recent Chat]\n{s.get('recent_chat','')}\n\n"
        f"[Loaded File Context]\n{s.get('file_snippets','')}\n\n"
        f"USER_QUESTION:\n{s.get('user_message','')}"
    ).strip()


def run_chat_once(request: dict, config: dict) -> tuple[int, dict]:
    context = build_context(request, config)
    prompt = compose_prompt_from_context(context)

    # ---------------------------
    # Memory-first decision gate
    # ---------------------------
    user_message = str(request.get("message") or "").strip()
    project_slug = str(request.get("project") or "").strip()
    memory_first_enabled = bool(config.get("memory_first_enabled", True))

    if memory_first_enabled and project_slug:
        mem = retrieve_memory_answer(
            query=user_message,
            project_slug=project_slug,
            intent=str(context.get("intent", "general")),
        )
        m_mode = str(mem.get("mode", "llm_fallback"))
        m_conf = float(mem.get("confidence", 0.0) or 0.0)

        if m_mode == "memory_only" and m_conf >= 0.70:
            out = {
                "ok": True,
                "mode": "memory",
                "request_id": f"req-{int(time.time() * 1000)}",
                "answer": mem.get("answer", ""),
                "confidence": m_conf,
                "citations": [f"memory:{r.get('id')}" for r in mem.get("search_results", [])[:5]],
                "memory_audit": {
                    "mode": m_mode,
                    "confidence": m_conf,
                    "top_matches": [r.get("id") for r in mem.get("search_results", [])[:5]],
                    "fallback_reason": None,
                },
                "context_audit": {
                    "model": context.get("model"),
                    "intent": context.get("intent"),
                    "token_budget": {
                        **context.get("budget", {}),
                        "allocation": context.get("allocation", {}),
                    },
                    "token_used_by_source": context.get("token_used_by_source", {}),
                    "dropped_sources": context.get("dropped_sources", []),
                },
            }
            attach_provenance(out, context.get("provenance", []))
            return 200, out

        if m_mode == "memory_plus_clarification" and 0.45 <= m_conf < 0.70:
            out = {
                "ok": True,
                "mode": "hybrid",
                "request_id": f"req-{int(time.time() * 1000)}",
                "answer": mem.get("answer", ""),
                "clarification_needed": mem.get("clarification"),
                "confidence": m_conf,
                "citations": [f"memory:{r.get('id')}" for r in mem.get("search_results", [])[:5]],
                "memory_audit": {
                    "mode": m_mode,
                    "confidence": m_conf,
                    "top_matches": [r.get("id") for r in mem.get("search_results", [])[:5]],
                    "fallback_reason": None,
                },
                "context_audit": {
                    "model": context.get("model"),
                    "intent": context.get("intent"),
                    "token_budget": {
                        **context.get("budget", {}),
                        "allocation": context.get("allocation", {}),
                    },
                    "token_used_by_source": context.get("token_used_by_source", {}),
                    "dropped_sources": context.get("dropped_sources", []),
                },
            }
            attach_provenance(out, context.get("provenance", []))
            return 200, out

    request_id = f"req-{int(time.time() * 1000)}"
    status, out = route_llm_low_level({"message": prompt, "request_id": request_id}, config)

    if not isinstance(out, dict):
        out = {"ok": False, "error": "Invalid low-level LLM output"}

    out.setdefault("ok", status < 400)
    out["request_id"] = request_id
    out["context_audit"] = {
        "model": context.get("model"),
        "intent": context.get("intent"),
        "token_budget": {
            **context.get("budget", {}),
            "allocation": context.get("allocation", {}),
        },
        "token_used_by_source": context.get("token_used_by_source", {}),
        "dropped_sources": context.get("dropped_sources", []),
    }
    attach_provenance(out, context.get("provenance", []))

    # ---------------------------
    # Multi-pass verifier stage
    # ---------------------------
    strict_mode = bool(config.get("strict_mode", False) or request.get("strict_mode", False))
    answer_text = str(
        out.get("answer")
        or out.get("assistant_response")
        or out.get("response")
        or out.get("message")
        or ""
    ).strip()

    verification = verify_answer(answer_text, context)
    out["verification"] = verification
    out["confidence"] = verification.get("confidence", 0.0)
    out["citations"] = verification.get("citations", [])

    conf = float(verification.get("confidence", 0.0) or 0.0)
    low_threshold = float(config.get("verify_low_conf_threshold", 0.55) or 0.55)

    if conf < low_threshold:
        needed_files = verification.get("needed_files", []) or []
        needed_hint = (
            f"Please provide or allow loading these files: {', '.join(needed_files)}"
            if needed_files else
            "Please provide a specific file path or narrower scope so I can verify the answer."
        )
        clarification = (
            "I can give a higher-confidence answer with a bit more context.\n"
            f"{needed_hint}"
        )

        if strict_mode:
            return 409, {
                "ok": False,
                "mode": "verification_block",
                "request_id": request_id,
                "code": "LOW_CONFIDENCE_BLOCKED",
                "message": "Answer confidence is below strict threshold.",
                "hint": needed_hint,
                "retryable": True,
                "verification": verification,
                "context_audit": out.get("context_audit", {}),
                "provenance": out.get("provenance", []),
            }
        else:
            out["low_confidence"] = True
            out["clarification_needed"] = clarification
            out["answer"] = (answer_text + "\n\n---\n" + clarification).strip()

    return status, out


def run_chat_stream(request: dict, config: dict) -> Generator[dict, None, None]:
    context = build_context(request, config)
    prompt = compose_prompt_from_context(context)
    request_id = f"req-{int(time.time() * 1000)}"
    project_slug = str(request.get("project") or "").strip() or None

    yield {"type": "meta", "ok": True, "mode": "llm", "request_id": request_id}
    yield {"type": "context", "context": {
        "summary": f"[{context.get('intent','general')}] unified context loaded",
        "detail": ", ".join([p.get("path", "") for p in context.get("provenance", [])]) or "No explicit file snippets",
    }}

    final_text_parts: list[str] = []
    had_error = None

    for ev in route_llm_stream_low_level({"message": prompt, "request_id": request_id}, config):
        et = str(ev.get("type") or "")
        if et == "token":
            t = str(ev.get("text") or "")
            final_text_parts.append(t)
            yield {"type": "token", "text": t}
        elif et == "error":
            had_error = str(ev.get("error") or "stream error")
            yield {"type": "error", "error": had_error}
            return
        elif et == "done":
            break

    result = {
        "ok": had_error is None,
        "mode": "llm",
        "request_id": request_id,
        "answer": "".join(final_text_parts).strip(),
        "context_audit": {
            "model": context.get("model"),
            "intent": context.get("intent"),
            "token_budget": {
                **context.get("budget", {}),
                "allocation": context.get("allocation", {}),
            },
            "token_used_by_source": context.get("token_used_by_source", {}),
            "dropped_sources": context.get("dropped_sources", []),
        },
    }
    attach_provenance(result, context.get("provenance", []))
    yield {"type": "done", "result": result}
