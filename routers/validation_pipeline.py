#!/usr/bin/env python3
"""
Bosly Gov v4 - Validation Pipeline
Runs targeted checks first, then project checks.
Captures logs/artifacts in a deterministic structure.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import re

from routers.direct_llm import call_llm_direct
from routers.patch_engine import build_unified_diff

PROJECT_ROOT = "/home/bosly_accord/bosly-1.0"
ARTIFACT_ROOT = "/mnt/bosly/bosly-data/.data/governor/validation-artifacts"
DEFAULT_TIMEOUT = 240
SEMANTIC_REVIEW_TIMEOUT = 90
SEMANTIC_REVIEW_BLOCKING = False
SEMANTIC_REVIEW_MIN_CONFIDENCE = 0.60
SEMANTIC_REVIEW_WARN_RISK = 8


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CheckResult:
    name: str
    stage: str  # targeted | project
    command: List[str]
    cwd: str
    code: int
    duration_ms: int
    passed: bool
    stdout_log: str
    stderr_log: str
    summary: str


def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, content: str) -> None:
    path.write_text(content or "", encoding="utf-8", errors="replace")


def _run_cmd(
    argv: List[str],
    cwd: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    t0 = time.perf_counter()

    # executable fallback for missing pnpm/yarn
    run_variants = [argv]
    if argv and argv[0] == "pnpm":
        run_variants.append(["npx", *argv[1:]])
        run_variants.append(["npm", "run", "eslint", "--", *argv[2:]] if len(argv) > 1 and argv[1] == "eslint" else argv)
    elif argv and argv[0] == "yarn":
        run_variants.append(["npx", *argv[1:]])
        run_variants.append(["npm", "run", "eslint", "--", *argv[2:]] if len(argv) > 1 and argv[1] == "eslint" else argv)

    last_err = ""
    for cmd in run_variants:
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=os.environ.copy(),
            )
            dt = int((time.perf_counter() - t0) * 1000)
            return {"code": int(proc.returncode), "stdout": proc.stdout or "", "stderr": proc.stderr or "", "duration_ms": dt, "argv_used": cmd}
        except FileNotFoundError as e:
            last_err = str(e)
            continue
        except subprocess.TimeoutExpired:
            dt = int((time.perf_counter() - t0) * 1000)
            return {"code": 124, "stdout": "", "stderr": f"Timeout after {timeout}s", "duration_ms": dt, "argv_used": cmd}
        except Exception as e:
            last_err = str(e)
            continue

    dt = int((time.perf_counter() - t0) * 1000)
    return {"code": 1, "stdout": "", "stderr": f"Execution failed: {last_err}", "duration_ms": dt, "argv_used": argv}


def _detect_package_manager(root: str) -> str:
    # Force npm on mini PC (pnpm not installed)
    return "npm"
    if os.path.exists(os.path.join(root, "yarn.lock")):
        return "yarn"
    return "npm"


def _command_exists(name: str) -> bool:
    from shutil import which
    return which(name) is not None



def _extract_imports_ts_js(source: str) -> List[str]:
    pats = [
        r"(?m)^\s*import\s+[^\"']*from\s+[\"']([^\"']+)[\"']",
        r"(?m)^\s*import\s+[\"']([^\"']+)[\"']",
        r"(?m)^\s*const\s+.+?=\s*require\([\"']([^\"']+)[\"']\)",
    ]
    out: List[str] = []
    for pat in pats:
        for m in re.finditer(pat, source or ""):
            out.append((m.group(1) or "").strip())
    seen = set()
    uniq = []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def _resolve_import_candidates(import_path: str, from_file_abs: Path) -> List[Path]:
    if not import_path:
        return []
    if import_path.startswith("@/"):
        base = Path(PROJECT_ROOT) / import_path[2:]
    elif import_path.startswith("."):
        base = (from_file_abs.parent / import_path).resolve()
    else:
        return []

    suffixes = ["", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"]
    out: List[Path] = []
    for s in suffixes:
        p = Path(str(base) + s)
        if p.exists() and p.is_file():
            out.append(p.resolve())
    return out


def _build_relevant_paths(file_rel: str) -> List[str]:
    """Target file + direct local imports (one hop)."""
    target_abs = (Path(PROJECT_ROOT) / file_rel).resolve()
    if not target_abs.exists():
        return [file_rel.replace("\\", "/")]

    rels = []
    try:
        rels.append(str(target_abs.relative_to(PROJECT_ROOT)).replace("\\", "/"))
    except Exception:
        rels.append(file_rel.replace("\\", "/"))

    try:
        src = target_abs.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return rels

    imports = _extract_imports_ts_js(src)
    for imp in imports:
        for p in _resolve_import_candidates(imp, target_abs):
            try:
                rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except Exception:
                continue
            if rel not in rels:
                rels.append(rel)
    return rels


def _filter_tsc_output_for_paths(output: str, rel_paths: List[str]) -> str:
    if not output:
        return ""
    lines = output.splitlines()
    hits = []
    needles = [p.replace("\\", "/") for p in rel_paths]
    for ln in lines:
        lnorm = ln.replace("\\", "/")
        if any(n in lnorm or f"/{n}" in lnorm for n in needles):
            hits.append(ln)
    return "\n".join(hits)




def extract_error_files_from_tsc_output(output_text: str) -> List[str]:
    """
    Extract file paths from TypeScript diagnostic lines.
    Supports common tsc formats:
      path/to/file.ts(12,5): error TS...
      /abs/path/to/file.ts:12:5 - error TS...
    Returns repo-relative normalized paths when possible.
    """
    if not output_text:
        return []

    lines = output_text.splitlines()
    found: List[str] = []
    seen = set()

    pats = [
        re.compile(r'^(?P<path>[^:(\s][^:(]*\.(?:ts|tsx|js|jsx))\(\d+,\d+\)\s*:\s*error\s+TS', re.IGNORECASE),
        re.compile(r'^(?P<path>[^:\s][^:]*\.(?:ts|tsx|js|jsx)):\d+:\d+\s*-\s*error\s+TS', re.IGNORECASE),
    ]

    root = Path(PROJECT_ROOT).resolve()
    for ln in lines:
        path_val = None
        for pat in pats:
            m = pat.search(ln.strip())
            if m:
                path_val = m.group("path").strip()
                break
        if not path_val:
            continue

        p = Path(path_val)
        if not p.is_absolute():
            p = (root / path_val).resolve()
        try:
            rel = str(p.relative_to(root)).replace("\\", "/")
        except Exception:
            rel = str(path_val).replace("\\", "/")

        if rel not in seen:
            seen.add(rel)
            found.append(rel)

    return found

def _truncate(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]..."


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Robust JSON extraction from possible fenced / mixed LLM output."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Empty semantic review output.")
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("No JSON object found.")
    obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        raise ValueError("Parsed JSON is not an object.")
    return obj


def _semantic_review_prompt(file_rel: str, original_text: str, candidate_text: str, diff_text: str) -> str:
    return f"""
