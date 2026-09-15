#!/usr/bin/env python3
"""
Bosly Gov v4 - Multi-pass Answer Verifier
Python 3.12+
"""

from __future__ import annotations

import re
from typing import Any

_WORD_RE = re.compile(r"[a-zA-Z0-9_]{2,}")
_FILE_REF_RE = re.compile(r"[A-Za-z0-9_\-./]+\.(?:ts|tsx|js|jsx|py|json|md|css|html|yml|yaml|sh|prisma)")
_LINE_REF_RE = re.compile(r"(?i)\bL\d+\b|\bline[s]?\s+\d+(?:\s*-\s*\d+)?")
_CODEISH_RE = re.compile(r"[`][^`]+[`]|[A-Za-z_][A-Za-z0-9_]*\s*\(")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def extract_claims(answer: str) -> list[str]:
    if not answer or not answer.strip():
        return []

    text = answer.replace("\r\n", "\n").replace("\r", "\n")
    parts = []

    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        ln = re.sub(r"^\s*[-*]\s+", "", ln)
        ln = re.sub(r"^\s*\d+[.)]\s+", "", ln)
        parts.append(ln)

    claims: list[str] = []
    for p in parts:
        subs = re.split(r"(?<=[.!?])\s+", p)
        for s in subs:
            s = s.strip()
            if len(s) < 18:
                continue
            if (
                any(x in s.lower() for x in ["is", "are", "uses", "reads", "writes", "calls", "returns", "supports", "contains"])
                or _FILE_REF_RE.search(s)
                or _LINE_REF_RE.search(s)
                or _CODEISH_RE.search(s)
            ):
                claims.append(s)

    out: list[str] = []
    seen: set[str] = set()
    for c in claims:
        k = _norm(c)
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def _collect_context_texts(context: dict) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    if not isinstance(context, dict):
        return chunks

    src = context.get("sources", {})
    if isinstance(src, dict):
        for k in ("accord", "report", "memory", "recent_chat", "file_snippets", "user_message"):
            v = src.get(k, "")
            if isinstance(v, str) and v.strip():
                chunks.append((k, v))

    for k in ("accord", "report", "memory", "recent_chat", "file_snippets"):
        v = context.get(k, "")
        if isinstance(v, str) and v.strip():
            chunks.append((k, v))

    return chunks


def _best_overlap_score(claim: str, chunk: str) -> float:
    ct = set(_WORD_RE.findall(_norm(claim)))
    xt = set(_WORD_RE.findall(_norm(chunk)))
    if not ct or not xt:
        return 0.0
    inter = len(ct & xt)
    return inter / max(1, len(ct))


def _extract_needed_file_hint(claim: str) -> str | None:
    m = _FILE_REF_RE.search(claim or "")
    if m:
        return m.group(0)
    return None


def check_claim_against_context(claim: str, context: dict) -> dict:
    c = (claim or "").strip()
    if not c:
        return {
            "claim": c,
            "supported": False,
            "support_score": 0.0,
            "citations": [],
            "needed_file": None,
            "reason": "empty_claim",
        }

    chunks = _collect_context_texts(context)
    if not chunks:
        return {
            "claim": c,
            "supported": False,
            "support_score": 0.0,
            "citations": [],
            "needed_file": _extract_needed_file_hint(c),
            "reason": "no_context_available",
        }

    prov = context.get("provenance", [])
    prov_by_path: dict[str, tuple[int, int]] = {}
    if isinstance(prov, list):
        for p in prov:
            if not isinstance(p, dict):
                continue
            path = str(p.get("path", "")).strip()
            if not path:
                continue
            s = int(p.get("start_line", 1) or 1)
            e = int(p.get("end_line", s) or s)
            prov_by_path[path] = (s, e)

    best = 0.0
    best_label = ""
    for label, text in chunks:
        score = _best_overlap_score(c, text)
        if score > best:
            best = score
            best_label = label

    supported = best >= 0.45
    weak_supported = 0.30 <= best < 0.45

    citations: list[str] = []
    for path, (s, e) in prov_by_path.items():
        if path.lower() in c.lower() or path.split("/")[-1].lower() in c.lower():
            citations.append(f"{path}:{s}-{e}")

    if not citations and best_label:
        citations.append(f"context:{best_label}")

    needed_file = None
    reason = "supported" if supported else ("weak_support" if weak_supported else "unverifiable")
    if not supported:
        needed_file = _extract_needed_file_hint(c)

    return {
        "claim": c,
        "supported": supported,
        "support_score": round(best, 3),
        "citations": citations,
        "needed_file": needed_file,
        "reason": reason,
    }


def calculate_confidence(verified_claims: list[dict]) -> float:
    if not verified_claims:
        return 0.35
    total = len(verified_claims)
    strong = sum(1 for x in verified_claims if x.get("supported") is True)
    weak = sum(1 for x in verified_claims if x.get("reason") == "weak_support")
    conf = (strong + 0.5 * weak) / max(1, total)
    return round(float(conf), 3)


def verify_answer(answer: str, context: dict) -> dict:
    claims = extract_claims(answer)
    checked = [check_claim_against_context(c, context) for c in claims]
    confidence = calculate_confidence(checked)

    needed_files = []
    for c in checked:
        nf = c.get("needed_file")
        if nf and nf not in needed_files:
            needed_files.append(nf)

    citations = []
    seen = set()
    for c in checked:
        for cit in c.get("citations", []) or []:
            if cit not in seen:
                seen.add(cit)
                citations.append(cit)

    return {
        "ok": True,
        "claims": checked,
        "confidence": confidence,
        "citations": citations,
        "needed_files": needed_files,
        "unverifiable_count": sum(1 for c in checked if not c.get("supported")),
        "supported_count": sum(1 for c in checked if c.get("supported")),
        "total_claims": len(checked),
    }
