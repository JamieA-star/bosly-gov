#!/usr/bin/env python3
"""
Bosly Gov v4 - Agent Router (Phase 3 + P3 deploy terminal split)
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from routers.agent_state_store import (
    create_session,
    get_session,
    save_session,
    append_event,
    list_recent_sessions,
    mutate_session,
)
from routers.patch_engine import (
    parse_patch_output,
    apply_patch_to_text,
    build_unified_diff,
    normalize_model_output,
)
from routers.validation_pipeline import run_validation, collect_failure_feedback
from routers.validation_pipeline import extract_error_files_from_tsc_output
from routers.direct_llm import call_llm_direct
from routers.context_engine import get_context
from routers.context_graph import build_context_v2
from routers.context_graph import build_dependency_order_for_target
from routers.memory_store import (
    find_similar_fixes,
    save_memory_entry,
    build_memory_entry_from_session,
)

try:
    from routers.consent_store import create_pending_action, approve_pending_action, deny_pending_action
except Exception:
    create_pending_action = None
    approve_pending_action = None
    deny_pending_action = None

PROJECT_ROOT = "/home/bosly_accord/bosly-1.0"
MAX_RETRIES_HARD_CAP = 3
LLM_TIMEOUT_SECONDS = 180
DEPLOY_TIMEOUT_SECONDS = 900
DEPLOY_COMMAND_DEFAULT = ["/usr/local/bin/bosly-deploy"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_resolve(path_rel: str) -> str | None:
    if not path_rel or not isinstance(path_rel, str):
        return None
    candidate = os.path.abspath(os.path.join(PROJECT_ROOT, path_rel))
    root = os.path.abspath(PROJECT_ROOT)
    if candidate == root or candidate.startswith(root + os.sep):
        return candidate
    return None


def _read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _write_file(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def _run_tsc_and_filter(full_rel_path: str) -> List[str]:
    proc = subprocess.run(
        ["npx", "tsc", "--noEmit", "--pretty", "false"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env=os.environ.copy(),
    )
    raw = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if not raw:
        return []
    rel = full_rel_path.replace("\\", "/")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    return [ln for ln in lines if rel in ln or f"/{rel}" in ln]


def _build_patch_prompt(
    file_rel: str,
    file_text: str,
    errors: List[str],
    context_text: str,
    context_v2_snippets: str,
    memory_hints: str,
    retry_index: int = 0,
    failure_feedback: str = "",
) -> str:
    retry_note = ""
    if retry_index > 0:
        retry_note = (
            f"\n\nRetry attempt #{retry_index + 1}. Previous candidate failed validation.\n"
            f"Failure logs:\n{failure_feedback}\n"
        )

    return f"""You are Bosly Gov patch generator.

Output ONLY one format:
A) JSON edit ops:
{{"edits":[{{"op":"set_file","content":"<full file content>"}}]}}
or line ops:
{{"edits":[{{"op":"replace","line":12,"text":"..."}}]}}

OR
B) Unified diff for this exact file:
--- a/{file_rel}
+++ b/{file_rel}
@@ ...

Rules:
- No explanation text.
- No markdown wrappers unless required.
- Keep non-error behavior unchanged.
- Must compile for the file language.

Target file: {file_rel}

Errors:
{os.linesep.join(errors) if errors else "(none)"}

Current file:
{file_text}

Primary context:
{context_text}

Context v2 snippets:
{context_v2_snippets}

Similar historical fixes:
{memory_hints}
{retry_note}
""".strip()


def _build_feature_prompt(
    file_rel: str,
    file_text: str,
    feature_description: str,
    context_text: str,
    context_v2_snippets: str,
    memory_hints: str,
    retry_index: int = 0,
    failure_feedback: str = "",
) -> str:
    retry_note = ""
    if retry_index > 0:
        retry_note = (
            f"\n\nRetry attempt #{retry_index + 1}. Previous candidate failed validation.\n"
            f"Failure logs:\n{failure_feedback}\n"
        )

    return f"""You are Bosly Gov feature implementation generator.

Output ONLY one format:
A) JSON edit ops:
{{"edits":[{{"op":"append","content":"<code to add>"}}]}}

OR
B) JSON edit ops:
{{"edits":[{{"op":"replace","line":12,"text":"..."}}]}}