You are a strict static code reviewer focused on semantic and logic correctness.
Review the proposed patch for logic/behavior bugs, not style or formatting.

Return ONLY valid JSON in this exact schema:
{{
  "risk_score": 0,
  "suspected_issues": [
    {{"description": "string", "severity": "low|medium|high", "confidence": 0.0}}
  ],
  "suggested_fixes": [
    {{"description": "string", "code_hint": "string"}}
  ]
}}

Rules:
- risk_score must be integer 0-10
- confidence must be float 0-1
- Flag ANY logic bug, arithmetic error, or validation gap you can find
- Look for: wrong formulas, missing edge cases, incomplete validation, inverted conditions
- If you see a suspicious pattern, include it even with moderate confidence
- Only return empty arrays if the code is genuinely correct

Target file: {file_rel}

Unified diff:
{_truncate(diff_text, 18000)}

Original file:
{_truncate(original_text, 12000)}

Candidate file:
{_truncate(candidate_text, 12000)}
""".strip()


def run_semantic_review(file_rel: str, original_text: str, candidate_text: str) -> Dict[str, Any]:
    diff_text = build_unified_diff(original_text, candidate_text, file_rel)
    prompt = _semantic_review_prompt(file_rel=file_rel, original_text=original_text, candidate_text=candidate_text, diff_text=diff_text)
    rc, out, err = call_llm_direct(
        system_prompt="You are a semantic logic bug detector. Output strict JSON only.",
        user_message=prompt,
        timeout=SEMANTIC_REVIEW_TIMEOUT,
    )
    if rc != 0:
        return {"ok": False, "skipped": True, "reason": f"LLM call failed: {err or 'unknown error'}", "risk_score": None, "suspected_issues": [], "suggested_fixes": [], "raw_output": _truncate(out or "", 2000)}
    try:
        parsed = _extract_json_object(out or "")
    except Exception as e:
        return {"ok": False, "skipped": True, "reason": f"Invalid JSON from semantic review: {e}", "risk_score": None, "suspected_issues": [], "suggested_fixes": [], "raw_output": _truncate(out or "", 2000)}
    risk = parsed.get("risk_score", 0)
    try:
        risk = int(risk)
    except Exception:
        risk = 0
    risk = max(0, min(10, risk))
    issues = parsed.get("suspected_issues", [])
    fixes = parsed.get("suggested_fixes", [])
    if not isinstance(issues, list):
        issues = []
    if not isinstance(fixes, list):
        fixes = []
    normalized_issues = []
    for it in issues:
        if not isinstance(it, dict):
            continue
        desc = str(it.get("description", "")).strip()
        sev = str(it.get("severity", "low")).strip().lower()
        conf = it.get("confidence", 0)
        try:
            conf = float(conf)
        except Exception:
            conf = 0.0
        if sev not in {"low", "medium", "high"}:
            sev = "low"
        if desc:
            normalized_issues.append({"description": desc, "severity": sev, "confidence": max(0.0, min(1.0, conf))})
    normalized_fixes = []
    for it in fixes:
        if not isinstance(it, dict):
            continue
        desc = str(it.get("description", "")).strip()
        hint = str(it.get("code_hint", "")).strip()
        if desc or hint:
            normalized_fixes.append({"description": desc, "code_hint": hint})
    high_conf_issues = [i for i in normalized_issues if i["confidence"] >= SEMANTIC_REVIEW_MIN_CONFIDENCE and i["severity"] in {"medium", "high"}]
    warn = risk >= SEMANTIC_REVIEW_WARN_RISK or len(high_conf_issues) > 0
    return {"ok": True, "skipped": False, "risk_score": risk, "suspected_issues": normalized_issues, "suggested_fixes": normalized_fixes, "warn": warn, "high_conf_issues": high_conf_issues}


def _build_targeted_checks(file_rel: str) -> List[Dict[str, Any]]:
    ext = Path(file_rel).suffix.lower()
    pm = _detect_package_manager(PROJECT_ROOT)

    checks: List[Dict[str, Any]] = []

    # Always run tsc for TS/JS family
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        checks.append({
            "name": "tsc_targeted_scope",
            "stage": "targeted",
            "argv": [
                "npx", "tsc",
                "--noEmit",
                "--pretty", "false",
                "--project", "tsconfig.json",
                "--incremental", "false",
                "--assumeChangesOnlyAffectDirectDependencies", "true",
            ],
            "filter_path": None,
            "timeout": 180,
            "relevant_paths": _build_relevant_paths(file_rel),
        })

    # ESLint targeted if available
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        if pm == "pnpm":
            argv = ["pnpm", "eslint", file_rel, "--format", "unix"]
        elif pm == "yarn":
            argv = ["yarn", "eslint", file_rel, "--format", "unix"]
        else:
            argv = ["npx", "eslint", file_rel, "--format", "unix"]
        checks.append({
            "name": "eslint_targeted",
            "stage": "targeted",
            "argv": argv,
            "filter_path": None,
            "timeout": 120,
        })

    # Python file checks
    if ext == ".py":
        if _command_exists("python3"):
            checks.append({
                "name": "python_compile",
                "stage": "targeted",
                "argv": ["python3", "-m", "py_compile", file_rel],
                "filter_path": None,
                "timeout": 60,
            })

    return checks


def _build_project_checks() -> List[Dict[str, Any]]:
    pm = _detect_package_manager(PROJECT_ROOT)
    checks: List[Dict[str, Any]] = []

    # Build
    if pm == "pnpm":
        checks.append({"name": "project_build", "stage": "project", "argv": ["pnpm", "build"], "timeout": 600})
        checks.append({"name": "project_test", "stage": "project", "argv": ["pnpm", "test", "--", "--runInBand"], "timeout": 600})
    elif pm == "yarn":
        checks.append({"name": "project_build", "stage": "project", "argv": ["yarn", "build"], "timeout": 600})
        checks.append({"name": "project_test", "stage": "project", "argv": ["yarn", "test", "--runInBand"], "timeout": 600})
    else:
        checks.append({"name": "project_build", "stage": "project", "argv": ["npm", "run", "build"], "timeout": 600})
        checks.append({"name": "project_test", "stage": "project", "argv": ["npm", "test", "--", "--runInBand"], "timeout": 600})

    return checks


def _filter_output_for_path(output: str, file_rel: str) -> str:
    if not output:
        return ""
    rel = file_rel.replace("\\", "/")
    out_lines = output.splitlines()
    hits = [ln for ln in out_lines if rel in ln or f"/{rel}" in ln]
    return "\n".join(hits) if hits else output


def run_validation(
    file_rel: str,
    run_project_checks: bool = True,
    original_text: str | None = None,
    candidate_text: str | None = None,
) -> Dict[str, Any]:
    run_id = f"val-{int(time.time() * 1000)}"
    artifact_dir = Path(ARTIFACT_ROOT) / run_id
    _safe_mkdir(artifact_dir)

    checks_run: List[CheckResult] = []

    # 1) targeted checks
    for chk in _build_targeted_checks(file_rel):
        res = _run_cmd(chk["argv"], cwd=PROJECT_ROOT, timeout=int(chk.get("timeout", DEFAULT_TIMEOUT)))
        stdout = res["stdout"]
        stderr = res["stderr"]

        if chk.get("name") == "tsc_targeted_scope":
            relevant = chk.get("relevant_paths") or [file_rel.replace("\\", "/")]
            scoped_stdout = _filter_tsc_output_for_paths(stdout, relevant)
            scoped_stderr = _filter_tsc_output_for_paths(stderr, relevant)
            stdout = scoped_stdout
            stderr = scoped_stderr
            passed = (not stdout.strip() and not stderr.strip())
            if passed:
                res["code"] = 0
            summary = "ok" if passed else "failed (scoped diagnostics found)"
        else:
            passed = res["code"] == 0
            summary = "ok" if passed else f"failed ({res['code']})"

        stdout_log = f"{chk['name']}.stdout.log"
        stderr_log = f"{chk['name']}.stderr.log"
        _write_text(artifact_dir / stdout_log, stdout)
        _write_text(artifact_dir / stderr_log, stderr)

        checks_run.append(
            CheckResult(
                name=chk["name"],
                stage=chk["stage"],
                command=list(chk["argv"]),
                cwd=PROJECT_ROOT,
                code=int(res["code"]),
                duration_ms=int(res["duration_ms"]),
                passed=passed,
                stdout_log=stdout_log,
                stderr_log=stderr_log,
                summary=summary,
            )
        )

    targeted_passed = all(c.passed for c in checks_run if c.stage == "targeted")
    if not targeted_passed:
        report = {
            "ok": False,
            "run_id": run_id,
            "artifact_dir": str(artifact_dir),
            "checks_run": [asdict(c) for c in checks_run],
            "check_results": {
                "targeted_passed": False,
                "project_passed": None,
                "overall_passed": False,
            },
            "checked_at": utc_now_iso(),
        }
        _write_text(artifact_dir / "summary.json", json.dumps(report, indent=2))
        return report

    # 1.5) semantic review (warn-only by default)
    semantic_payload = None
    if original_text is not None and candidate_text is not None:
        sem = run_semantic_review(
            file_rel=file_rel,
            original_text=original_text,
            candidate_text=candidate_text,
        )
        semantic_payload = sem

        sem_stdout = json.dumps(sem, ensure_ascii=False, indent=2)
        sem_stderr = ""
        sem_passed = True
        sem_code = 0
        sem_summary = "ok"

        if sem.get("skipped"):
            sem_summary = f"skipped: {sem.get('reason', 'unknown')}"
        elif sem.get("warn"):
            sem_summary = "warn: semantic risks found"
            if SEMANTIC_REVIEW_BLOCKING:
                sem_passed = False
                sem_code = 2
                sem_stderr = "Blocking semantic review failed."

        stdout_log = "semantic_review.stdout.log"
        stderr_log = "semantic_review.stderr.log"
        _write_text(artifact_dir / stdout_log, sem_stdout)
        _write_text(artifact_dir / stderr_log, sem_stderr)

        checks_run.append(
            CheckResult(
                name="semantic_review",
                stage="targeted",
                command=["llm", "semantic_review"],
                cwd=PROJECT_ROOT,
                code=sem_code,
                duration_ms=0,
                passed=sem_passed,
                stdout_log=stdout_log,
                stderr_log=stderr_log,
                summary=sem_summary,
            )
        )

        # Recompute targeted status in case blocking mode enabled
        targeted_passed = all(c.passed for c in checks_run if c.stage == "targeted")
        if not targeted_passed:
            report = {
                "ok": False,
                "run_id": run_id,
                "artifact_dir": str(artifact_dir),
                "checks_run": [asdict(c) for c in checks_run],
                "check_results": {
                    "targeted_passed": False,
                    "project_passed": None,
                    "overall_passed": False,
                },
                "semantic_review": semantic_payload,
                "checked_at": utc_now_iso(),
            }
            _write_text(artifact_dir / "summary.json", json.dumps(report, indent=2))
            return report

    # 2) project checks
    if run_project_checks:
        for chk in _build_project_checks():
            res = _run_cmd(chk["argv"], cwd=PROJECT_ROOT, timeout=int(chk.get("timeout", DEFAULT_TIMEOUT)))
            passed = res["code"] == 0
            summary = "ok" if passed else f"failed ({res['code']})"

            stdout_log = f"{chk['name']}.stdout.log"
            stderr_log = f"{chk['name']}.stderr.log"
            _write_text(artifact_dir / stdout_log, res["stdout"])
            _write_text(artifact_dir / stderr_log, res["stderr"])

            checks_run.append(
                CheckResult(
                    name=chk["name"],
                    stage=chk["stage"],
                    command=list(chk["argv"]),
                    cwd=PROJECT_ROOT,
                    code=int(res["code"]),
                    duration_ms=int(res["duration_ms"]),
                    passed=passed,
                    stdout_log=stdout_log,
                    stderr_log=stderr_log,
                    summary=summary,
                )
            )

    project_checks = [c for c in checks_run if c.stage == "project"]
    project_passed = all(c.passed for c in project_checks) if project_checks else True
    overall_passed = targeted_passed and project_passed

    report = {
        "ok": overall_passed,
        "run_id": run_id,
        "artifact_dir": str(artifact_dir),
        "checks_run": [asdict(c) for c in checks_run],
        "check_results": {
            "targeted_passed": targeted_passed,
            "project_passed": project_passed,
            "overall_passed": overall_passed,
        },
        "semantic_review": semantic_payload,
        "checked_at": utc_now_iso(),
    }
    _write_text(artifact_dir / "summary.json", json.dumps(report, indent=2))
    return report


def collect_failure_feedback(report: Dict[str, Any], max_chars: int = 8000) -> str:
    """
    Build concise failure feedback text for retry prompts using failed check logs.
    """
    checks = report.get("checks_run") or []
    artifact_dir = report.get("artifact_dir") or ""
    snippets: List[str] = []

    for c in checks:
        if not isinstance(c, dict):
            continue
        if c.get("passed") is True:
            continue
        name = str(c.get("name") or "check")
        code = c.get("code")
        stdout_log = str(c.get("stdout_log") or "")
        stderr_log = str(c.get("stderr_log") or "")

        snippets.append(f"## Failed check: {name} (exit={code})")
        for log_name in (stderr_log, stdout_log):
            if not log_name:
                continue
            p = Path(artifact_dir) / log_name
            if not p.exists():
                continue
            txt = p.read_text(encoding="utf-8", errors="replace").strip()
            if txt:
                snippets.append(f"### {log_name}\n{txt[:2500]}")

    out = "\n\n".join(snippets).strip()
    if len(out) > max_chars:
        out = out[:max_chars] + "\n...[truncated]..."
    return out
