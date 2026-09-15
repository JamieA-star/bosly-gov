#!/usr/bin/env python3
"""
Bosly Gov v4 - Tiered Context Engine
Provides light or full context bundles for LLM requests.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

WORKSPACE_ROOT = "/home/bosly_accord/bosly-1.0"
CONTEXT_PATH = "/tmp/bosly-context.json"
ACCORD_PATH = "/mnt/bosly/bosly-data/.data/governor/bosly-accord.md"

MAX_CONTEXT_CHARS_LIGHT = 7000
MAX_CONTEXT_CHARS_FULL = 14000
MAX_FILE_CHARS = 4000
MAX_RELATED_FILES_LIGHT = 2
MAX_RELATED_FILES_FULL = 4
MAX_PROJECT_TREE_ENTRIES = 80
CACHE_TTL_SECONDS = 60

_CONTEXT_CACHE: Dict[str, Dict[str, object]] = {"light": {"built_at": 0.0, "value": ""}, "full": {"built_at": 0.0, "value": ""}}

def _safe_read_text(path: Path, max_chars: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if max_chars is not None and len(text) > max_chars:
            return text[:max_chars] + "\n...[truncated]..."
        return text
    except Exception:
        return ""

def _read_context_pointer() -> Dict[str, object]:
    p = Path(CONTEXT_PATH)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def _resolve_in_workspace(rel_or_abs: str) -> Path | None:
    if not rel_or_abs:
        return None
    raw = rel_or_abs.strip()
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = Path(WORKSPACE_ROOT) / raw
    try:
        rp = p.resolve()
        root = Path(WORKSPACE_ROOT).resolve()
        if str(rp).startswith(str(root) + os.sep) or rp == root:
            return rp
        return None
    except Exception:
        return None

def _extract_imports(source: str) -> List[str]:
    imports: List[str] = []
    if not source:
        return imports
    patterns = [
        r'(?m)^\s*import\s+[^"\']*from\s+["\']([^"\']+)["\']',
        r'(?m)^\s*import\s+["\']([^"\']+)["\']',
        r'(?m)^\s*const\s+.+?=\s*require\(["\']([^"\']+)["\']\)',
        r'(?m)^\s*from\s+["\']([^"\']+)["\']\s+import\s+',
    ]
    for pat in patterns:
        for m in re.finditer(pat, source):
            mod = (m.group(1) or "").strip()
            if mod:
                imports.append(mod)
    seen: Set[str] = set()
    uniq: List[str] = []
    for i in imports:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq

def _candidate_paths_for_import(import_path: str, from_file: Path) -> List[Path]:
    cands: List[Path] = []
    if not import_path or import_path.startswith(("http://", "https://")):
        return cands
    if import_path.startswith("@/"):
        base = Path(WORKSPACE_ROOT) / import_path[2:]
    elif import_path.startswith("."):
        base = from_file.parent / import_path
    else:
        return cands
    suffixes = ["", ".ts", ".tsx", ".js", ".jsx", ".py", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"]
    for s in suffixes:
        cands.append(Path(str(base) + s))
    return cands

def _resolve_related_files(current_file: Path, imports: List[str], limit: int) -> List[Path]:
    out: List[Path] = []
    seen: Set[str] = set()
    for imp in imports:
        for c in _candidate_paths_for_import(imp, current_file):
            try:
                rp = c.resolve()
            except Exception:
                continue
            if not rp.exists() or not rp.is_file():
                continue
            if not str(rp).startswith(str(Path(WORKSPACE_ROOT).resolve()) + os.sep):
                continue
            key = str(rp)
            if key in seen:
                continue
            seen.add(key)
            out.append(rp)
            if len(out) >= limit:
                return out
    return out

def _run_cmd(cmd: List[str], cwd: str, timeout: int = 6) -> str:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
        return (proc.stdout or "").strip()
    except Exception:
        return ""

def _get_git_diff_stat() -> str:
    return _run_cmd(["git", "diff", "--stat", "HEAD~3"], cwd=WORKSPACE_ROOT, timeout=8)

def _walk_condensed_tree(root_dir: Path, label: str, max_entries: int) -> List[str]:
    lines: List[str] = []
    if not root_dir.exists() or not root_dir.is_dir():
        return [f"{label}/ (not found)"]
    count = 0
    for base, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".next", "dist", "build", "__pycache__"}]
        rel_base = Path(base).relative_to(root_dir)
        depth = len(rel_base.parts)
        if depth > 4:
            dirs[:] = []
            continue
        indent = "  " * depth
        lines.append(f"{label}/" if str(rel_base) == "." else f"{indent}{rel_base.name}/")
        if str(rel_base) != ".":
            count += 1
            if count >= max_entries:
                lines.append("  ...[truncated]...")
                return lines
        for f in sorted(files):
            if f.startswith("."):
                continue
            fp = Path(base) / f
            try:
                if fp.stat().st_size > 300_000:
                    continue
            except Exception:
                continue
            lines.append(f"{indent}  {f}")
            count += 1
            if count >= max_entries:
                lines.append("  ...[truncated]...")
                return lines
    return lines

def _get_accord_summary(max_lines: int = 50) -> str:
    p = Path(ACCORD_PATH)
    if not p.exists():
        return "(Bosly Accord file not found)"
    txt = _safe_read_text(p)
    if not txt:
        return "(Bosly Accord unavailable)"
    return "\n".join(txt.splitlines()[:max_lines])

def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[context truncated]..."

def _detect_context_tier(user_message: str) -> str:
    m = (user_message or "").lower()
    full_markers = ["deep", "full analysis", "full context", "analyze deeply", "comprehensive", "include diff", "use full context"]
    for k in full_markers:
        if k in m:
            return "full"
    return "light"

def _build_context(tier: str) -> Tuple[str, Dict[str, object]]:
    pointer = _read_context_pointer()
    current_file_raw = str(pointer.get("current_file") or "").strip()
    current_file = _resolve_in_workspace(current_file_raw) if current_file_raw else None

    light = tier == "light"
    related_limit = MAX_RELATED_FILES_LIGHT if light else MAX_RELATED_FILES_FULL

    sections: List[str] = []
    meta: Dict[str, object] = {"tier": tier, "current_file": current_file_raw or "", "context_files": []}

    sections.append(f"CONTEXT_TIER: {tier.upper()}")
    sections.append(f"WORKSPACE_ROOT: {WORKSPACE_ROOT}")
    sections.append(f"CURRENT_FILE: {current_file_raw if current_file_raw else '(none)'}")

    imports: List[str] = []
    related_files: List[Path] = []

    if current_file and current_file.exists() and current_file.is_file():
        current_text = _safe_read_text(current_file, max_chars=MAX_FILE_CHARS)
        sections.append("\n=== CURRENT FILE CONTENT ===")
        sections.append(current_text)

        imports = _extract_imports(current_text)
        sections.append("\n=== CURRENT FILE IMPORTS ===")
        sections.extend(imports if imports else ["(none detected)"])

        related_files = _resolve_related_files(current_file, imports, related_limit)
        sections.append("\n=== RELATED FILES (RESOLVED FROM IMPORTS) ===")
        if related_files:
            for rf in related_files:
                try:
                    rel = str(rf.relative_to(Path(WORKSPACE_ROOT)))
                except Exception:
                    rel = str(rf)
                sections.append(rel)
        else:
            sections.append("(none resolved)")
    else:
        sections.append("\n=== CURRENT FILE CONTENT ===")
        sections.append("(no current file set or file missing)")
        sections.append("\n=== CURRENT FILE IMPORTS ===")
        sections.append("(none)")

    context_files: List[str] = []
    if current_file_raw:
        context_files.append(current_file_raw)
    for rf in related_files:
        try:
            context_files.append(str(rf.relative_to(Path(WORKSPACE_ROOT))))
        except Exception:
            context_files.append(str(rf))
    meta["context_files"] = context_files

    if related_files:
        sections.append("\n=== RELATED FILE SNIPPETS ===")
        snippet_chars = 1200 if light else 2500
        for rf in related_files:
            try:
                rel = rf.relative_to(Path(WORKSPACE_ROOT))
            except Exception:
                rel = rf
            sections.append(f"\n--- {rel} ---")
            sections.append(_safe_read_text(rf, max_chars=snippet_chars))

    sections.append("\n=== BOSLY ACCORD SUMMARY ===")
    sections.append(_get_accord_summary(25 if light else 50))

    if not light:
        sections.append("\n=== RECENT GIT CHANGES (git diff --stat HEAD~3) ===")
        git_stat = _get_git_diff_stat()
        sections.append(git_stat if git_stat else "(no git diff stat available)")

        sections.append("\n=== PROJECT STRUCTURE (CONDENSED) ===")
        for top in ("app", "components", "lib", "scripts", "prisma"):
            sections.extend(_walk_condensed_tree(Path(WORKSPACE_ROOT) / top, top, max_entries=MAX_PROJECT_TREE_ENTRIES // 4))

        sections.append("\n=== SYSTEM TOOLS (bosly-* commands) ===")
        tools = sorted(glob.glob("/usr/local/bin/bosly-*"))
        tool_names = [os.path.basename(t) for t in tools if os.access(t, os.X_OK)][:15]
        sections.append(", ".join(tool_names) if tool_names else "(none found)")

        sections.append("\n=== LATEST ACCORD TEST RESULTS ===")
        test_dir = Path("/mnt/bosly/bosly-data/test-results")
        if test_dir.exists():
            test_files = sorted(test_dir.glob("*.json"), reverse=True)
            if test_files:
                try:
                    test_data = json.loads(test_files[0].read_text(encoding="utf-8", errors="replace"))
                    sections.append(
                        f"Passed: {test_data.get('passed','?')}/{test_data.get('total','?')}, "
                        f"Grade: {test_data.get('bosly_health',{}).get('grade','?')}, "
                        f"Run: {test_data.get('run_timestamp','?')}"
                    )
                except Exception:
                    sections.append("(could not read latest results)")
            else:
                sections.append("(no test result files found)")
        else:
            sections.append("(test results directory not found)")

        sections.append("\n=== EVOLUTION HISTORY (recent) ===")
        evolve_file = Path("/mnt/bosly/bosly-data/.data/governor/evolution-suggestions.txt")
        if evolve_file.exists():
            try:
                lines = [l for l in evolve_file.read_text(encoding="utf-8", errors="replace").split("\n") if l.strip()]
                sections.extend(lines[-10:] if lines else ["(empty)"])
            except Exception:
                sections.append("(could not read evolution history)")
        else:
            sections.append("(evolution history not found)")

    assembled = "\n".join(sections).strip()
    max_chars = MAX_CONTEXT_CHARS_LIGHT if light else MAX_CONTEXT_CHARS_FULL
    return _truncate(assembled, max_chars), meta

def get_context(user_message: str = "", force_tier: str | None = None) -> Tuple[str, Dict[str, object]]:
    tier = (force_tier or _detect_context_tier(user_message)).lower().strip()
    if tier not in {"light", "full"}:
        tier = "light"

    now = time.time()
    bucket = _CONTEXT_CACHE.get(tier) or {"built_at": 0.0, "value": "", "meta": {}}
    built_at = float(bucket.get("built_at") or 0.0)
    cached_val = str(bucket.get("value") or "")
    cached_meta = bucket.get("meta") if isinstance(bucket.get("meta"), dict) else {}

    if cached_val and (now - built_at) <= CACHE_TTL_SECONDS:
        return cached_val, dict(cached_meta)

    text, meta = _build_context(tier)
    _CONTEXT_CACHE[tier] = {"built_at": now, "value": text, "meta": meta}
    return text, meta
