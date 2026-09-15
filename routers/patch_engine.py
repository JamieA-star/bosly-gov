#!/usr/bin/env python3
"""
Bosly Gov v4 - Structured Patch Engine
Parses and validates LLM patch outputs in either:
1) JSON edit ops format, or
2) unified diff format.

Applies edits in-memory only (no disk writes here).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

JSON_FENCE_RE = re.compile(r"(?is)^\s*```(?:json)?\s*(.*?)\s*```\s*$")
DIFF_FENCE_RE = re.compile(r"(?is)```(?:diff|patch)?\s*(.*?)\s*```")
HUNK_HEADER_RE = re.compile(r"^@@\s*-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s*@@")

MAX_OPS = 500
MAX_CONTENT_CHARS = 2_000_000


@dataclass
class PatchParseResult:
    ok: bool
    format: str
    errors: List[str]
    edits: List[Dict[str, Any]]
    normalized_raw: str


def _strip_code_fences(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    m = JSON_FENCE_RE.match(s)
    if m:
        return m.group(1).strip()
    # for diff, unwrap all fenced diff blocks and join
    if "```" in s:
        parts = DIFF_FENCE_RE.findall(s)
        if parts:
            return "\n".join(p.strip() for p in parts if p.strip()).strip()
    return s


def normalize_model_output(text: str) -> str:
    """Remove common markdown wrappers and normalize line endings."""
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    elif not isinstance(text, str):
        text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _strip_code_fences(text)
    if len(text) > MAX_CONTENT_CHARS:
        text = text[:MAX_CONTENT_CHARS]
    # ensure valid utf-8 roundtrip
    text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return text.strip()


def _try_parse_json_edits(raw: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
    errs: List[str] = []
    try:
        data = json.loads(raw)
    except Exception as e:
        return False, [], [f"JSON parse error: {e}"]

    if isinstance(data, dict) and isinstance(data.get("edits"), list):
        ops = data["edits"]
    elif isinstance(data, list):
        ops = data
    else:
        return False, [], ["JSON must be an array of edit ops or object with key 'edits'."]

    if len(ops) > MAX_OPS:
        return False, [], [f"Too many edit ops ({len(ops)} > {MAX_OPS})."]

    out: List[Dict[str, Any]] = []
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            errs.append(f"Edit #{i}: op must be object.")
            continue
        kind = str(op.get("op", "")).strip().lower()
        if kind not in {"replace", "insert", "delete", "set_file", "append"}:
            errs.append(f"Edit #{i}: unsupported op '{kind}'.")
            continue

        if kind == "set_file":
            content = op.get("content", "")
            if not isinstance(content, str):
                errs.append(f"Edit #{i}: set_file.content must be string.")
                continue
            out.append({"op": "set_file", "content": content})
            continue

        if kind == "append":
            content = op.get("content", "")
            if not isinstance(content, str):
                errs.append(f"Edit #{i}: append.content must be string.")
                continue
            out.append({"op": "append", "content": content})
            continue

        line = op.get("line")
        if not isinstance(line, int) or line < 1:
            errs.append(f"Edit #{i}: line must be int >= 1.")
            continue

        if kind in {"replace", "insert"}:
            text = op.get("text", "")
            if not isinstance(text, str):
                errs.append(f"Edit #{i}: text must be string.")
                continue
            out.append({"op": kind, "line": line, "text": text})
        elif kind == "delete":
            count = op.get("count", 1)
            if not isinstance(count, int) or count < 1:
                errs.append(f"Edit #{i}: count must be int >= 1.")
                continue
            out.append({"op": "delete", "line": line, "count": count})

    return len(errs) == 0, out, errs


def _parse_unified_diff(raw: str, expected_rel_path: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
    """
    Parse a simple unified diff and convert to set_file by applying hunks in-memory.
    For safety/clarity in Phase 1, we only accept diffs targeting the expected file path.
    """
    lines = raw.splitlines()
    errs: List[str] = []

    old_path = None
    new_path = None
    hunks: List[Tuple[int, int, int, int, List[str]]] = []

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("--- "):
            old_path = ln[4:].strip()
            i += 1
            continue
        if ln.startswith("+++ "):
            new_path = ln[4:].strip()
            i += 1
            continue
        m = HUNK_HEADER_RE.match(ln)
        if m:
            old_start = int(m.group(1))
            old_count = int(m.group(2) or "1")
            new_start = int(m.group(3))
            new_count = int(m.group(4) or "1")
            i += 1
            body: List[str] = []
            while i < len(lines):
                x = lines[i]
                if x.startswith("@@ "):
                    break
                if x.startswith(("--- ", "+++ ")):
                    break
                body.append(x)
                i += 1
            hunks.append((old_start, old_count, new_start, new_count, body))
            continue
        i += 1

    if not hunks:
        return False, [], ["No valid diff hunks found."]

    # Validate file target
    expected_norm = expected_rel_path.replace("\\", "/").lstrip("./")
    parsed_new = (new_path or "").replace("b/", "").replace("a/", "").strip()
    parsed_new = parsed_new.lstrip("./")
    if parsed_new and parsed_new != expected_norm:
        errs.append(f"Diff targets '{parsed_new}', expected '{expected_norm}'.")

    # We convert hunks to line ops (replace/insert/delete) for visibility
    # and final apply will use apply_diff_to_text directly.
    edits: List[Dict[str, Any]] = [{"op": "unified_diff", "raw_diff": raw}]
    return len(errs) == 0, edits, errs


def parse_patch_output(raw_model_output: str, expected_rel_path: str) -> PatchParseResult:
    normalized = normalize_model_output(raw_model_output)
    if not normalized:
        return PatchParseResult(
            ok=False,
            format="unknown",
            errors=["Empty model output after normalization."],
            edits=[],
            normalized_raw="",
        )

    # Try JSON first
    ok_json, json_ops, json_errs = _try_parse_json_edits(normalized)
    if ok_json:
        return PatchParseResult(ok=True, format="json_edits", errors=[], edits=json_ops, normalized_raw=normalized)

    # Try unified diff
    if ("@@ " in normalized and ("--- " in normalized or "+++ " in normalized)) or normalized.startswith("diff --git"):
        ok_diff, diff_ops, diff_errs = _parse_unified_diff(normalized, expected_rel_path=expected_rel_path)
        if ok_diff:
            return PatchParseResult(ok=True, format="unified_diff", errors=[], edits=diff_ops, normalized_raw=normalized)
        retry_hint = "Unified diff parse failed. Retry with JSON set_file format only: {'edits':[{'op':'set_file','content':'<full file content>'}]}"
        return PatchParseResult(ok=False, format="unified_diff", errors=[*diff_errs, retry_hint], edits=[], normalized_raw=normalized)

    return PatchParseResult(
        ok=False,
        format="unknown",
        errors=["Output is neither valid JSON edits nor unified diff.", *json_errs[:3]],
        edits=[],
        normalized_raw=normalized,
    )


def apply_json_edits_to_text(original: str, edits: List[Dict[str, Any]]) -> Tuple[bool, str, List[str]]:
    errs: List[str] = []
    text = original.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    # single full-file set shortcut
    if len(edits) == 1 and edits[0].get("op") == "set_file":
        new_text = str(edits[0].get("content", ""))
        return True, new_text, []

    for idx, op in enumerate(edits):
        kind = op.get("op")
        if kind == "set_file":
            lines = str(op.get("content", "")).split("\n")
            continue

        if kind == "append":
            content = str(op.get("content", ""))
            lines.append(content)
            continue

        line_no = int(op.get("line", 0))
        if line_no < 1:
            errs.append(f"Edit #{idx}: invalid line {line_no}")
            continue

        i = line_no - 1
        if kind == "replace":
            if i >= len(lines):
                errs.append(f"Edit #{idx}: replace line {line_no} out of range.")
                continue
            repl = str(op.get("text", ""))
            lines[i:i + 1] = repl.split("\n")
        elif kind == "insert":
            ins = str(op.get("text", ""))
            if i > len(lines):
                errs.append(f"Edit #{idx}: insert line {line_no} out of range.")
                continue
            lines[i:i] = ins.split("\n")
        elif kind == "delete":
            count = int(op.get("count", 1))
            if i >= len(lines):
                errs.append(f"Edit #{idx}: delete line {line_no} out of range.")
                continue
            del lines[i:i + count]
        else:
            errs.append(f"Edit #{idx}: unsupported op {kind}")

    return len(errs) == 0, "\n".join(lines), errs


def apply_unified_diff_to_text(original: str, diff_text: str) -> Tuple[bool, str, List[str]]:
    """
    Minimal unified-diff applier for single file patches.
    """
    errs: List[str] = []
    src = original.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: List[str] = []
    i_src = 0

    lines = diff_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = HUNK_HEADER_RE.match(ln)
        if not m:
            i += 1
            continue

        old_start = int(m.group(1))
        # copy unchanged region before hunk
        target_src_idx = old_start - 1
        if target_src_idx < i_src or target_src_idx > len(src):
            errs.append(f"Invalid hunk position near '{ln}'")
            return False, original, errs
        out.extend(src[i_src:target_src_idx])
        i_src = target_src_idx
        i += 1

        while i < len(lines):
            x = lines[i]
            if x.startswith("@@ "):
                break
            if x.startswith(("--- ", "+++ ", "diff --git")):
                break
            if not x:
                # treat empty as context line with empty content only if prefixed;
                # bare empty lines in diff bodies are uncommon; keep safe
                i += 1
                continue

            prefix = x[0]
            body = x[1:] if len(x) > 1 else ""
            if prefix == " ":
                if i_src >= len(src) or src[i_src] != body:
                    errs.append("Context mismatch while applying diff.")
                    return False, original, errs
                out.append(src[i_src])
                i_src += 1
            elif prefix == "-":
                if i_src >= len(src) or src[i_src] != body:
                    errs.append("Delete mismatch while applying diff.")
                    return False, original, errs
                i_src += 1
            elif prefix == "+":
                out.append(body)
            elif prefix == "\\":
                # "\ No newline at end of file" -> ignore
                pass
            else:
                # unknown line, be strict
                errs.append(f"Unexpected diff line prefix: {prefix}")
                return False, original, errs
            i += 1

    out.extend(src[i_src:])
    return True, "\n".join(out), []


def apply_patch_to_text(original_text: str, parse_result: PatchParseResult) -> Tuple[bool, str, List[str]]:
    if not parse_result.ok:
        return False, original_text, list(parse_result.errors)

    if parse_result.format == "json_edits":
        return apply_json_edits_to_text(original_text, parse_result.edits)

    if parse_result.format == "unified_diff":
        diff_raw = ""
        if parse_result.edits and isinstance(parse_result.edits[0], dict):
            diff_raw = str(parse_result.edits[0].get("raw_diff", ""))
        return apply_unified_diff_to_text(original_text, diff_raw)

    return False, original_text, [f"Unsupported patch format: {parse_result.format}"]


def build_unified_diff(original_text: str, updated_text: str, rel_path: str) -> str:
    import difflib

    old_lines = original_text.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
    new_lines = updated_text.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
        n=3,
    )
    return "".join(diff)
