#!/usr/bin/env python3
"""
Bosly Gov v4 - Context Graph (Phase 3 + P2 timing)
Symbol-aware-ish retrieval using practical heuristics:
- target file
- direct imports
- reverse references
- nearest tests
- key config files

Returns deterministic file list + snippets and timing metrics.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Set

PROJECT_ROOT = Path("/home/bosly_accord/bosly-1.0").resolve()
MAX_FILES = 18
MAX_SNIPPET_CHARS = 2200
MAX_SCAN_FILE_SIZE_BYTES = 300_000
MAX_SCANNED_FILES = 1200

SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".turbo"}
CODE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".md", ".css", ".prisma", ".yml", ".yaml"}


def _safe_read(path: Path, max_chars: int = MAX_SNIPPET_CHARS) -> str:
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if len(txt) > max_chars:
        return txt[:max_chars] + "\n...[truncated]..."
    return txt


def _in_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(PROJECT_ROOT)
        return True
    except Exception:
        return False


def _normalize_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _walk_files() -> List[Path]:
    out: List[Path] = []
    scanned = 0
    for base, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        pbase = Path(base)
        for f in files:
            if f.startswith("."):
                continue
            p = pbase / f
            if p.suffix.lower() in CODE_EXTS:
                try:
                    if p.stat().st_size > MAX_SCAN_FILE_SIZE_BYTES:
                        continue
                except Exception:
                    continue
                out.append(p)
                scanned += 1
                if scanned >= MAX_SCANNED_FILES:
                    return out
    return out


def _extract_imports(text: str) -> List[str]:
    pats = [
        r'(?m)^\s*import\s+[^"\']*from\s+["\']([^"\']+)["\']',
        r'(?m)^\s*import\s+["\']([^"\']+)["\']',
        r'(?m)^\s*const\s+.+?=\s*require\(["\']([^"\']+)["\']\)',
        r'(?m)^\s*from\s+["\']([^"\']+)["\']\s+import\s+',
    ]
    out: List[str] = []
    for pat in pats:
        for m in re.finditer(pat, text or ""):
            mod = (m.group(1) or "").strip()
            if mod:
                out.append(mod)
    seen: Set[str] = set()
    uniq: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def _resolve_import_to_file(import_path: str, from_file: Path) -> List[Path]:
    if not import_path or import_path.startswith(("http://", "https://")):
        return []
    if import_path.startswith("@/"):
        base = PROJECT_ROOT / import_path[2:]
    elif import_path.startswith("."):
        base = (from_file.parent / import_path).resolve()
    else:
        return []

    suffixes = ["", ".ts", ".tsx", ".js", ".jsx", ".py", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"]
    cands: List[Path] = []
    for s in suffixes:
        c = Path(str(base) + s)
        if c.exists() and c.is_file() and _in_repo(c):
            cands.append(c.resolve())
    return cands


def _find_nearest_tests(target_rel: str) -> List[Path]:
    target = (PROJECT_ROOT / target_rel).resolve()
    stem = target.stem
    parent = target.parent
    out: List[Path] = []

    patterns = [
        f"{stem}.test.ts", f"{stem}.test.tsx", f"{stem}.spec.ts", f"{stem}.spec.tsx",
        f"{stem}.test.js", f"{stem}.spec.js",
    ]
    for pat in patterns:
        p = parent / pat
        if p.exists() and p.is_file():
            out.append(p.resolve())

    for p in _walk_files():
        rel = _normalize_rel(p)
        if "__tests__/" in rel or rel.startswith("tests/") or "/tests/" in rel:
            if stem in p.name:
                out.append(p.resolve())

    uniq: List[Path] = []
    seen: Set[str] = set()
    for p in out:
        k = str(p)
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq[:4]


def _find_reverse_refs(target_rel: str) -> List[Path]:
    target_norm = target_rel.replace("\\", "/").lstrip("./")
    stem = Path(target_norm).stem
    parent = Path(target_norm).parent.as_posix()

    needles = {target_norm, f"./{stem}", f"../{stem}", f"/{stem}", stem, parent}

    out: List[Path] = []
    for p in _walk_files():
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if any(n and n in txt for n in needles):
            out.append(p.resolve())
    return out[:10]


def _config_files() -> List[Path]:
    candidates = [
        "package.json", "tsconfig.json", "tsconfig.base.json",
        "next.config.js", "next.config.mjs", "next.config.ts",
        "prisma/schema.prisma", ".eslintrc", ".eslintrc.json", ".eslintrc.js",
    ]
    out: List[Path] = []
    for rel in candidates:
        p = (PROJECT_ROOT / rel).resolve()
        if p.exists() and p.is_file():
            out.append(p)
    return out


def build_context_v2(target_rel_path: str) -> Dict[str, object]:
    t0 = time.perf_counter()
    stage_ms: Dict[str, int] = {}
    try:
        stage_start = time.perf_counter()
        target = (PROJECT_ROOT / target_rel_path).resolve()
        if not target.exists() or not target.is_file() or not _in_repo(target):
            return {"ok": False, "error": f"Target file not found in repo: {target_rel_path}", "timing_ms": int((time.perf_counter()-t0)*1000)}
        selected: List[Path] = [target]
        stage_ms["resolve_target"] = int((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        target_text = _safe_read(target, max_chars=4000)
        imports = _extract_imports(target_text)
        stage_ms["read_target_and_imports"] = int((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        for imp in imports:
            for p in _resolve_import_to_file(imp, target):
                if p not in selected:
                    selected.append(p)
        stage_ms["resolve_imports"] = int((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        for p in _find_reverse_refs(_normalize_rel(target)):
            if p == target:
                continue
            if p not in selected:
                selected.append(p)
        stage_ms["reverse_refs"] = int((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        for p in _find_nearest_tests(_normalize_rel(target)):
            if p not in selected:
                selected.append(p)
        stage_ms["nearest_tests"] = int((time.perf_counter() - stage_start) * 1000)

        stage_start = time.perf_counter()
        for p in _config_files():
            if p not in selected:
                selected.append(p)
        stage_ms["config_files"] = int((time.perf_counter() - stage_start) * 1000)

        selected = selected[:MAX_FILES]

        stage_start = time.perf_counter()
        files: List[Dict[str, str]] = []
        for p in selected:
            files.append({"path": _normalize_rel(p), "snippet": _safe_read(p, MAX_SNIPPET_CHARS)})
        stage_ms["read_snippets"] = int((time.perf_counter() - stage_start) * 1000)

        total_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "ok": True,
            "target": _normalize_rel(target),
            "file_count": len(files),
            "files": files,
            "imports_detected": imports[:30],
            "timing_ms": total_ms,
            "stage_timing_ms": stage_ms,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"context_v2_failed: {e}",
            "timing_ms": int((time.perf_counter() - t0) * 1000),
            "stage_timing_ms": stage_ms,
        }


def build_dependency_order_for_target(target_rel_path: str, candidate_files: List[str]) -> List[str]:
    """
    Returns ordered files so dependencies appear before target where possible.
    Simple heuristic: files directly imported by target first, then others, target last.
    """
    target = (PROJECT_ROOT / target_rel_path).resolve()
    if not target.exists():
        out = [f for f in candidate_files if f != target_rel_path]
        out.append(target_rel_path)
        return out

    target_src = _safe_read(target, max_chars=8000)
    imports = _extract_imports(target_src)
    imported_rel = []
    for imp in imports:
        for p in _resolve_import_to_file(imp, target):
            try:
                rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except Exception:
                continue
            imported_rel.append(rel)

    imported_set = set(imported_rel)
    cands = [c.replace("\\", "/") for c in candidate_files if c]
    cands_set = set(cands)

    dep_first = [r for r in imported_rel if r in cands_set and r != target_rel_path]
    remaining = [r for r in cands if r not in set(dep_first) and r != target_rel_path]
    ordered = dep_first + remaining
    if target_rel_path not in ordered:
        ordered.append(target_rel_path)
    return ordered