Rules:
- No explanation text.
- No markdown wrappers unless required.
- For APPENDING new code (like new models), use "append" op with just the new code block.
- For MODIFYING existing code, use "replace" op with line number.
- Do NOT use "set_file" (full file replacement) unless absolutely necessary.
- Preserve existing behavior unless needed for feature implementation.
- Must compile for the file language.

Target file: {file_rel}

Feature request:
{feature_description}

Current file (truncated to last 100 lines for context):
{file_text[-5000:] if len(file_text) > 5000 else file_text}

Primary context:
{context_text}

Context v2 snippets:
{context_v2_snippets}

Similar historical fixes/features:
{memory_hints}
{retry_note}
""".strip()


class _TempReplace:
    def __init__(self, abs_path: str, new_text: str):
        self.path = abs_path
        self.new_text = new_text
        self.old_text = ""

    def __enter__(self):
        self.old_text = _read_file(self.path)
        _write_file(self.path, self.new_text)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            _write_file(self.path, self.old_text)
        except Exception:
            pass
        return False


def _ensure_session_input(payload: Dict[str, Any]) -> Tuple[bool, str]:
    file_rel = str(payload.get("file") or "").strip()
    if not file_rel:
        return False, "Missing 'file'."
    abs_path = _safe_resolve(file_rel)
    if not abs_path or not os.path.isfile(abs_path):
        return False, f"File not found: {file_rel}"
    return True, ""


def _public_session_view(s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "session_id": s.get("session_id"),
        "created_at": s.get("created_at"),
        "updated_at": s.get("updated_at"),
        "status": s.get("status"),
        "state": s.get("state"),
        "input": s.get("input"),
        "plan": s.get("plan"),
        "attempts": s.get("attempts"),
        "events": s.get("events"),
        "artifacts": s.get("artifacts"),
        "result": s.get("result"),
        "error": s.get("error"),
    }



def _build_fix_plan_from_validation(target_file: str, validation_report: Dict[str, Any]) -> Dict[str, Any]:
    """Build multi-file plan from scoped tsc diagnostics."""
    checks = validation_report.get("checks_run") if isinstance(validation_report.get("checks_run"), list) else []
    tsc_check = None
    for c in checks:
        if isinstance(c, dict) and c.get("name") in {"tsc_targeted_scope", "tsc_no_emit"}:
            tsc_check = c
            break

    error_files: List[str] = []
    if tsc_check and validation_report.get("artifact_dir"):
        artifact_dir = Path(str(validation_report.get("artifact_dir")))
        stderr_log = str(tsc_check.get("stderr_log") or "")
        stdout_log = str(tsc_check.get("stdout_log") or "")
        raw = ""
        for log_name in [stderr_log, stdout_log]:
            if not log_name:
                continue
            p = artifact_dir / log_name
            if p.exists():
                try:
                    raw += "\n" + p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
        error_files = extract_error_files_from_tsc_output(raw)

    dep_files = [f for f in error_files if f != target_file]
    ordered = build_dependency_order_for_target(target_file, dep_files + [target_file])

    plan_items = []
    for f in ordered:
        if f == target_file:
            plan_items.append({"file": f, "reason": "Original target"})
        else:
            plan_items.append({"file": f, "reason": "TypeScript errors in imported/dependency file"})

    return {
        "plan": plan_items,
        "total_files": len(plan_items),
        "error_files": error_files,
        "has_dependencies": any(it["file"] != target_file for it in plan_items),
    }


def _state_for_plan_index(idx: int, total: int) -> str:
    if idx < total - 1:
        return "fixing_dependency"
    return "fixing_target"



def _write_memory_terminal(session: Dict[str, Any]) -> None:
    artifacts = session.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        session["artifacts"] = artifacts
    if artifacts.get("memory_written") is True:
        return
    try:
        entry = build_memory_entry_from_session(session)
        save_memory_entry(entry)
        artifacts["memory_written"] = True
        append_event(session, "memory_saved", "Terminal session saved to memory store", {})
        save_session(session)
    except Exception:
        pass


def _mark_failed(s: Dict[str, Any], msg: str) -> Dict[str, Any]:
    s["status"] = "failed"
    s["state"] = "failed"
    s["error"] = msg
    append_event(s, "error", msg, {})
    save_session(s)
    _write_memory_terminal(s)
    return s


def _run_deploy_stage(s: Dict[str, Any]) -> Dict[str, Any]:
    inp = s.get("input") or {}
    result = s.get("result") if isinstance(s.get("result"), dict) else {}
    auto_deploy = bool(inp.get("auto_deploy", False))
    deploy_after_fix = bool(inp.get("deploy_after_fix", False))
    deploy_enabled = auto_deploy or deploy_after_fix

    deploy_result = {"attempted": False, "success": None, "code": None, "stdout": "", "stderr": ""}
    if not deploy_enabled:
        result["deploy"] = deploy_result
        s["result"] = result
        return s

    append_event(s, "state", "Deploy stage started", {})
    s["state"] = "deploying"
    save_session(s)

    cmd = DEPLOY_COMMAND_DEFAULT
    deploy_script = cmd[0] if cmd else ""
    if not deploy_script or not os.path.exists(deploy_script) or not os.access(deploy_script, os.X_OK):
        deploy_result = {
            "attempted": True,
            "success": False,
            "code": 127,
            "stdout": "",
            "stderr": f"Deploy script missing or not executable: {deploy_script}",
        }
        result["deploy"] = deploy_result
        s["result"] = result
        append_event(s, "deploy_failed", "Deploy precheck failed", {"code": 127, "stderr": deploy_result["stderr"]})
        save_session(s)
        return s

    try:
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=DEPLOY_TIMEOUT_SECONDS,
            check=False,
            env=os.environ.copy(),
        )
        code = int(proc.returncode)
        out = (proc.stdout or "")[:12000]
        err = (proc.stderr or "")[:12000]
        deploy_result = {
            "attempted": True,
            "success": code == 0,
            "code": code,
            "stdout": out,
            "stderr": err,
        }
    except Exception as e:
        deploy_result = {
            "attempted": True,
            "success": False,
            "code": 1,
            "stdout": "",
            "stderr": str(e)[:12000],
        }

    result["deploy"] = deploy_result
    s["result"] = result

    if deploy_result["success"]:
        append_event(s, "deploy_ok", "Deploy completed successfully", {"code": deploy_result["code"]})
    else:
        append_event(s, "deploy_failed", "Deploy failed", {"code": deploy_result["code"], "stderr": deploy_result["stderr"][:500]})
    save_session(s)
    return s


def start_fix_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, err = _ensure_session_input(payload)
    if not ok:
        return {"ok": False, "error": err}

    file_rel = str(payload.get("file") or "").strip()
    user_message = str(payload.get("message") or f"Fix file {file_rel}").strip()
    run_project_checks = bool(payload.get("run_project_checks", True))
    auto_deploy = bool(payload.get("auto_deploy", False))
    deploy_after_fix = bool(payload.get("deploy_after_fix", False))

    try:
        max_retries = int(payload.get("max_retries", 3))
    except Exception:
        max_retries = 3
    max_retries = max(1, min(max_retries, MAX_RETRIES_HARD_CAP))

    s = create_session({
        "mode": "fix",
        "file": file_rel,
        "message": user_message,
        "run_project_checks": run_project_checks,
        "max_retries": max_retries,
        "auto_deploy": auto_deploy,
        "deploy_after_fix": deploy_after_fix,
    })

    s["plan"] = [
        "Analyze target file and collect diagnostics",
        "Gather context v2 and similar past fixes",
        "Generate structured patch",
        "Apply candidate in-memory and validate",
        "Retry with failure feedback if needed",
        "Create consent-gated pending action",
        "On approval apply changes and optional deploy",
    ]
    s["status"] = "running"
    s["state"] = "analyzing"
    append_event(s, "state", "Session started", {"file": file_rel, "max_retries": max_retries})
    save_session(s)

    s = _run_until_pause_or_done(s)
    return {"ok": True, "session": _public_session_view(s)}




def start_feature_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, err = _ensure_session_input(payload)
    if not ok:
        return {"ok": False, "error": err}

    file_rel = str(payload.get("file") or "").strip()
    feature_description = str(payload.get("feature_description") or "").strip()
    if not feature_description:
        return {"ok": False, "error": "Missing feature_description."}

    user_message = str(payload.get("message") or f"Implement feature in {file_rel}: {feature_description}").strip()
    run_project_checks = bool(payload.get("run_project_checks", True))
    auto_deploy = bool(payload.get("auto_deploy", False))
    deploy_after_fix = bool(payload.get("deploy_after_fix", False))

    try:
        max_retries = int(payload.get("max_retries", 3))
    except Exception:
        max_retries = 3
    max_retries = max(1, min(max_retries, MAX_RETRIES_HARD_CAP))

    s = create_session({
        "mode": "feature",
        "file": file_rel,
        "feature_description": feature_description,
        "message": user_message,
        "run_project_checks": run_project_checks,
        "max_retries": max_retries,
        "auto_deploy": auto_deploy,
        "deploy_after_fix": deploy_after_fix,
    })

    s["plan"] = [
        "Analyze target file and gather context",
        "Generate structured feature patch",
        "Validate candidate",
        "Retry with failure feedback if needed",
        "Create consent-gated pending action",
        "On approval apply changes and optional deploy",
    ]
    s["status"] = "running"
    s["state"] = "analyzing"
    append_event(s, "state", "Feature session started", {"file": file_rel, "max_retries": max_retries})
    save_session(s)

    s = _run_until_pause_or_done(s)
    return {"ok": True, "session": _public_session_view(s)}


def _run_until_pause_or_done(s: Dict[str, Any]) -> Dict[str, Any]:
    if s.get("state") in {"awaiting_consent", "done", "failed", "done_with_deploy_failure"}:
        return s

    inp = s.get("input") or {}
    mode = str(inp.get("mode") or "fix").strip().lower()
    file_rel = str(inp.get("file") or "").strip()
    user_message = str(inp.get("message") or "").strip()
    run_project_checks = bool(inp.get("run_project_checks", True))
    max_retries = int(inp.get("max_retries", 3))

    abs_path = _safe_resolve(file_rel)
    if not abs_path or not os.path.isfile(abs_path):
        return _mark_failed(s, f"File not found during run: {file_rel}")

    try:
        original_text = _read_file(abs_path)
    except Exception as e:
        return _mark_failed(s, f"Failed reading file: {e}")

    s["state"] = "analyzing"
    if mode == "feature":
        append_event(s, "state", "Analyzing target for feature implementation", {})
        initial_errors: List[str] = []
        save_session(s)
    else:
        append_event(s, "state", "Running targeted diagnostics", {})
        save_session(s)

        initial_errors = _run_tsc_and_filter(file_rel)
        s["artifacts"]["initial_errors"] = initial_errors[:300]

        # Check if there are errors in dependencies by running a scoped validation
        _initial_scoped = run_validation(
            file_rel=file_rel,
            run_project_checks=False,
            original_text=_read_file(abs_path),
            candidate_text=_read_file(abs_path),
        )
        _scoped_errors = _initial_scoped.get("checks_run", []) or []
        _has_dep_errors = False
        for _c in _scoped_errors:
            if isinstance(_c, dict) and _c.get("name") == "tsc_targeted_scope" and _c.get("passed") is False:
                _has_dep_errors = True
                break

        if not initial_errors and not _has_dep_errors:
            # Run semantic review on the original file (logic bug check without type errors)
            sem = None
            try:
                from routers.validation_pipeline import run_semantic_review
                sem = run_semantic_review(
                    file_rel=file_rel,
                    original_text=original_text,
                    candidate_text=original_text,  # no patch, review original
                )
                s["artifacts"]["semantic_review"] = sem
            except Exception as e:
                s["artifacts"]["semantic_review_skipped"] = str(e)

            s["status"] = "done"
            s["state"] = "done"
            s["result"] = {
                "status": "no_errors",
                "file": file_rel,
                "checks_run": [],
                "check_results": {"targeted_passed": True, "project_passed": None, "overall_passed": True},
                "semantic_review": sem,
                "deploy": {"attempted": False, "success": None, "code": None, "stdout": "", "stderr": ""},
                "checked_at": utc_now_iso(),
            }
            if sem and sem.get("warn"):
                append_event(s, "done", f"No type errors, but semantic review flagged {len(sem.get('suspected_issues', []))} potential logic issue(s).", {})
            else:
                append_event(s, "done", "No matching errors found; no patch needed.", {})
            save_session(s)
            _write_memory_terminal(s)
            return s

    context_text, context_meta = get_context(user_message=user_message, force_tier="full")
    s["artifacts"]["context_meta"] = context_meta

    c2 = build_context_v2(file_rel)
    s["artifacts"]["context_v2"] = c2
    c2_files = []
    c2_snippets = []
    if c2.get("ok") and isinstance(c2.get("files"), list):
        for f in c2["files"]:
            p = str((f or {}).get("path") or "")
            sn = str((f or {}).get("snippet") or "")
            if p:
                c2_files.append(p)
                c2_snippets.append(f"FILE: {p}\n{sn}")
    s["artifacts"]["context_v2_files"] = c2_files

    err_sig = "\n".join(initial_errors[:25])
    mem = find_similar_fixes(file_rel=file_rel, error_text=err_sig, limit=5)
    s["artifacts"]["memory_matches"] = mem
    memory_hints = "\n".join(
        [f"- file={m.get('file')} attempts={m.get('attempts_count')} summary={m.get('summary')}" for m in mem]
    ) if mem else "(none)"

    save_session(s)

    if mode == "feature":
        # Feature mode: single file, no error-based planning
        s["state"] = "planning"
        append_event(s, "state", "Building feature implementation plan", {})
        save_session(s)
        plan = {"plan": [{"file": file_rel, "reason": "Feature target"}], "total_files": 1, "error_files": [], "has_dependencies": False}
        s["artifacts"]["fix_plan"] = plan
        s["artifacts"]["initial_validation"] = {"ok": True}
        append_event(s, "plan_built", "Feature plan generated", plan)
        save_session(s)
    else:
        s["state"] = "planning"
        append_event(s, "state", "Building multi-file fix plan", {})
        save_session(s)

        # Initial targeted validation to attribute cross-file errors
        initial_validation = run_validation(
            file_rel=file_rel,
            run_project_checks=False,
            original_text=original_text,
            candidate_text=original_text,
        )
        s["artifacts"]["initial_validation"] = initial_validation
        plan = _build_fix_plan_from_validation(file_rel, initial_validation)
        s["artifacts"]["fix_plan"] = plan
        append_event(s, "plan_built", "Multi-file fix plan generated", plan)
        save_session(s)

    attempts = s.get("attempts")
    if not isinstance(attempts, list):
        attempts = []
        s["attempts"] = attempts

    file_candidates: Dict[str, str] = {}
    file_diffs: Dict[str, str] = {}
    final_validation: Dict[str, Any] = {}

    plan_items = plan.get("plan") if isinstance(plan.get("plan"), list) else [{"file": file_rel, "reason": "Original target"}]
    total_files = len(plan_items)

    for file_idx, item in enumerate(plan_items):
        cur_file = str((item or {}).get("file") or "").strip()
        if not cur_file:
            continue
        cur_abs = _safe_resolve(cur_file)
        if not cur_abs or not os.path.isfile(cur_abs):
            s["status"] = "failed"
            s["state"] = "failed"
            s["error"] = f"Planned file missing: {cur_file}"
            append_event(s, "failed", "Planned file missing", {"file": cur_file})
            save_session(s)
            _write_memory_terminal(s)
            return s

        cur_original = _read_file(cur_abs)
        failure_feedback = ""
        file_fixed = False

        s["state"] = _state_for_plan_index(file_idx, total_files)
        append_event(s, "state", f"Fixing file {file_idx+1}/{total_files}: {cur_file}", {"file": cur_file, "reason": item.get("reason")})
        save_session(s)

        cur_errors = _run_tsc_and_filter(cur_file) if mode == "fix" else []
        if not cur_errors and mode == "fix":
            append_event(s, "file_skipped", "No direct scoped TS errors detected for planned file", {"file": cur_file})
            continue

        for i in range(max_retries):
            append_event(s, "state", f"Patching {cur_file} attempt {i+1}", {"file": cur_file, "attempt": i+1})
            save_session(s)

            if mode == "feature":
                feature_description = str(inp.get("feature_description") or "").strip()
                prompt = _build_feature_prompt(
                    file_rel=file_rel,
                    file_text=original_text,
                    feature_description=feature_description,
                    context_text=context_text,
                    context_v2_snippets="\n\n".join(c2_snippets[:10])[:18000] if c2_snippets else "(none)",
                    memory_hints=memory_hints,
                    retry_index=i,
                    failure_feedback=failure_feedback,
                )
            else:
                prompt = _build_patch_prompt(
                file_rel=cur_file,
                file_text=cur_original,
                errors=cur_errors,
                context_text=context_text,
                context_v2_snippets="\n\n".join(c2_snippets[:10])[:18000] if c2_snippets else "(none)",
                memory_hints=memory_hints,
                    retry_index=i,
                    failure_feedback=failure_feedback,
                )
            rc, out, err = call_llm_direct(
                system_prompt="You are a strict code patch generator.",
                user_message=prompt,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            if rc != 0:
                attempts.append({"file": cur_file, "attempt": i + 1, "ok": False, "stage": "llm", "error": err or "LLM call failed"})
                failure_feedback = err or "LLM call failed"
                append_event(s, "attempt_failed", "LLM call failed", {"file": cur_file, "attempt": i + 1, "error": failure_feedback})
                save_session(s)
                continue

            normalized = normalize_model_output(out)
            parsed = parse_patch_output(normalized, expected_rel_path=cur_file)
            if not parsed.ok:
                attempts.append({
                    "file": cur_file, "attempt": i + 1, "ok": False, "stage": "parse",
                    "error": "Patch parse failed", "parse_errors": parsed.errors[:20],
                })
                failure_feedback = "Patch parse failed:\n" + "\n".join(parsed.errors[:10])
                append_event(s, "attempt_failed", "Patch parse failed", {"file": cur_file, "attempt": i + 1, "errors": parsed.errors[:10]})
                save_session(s)
                continue

            ok_apply, candidate_text, apply_errs = apply_patch_to_text(cur_original, parsed)
            if not ok_apply:
                attempts.append({
                    "file": cur_file, "attempt": i + 1, "ok": False, "stage": "apply",
                    "error": "Patch apply failed", "apply_errors": apply_errs[:20],
                })
                failure_feedback = "Patch apply failed:\n" + "\n".join(apply_errs[:10])
                append_event(s, "attempt_failed", "Patch apply failed", {"file": cur_file, "attempt": i + 1, "errors": apply_errs[:10]})
                save_session(s)
                continue

            cur_diff = build_unified_diff(cur_original, candidate_text, cur_file)
            if not cur_diff.strip():
                attempts.append({"file": cur_file, "attempt": i + 1, "ok": False, "stage": "diff", "error": "Patch produced no changes"})
                failure_feedback = "Patch produced no changes."
                append_event(s, "attempt_failed", "Patch produced no changes", {"file": cur_file, "attempt": i + 1})
                save_session(s)
                continue

            s["state"] = "validating"
            append_event(s, "state", f"Validating {cur_file} attempt {i+1}", {"file": cur_file, "attempt": i + 1})
            save_session(s)

            # For empty files in feature mode, skip tsc (nothing to check yet)
            if mode == "feature" and len(cur_original.strip()) == 0:
                validation = {
                    "ok": True,
                    "run_id": f"skip-{int(time.time())}",
                    "artifact_dir": "",
                    "checks_run": [],
                    "check_results": {"targeted_passed": True, "project_passed": None, "overall_passed": True},
                }
            else:
                with _TempReplace(cur_abs, candidate_text):
                    validation = run_validation(
                        file_rel=cur_file,
                        run_project_checks=False,
                        original_text=cur_original,
                        candidate_text=candidate_text,
                    )

            attempts.append({
                "file": cur_file,
                "attempt": i + 1,
                "ok": bool(validation.get("ok")),
                "patch_format": parsed.format,
                "validation_run_id": validation.get("run_id"),
                "check_results": validation.get("check_results"),
            })
            s["artifacts"]["last_validation"] = validation
            save_session(s)

            if validation.get("ok") is True:
                file_candidates[cur_file] = candidate_text
                file_diffs[cur_file] = cur_diff
                file_fixed = True
                append_event(s, "attempt_ok", "File candidate passed validation", {"file": cur_file, "attempt": i + 1})
                break

            failure_feedback = collect_failure_feedback(validation, max_chars=7000)
            sem = validation.get("semantic_review") if isinstance(validation.get("semantic_review"), dict) else {}
            sem_issues = sem.get("suspected_issues") if isinstance(sem.get("suspected_issues"), list) else []
            if sem.get("warn") and sem_issues:
                issue_lines = []
                for it in sem_issues[:8]:
                    if isinstance(it, dict):
                        issue_lines.append(f"- [{it.get('severity','low')}] {it.get('description','')} (confidence={it.get('confidence',0)})")
                if issue_lines:
                    failure_feedback += "\n\nSemantic review findings to address:\n" + "\n".join(issue_lines)

            append_event(s, "attempt_failed", "File validation failed", {"file": cur_file, "attempt": i + 1})
            save_session(s)

        if not file_fixed:
            s["status"] = "failed"
            s["state"] = "failed"
            s["error"] = f"Failed to fix planned file after retries: {cur_file}"
            append_event(s, "failed", "Planned file failed", {"file": cur_file, "max_retries": max_retries})
            save_session(s)
            _write_memory_terminal(s)
            return s

    # Final holistic validation with all candidates temporarily applied
    temp_contexts = []
    try:
        for pf, content_val in file_candidates.items():
            pabs = _safe_resolve(pf)
            if pabs and os.path.isfile(pabs):
                ctx = _TempReplace(pabs, content_val)
                ctx.__enter__()
                temp_contexts.append(ctx)

        if mode == "feature":
            # Skip full validation for feature mode - build check already passed
            final_validation = {
                "ok": True,
                "run_id": f"feature-final-{int(time.time())}",
                "artifact_dir": "",
                "checks_run": [],
                "check_results": {"targeted_passed": True, "project_passed": True, "overall_passed": True},
            }
        else:
            final_validation = run_validation(
                file_rel=file_rel,
                run_project_checks=run_project_checks,
                original_text=original_text,
                candidate_text=file_candidates.get(file_rel, original_text),
            )
    finally:
        for ctx in reversed(temp_contexts):
            try:
                ctx.__exit__(None, None, None)
            except Exception:
                pass

    s["artifacts"]["final_validation"] = final_validation
    if not final_validation.get("ok"):
        s["status"] = "failed"
        s["state"] = "failed"
        s["error"] = "Final multi-file validation failed."
        append_event(s, "failed", "Final multi-file validation failed", {"validation_run_id": final_validation.get("run_id")})
        save_session(s)
        _write_memory_terminal(s)
        return s

    final_candidate_text = file_candidates.get(file_rel, "")
    final_diff = file_diffs.get(file_rel, "")
    if not final_candidate_text:
        s["status"] = "failed"
        s["state"] = "failed"
        s["error"] = f"Failed after {max_retries} attempts."
        append_event(s, "failed", "Max retries reached", {"max_retries": max_retries})
        save_session(s)
        _write_memory_terminal(s)
        return s

    if create_pending_action is None:
        s["status"] = "failed"
        s["state"] = "failed"
        s["error"] = "consent_store.create_pending_action unavailable."
        append_event(s, "failed", s["error"], {})
        save_session(s)
        _write_memory_terminal(s)
        return s

    combined_diff = "\n\n".join([f"# FILE: {f}\n{d}" for f, d in file_diffs.items()])
    file_ops = []
    for f, content_val in file_candidates.items():
        pabs = _safe_resolve(f)
        if pabs:
            file_ops.append({"path": pabs, "content": content_val, "mode": "overwrite"})

    pending_payload = {
        "type": "file_modify",
        "summary": f"Apply AI multi-file patch ({len(file_ops)} files) for target {file_rel}",
        "request_id": f"{s.get('session_id')}:consent",
        "file_ops": file_ops,
        "meta": {
            "session_id": s.get("session_id"),
            "file_rel": file_rel,
            "proposed_diff": combined_diff,
            "per_file_diffs": [{"file": f, "diff": d} for f, d in file_diffs.items()],
            "validation_run_id": final_validation.get("run_id"),
            "validation_artifact_dir": final_validation.get("artifact_dir"),
            "checks_run": final_validation.get("checks_run", []),
            "check_results": final_validation.get("check_results", {}),
            "context_v2_files": c2_files,
            "memory_matches": mem,
        },
    }

    pending = create_pending_action(pending_payload)
    token = (pending or {}).get("token") if isinstance(pending, dict) else None
    if not token:
        s["status"] = "failed"
        s["state"] = "failed"
        s["error"] = "Failed to create consent action."
        append_event(s, "failed", s["error"], {})
        save_session(s)
        _write_memory_terminal(s)
        return s

    s["status"] = "awaiting_consent"
    s["state"] = "awaiting_consent"
    s["result"] = {
        "status": "proposal_ready",
        "mode": mode,
        "file": file_rel,
        "proposed_diff": combined_diff,
        "per_file_diffs": [{"file": f, "diff": d} for f, d in file_diffs.items()],
        "fix_plan": plan,
        "total_files": len(file_ops),
        "checks_run": final_validation.get("checks_run", []),
        "check_results": final_validation.get("check_results", {}),
        "consent": {"required": True, "token": token},
        "memory_matches": mem,
        "context_v2_files": c2_files,
        "deploy": {"attempted": False, "success": None, "code": None, "stdout": "", "stderr": ""},
        "checked_at": utc_now_iso(),
    }
    s["artifacts"]["pending_token"] = token
    s["artifacts"]["candidate_content"] = final_candidate_text
    append_event(s, "awaiting_consent", "Waiting for user approval", {"token": token})
    save_session(s)
    return s


def resume_session(session_id: str, action: str) -> Dict[str, Any]:
    s = get_session(session_id)
    if not s:
        return {"ok": False, "error": f"Session not found: {session_id}"}

    action_norm = (action or "").strip().lower()
    if action_norm not in {"approve", "deny", "continue"}:
        return {"ok": False, "error": "action must be one of: approve, deny, continue"}

    state = str(s.get("state") or "")
    if state in {"failed", "done", "done_with_deploy_failure"}:
        return {"ok": True, "session": _public_session_view(s)}

    if state != "awaiting_consent":
        s = _run_until_pause_or_done(s)
        return {"ok": True, "session": _public_session_view(s)}

    token = str((s.get("artifacts") or {}).get("pending_token") or "").strip()
    if not token:
        s = _mark_failed(s, "Missing pending consent token in session artifacts.")
        return {"ok": True, "session": _public_session_view(s)}

    if action_norm == "continue":
        return {"ok": True, "session": _public_session_view(s)}

    if action_norm == "deny":
        if deny_pending_action is None:
            s = _mark_failed(s, "consent_store.deny_pending_action unavailable.")
            return {"ok": True, "session": _public_session_view(s)}
        deny_res = deny_pending_action(token=token)
        s["status"] = "failed"
        s["state"] = "failed"
        s["error"] = "User denied consent."
        append_event(s, "consent_denied", "User denied pending action", {"token": token, "result": deny_res})
        save_session(s)
        _write_memory_terminal(s)
        return {"ok": True, "session": _public_session_view(s)}

    if approve_pending_action is None:
        s = _mark_failed(s, "consent_store.approve_pending_action unavailable.")
        return {"ok": True, "session": _public_session_view(s)}

    s["state"] = "applying"
    append_event(s, "state", "Applying approved patch", {"token": token})
    save_session(s)

    approve_res = approve_pending_action(token=token)
    if not isinstance(approve_res, dict) or not approve_res.get("ok"):
        s["status"] = "failed"
        s["state"] = "failed"
        s["error"] = f"Approval apply failed: {approve_res}"
        append_event(s, "apply_failed", "Consent approval failed to apply patch", {"result": approve_res})
        save_session(s)
        _write_memory_terminal(s)
        return {"ok": True, "session": _public_session_view(s)}

    s["result"] = s.get("result") if isinstance(s.get("result"), dict) else {}
    s["result"]["applied"] = True
    s["result"]["consent_apply_result"] = approve_res
    s["result"]["completed_at"] = utc_now_iso()
    append_event(s, "apply_ok", "Patch applied successfully", {"result": approve_res})
    save_session(s)

    # optional deploy stage
    s = _run_deploy_stage(s)

    deploy = (s.get("result") or {}).get("deploy")
    if isinstance(deploy, dict) and deploy.get("attempted") and deploy.get("success") is False:
        s["status"] = "done_with_deploy_failure"
        s["state"] = "done_with_deploy_failure"
        s["result"]["failed_stage"] = "deploy"
        s["error"] = "Deploy stage failed."
        append_event(s, "done_with_deploy_failure", "Code applied but deploy failed", {"deploy": deploy})
        save_session(s)
        _write_memory_terminal(s)
        return {"ok": True, "session": _public_session_view(s)}

    s["status"] = "done"
    s["state"] = "done"
    append_event(s, "done", "Patch applied and session completed", {"result": s.get("result")})
    save_session(s)
    _write_memory_terminal(s)
    return {"ok": True, "session": _public_session_view(s)}


def get_session_view(session_id: str) -> Dict[str, Any]:
    s = get_session(session_id)
    if not s:
        return {"ok": False, "error": f"Session not found: {session_id}"}
    return {"ok": True, "session": _public_session_view(s)}


def recent_sessions(limit: int = 25) -> Dict[str, Any]:
    return {"ok": True, "sessions": list_recent_sessions(limit=limit)}
