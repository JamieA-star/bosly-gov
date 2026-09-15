#!/usr/bin/env python3
"""
Bosly Gov v4 - Memory-First Retrieval (File-based)
Python 3.12+

Storage:
- /mnt/bosly/bosly-data/copilot-knowledge/<slug>/memory.json
- /mnt/bosly/bosly-data/copilot-knowledge/<slug>/chat.json
- /mnt/bosly/bosly-data/copilot-knowledge/<slug>/reports/<year>.md
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

PROJECTS_BASE = Path("/mnt/bosly/bosly-data/copilot-knowledge")
ALLOWED_ITEM_TYPES = {"decision", "pattern", "fact", "incident"}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _validate_slug(slug: str) -> bool:
    if not slug or len(slug) > 50:
        return False
    return all(c.isalnum() or c == "-" for c in slug) and slug == slug.lower()


def _project_path(slug: str) -> Path:
    return PROJECTS_BASE / slug


def _memory_path(slug: str) -> Path:
    return _project_path(slug) / "memory.json"


def _chat_path(slug: str) -> Path:
    return _project_path(slug) / "chat.json"


def _reports_dir(slug: str) -> Path:
    return _project_path(slug) / "reports"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]{2,}", (text or "").lower()))


def _norm_item(raw: dict, idx: int) -> dict[str, Any]:
    content = str(
        raw.get("content")
        or raw.get("text")
        or raw.get("summary")
        or raw.get("message")
        or raw.get("note")
        or ""
    ).strip()

    item_type = str(raw.get("item_type") or raw.get("type") or "fact").strip().lower()
    if item_type not in ALLOWED_ITEM_TYPES:
        item_type = "fact"

    metadata = raw.get("metadata_json")
    if metadata is None:
        metadata = raw.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {"raw": metadata}
    if not isinstance(metadata, dict):
        metadata = {"value": metadata}

    rid = str(raw.get("id") or "").strip()
    if not rid:
        seed = f"{item_type}|{content}|{idx}"
        rid = hashlib.sha256(seed.encode("utf-8", errors="replace")).hexdigest()[:24]

    created_at = str(raw.get("created_at") or "")
    updated_at = str(raw.get("updated_at") or created_at or _now_iso())

    return {
        "id": rid,
        "item_type": item_type,
        "content": content,
        "metadata_json": metadata,
        "created_at": created_at or updated_at,
        "updated_at": updated_at,
    }


def _load_memory_items(project_slug: str) -> list[dict[str, Any]]:
    mem_file = _memory_path(project_slug)
    data = _read_json(mem_file, default=[])
    out: list[dict[str, Any]] = []

    if isinstance(data, list):
        for i, row in enumerate(data):
            if isinstance(row, dict):
                out.append(_norm_item(row, i))
            elif isinstance(row, str):
                out.append(_norm_item({"content": row, "item_type": "fact", "metadata_json": {}}, i))
    elif isinstance(data, dict):
        if isinstance(data.get("memory"), list):
            for i, row in enumerate(data["memory"]):
                if isinstance(row, dict):
                    out.append(_norm_item(row, i))
                elif isinstance(row, str):
                    out.append(_norm_item({"content": row, "item_type": "fact"}, i))
        else:
            i = 0
            for k, v in data.items():
                out.append(_norm_item({"item_type": "fact", "content": f"{k}: {v}", "metadata_json": {"source": "memory_object"}}, i))
                i += 1

    return out


def _save_memory_items(project_slug: str, items: list[dict[str, Any]]) -> None:
    mem_file = _memory_path(project_slug)
    _write_json(mem_file, items)


def store_memory_item(item: dict) -> dict:
    slug = str(item.get("project_slug", "")).strip()
    if not _validate_slug(slug):
        return {"ok": False, "error": "Invalid project_slug"}

    item_type = str(item.get("item_type", "fact")).strip().lower()
    if item_type not in ALLOWED_ITEM_TYPES:
        return {"ok": False, "error": f"Invalid item_type: {item_type}"}

    content = str(item.get("content", "")).strip()
    if not content:
        return {"ok": False, "error": "content is required"}

    metadata = item.get("metadata_json", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {"raw": metadata}
    if not isinstance(metadata, dict):
        metadata = {"value": metadata}

    now = _now_iso()
    item_id = str(item.get("id", "")).strip()
    if not item_id:
        seed = f"{slug}|{item_type}|{content}"
        item_id = hashlib.sha256(seed.encode("utf-8", errors="replace")).hexdigest()[:24]

    new_row = {
        "id": item_id,
        "project_slug": slug,
        "item_type": item_type,
        "content": content,
        "metadata_json": metadata,
        "created_at": str(item.get("created_at", now)) or now,
        "updated_at": now,
    }

    rows = _load_memory_items(slug)
    by_id = {r["id"]: r for r in rows}
    by_id[item_id] = new_row
    saved = list(by_id.values())
    saved.sort(key=lambda x: str(x.get("updated_at", "")), reverse=True)

    _save_memory_items(slug, saved)
    return {"ok": True, "id": item_id}


def search_memory(query: str, project_slug: str, limit: int = 10) -> list[dict]:
    q = str(query or "").strip()
    slug = str(project_slug or "").strip()
    if not q or not _validate_slug(slug):
        return []

    lim = max(1, min(int(limit or 10), 100))
    q_tokens = _tokenize(q)
    if not q_tokens:
        return []

    rows = _load_memory_items(slug)
    scored: list[tuple[float, dict[str, Any]]] = []

    for row in rows:
        content = str(row.get("content", ""))
        meta = row.get("metadata_json", {})
        hay = f"{content} {json.dumps(meta, ensure_ascii=False)}".lower()
        h_tokens = _tokenize(hay)
        if not h_tokens:
            continue

        overlap = len(q_tokens & h_tokens)
        if overlap == 0:
            continue

        overlap_ratio = overlap / max(1, len(q_tokens))
        exact_phrase = 1.0 if q.lower() in hay else 0.0
        recency_bonus = 0.05
        type_bonus = 0.08 if row.get("item_type") in ("decision", "pattern") else 0.03
        score = (overlap_ratio * 0.82) + (exact_phrase * 0.10) + recency_bonus + type_bonus

        item = dict(row)
        item["_score"] = round(score, 4)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:lim]]


def get_confidence_score(search_results: list[dict], query: str) -> float:
    if not search_results:
        return 0.0

    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0

    top = search_results[:5]
    weighted = 0.0
    weight_sum = 0.0

    for i, r in enumerate(top):
        base = float(r.get("_score", 0.0) or 0.0)
        hay = f"{r.get('content','')} {json.dumps(r.get('metadata_json', {}), ensure_ascii=False)}"
        overlap = len(q_tokens & _tokenize(hay))
        overlap_ratio = overlap / max(1, len(q_tokens))

        recency_weight = max(0.5, 1.0 - (i * 0.12))
        combined = min(1.0, (base * 0.7) + (overlap_ratio * 0.3))

        weighted += combined * recency_weight
        weight_sum += recency_weight

    if weight_sum <= 0:
        return 0.0
    return round(max(0.0, min(1.0, weighted / weight_sum)), 3)


def build_memory_context(search_results: list[dict]) -> str:
    if not search_results:
        return ""

    lines = ["[Memory hits]"]
    for r in search_results[:10]:
        rid = str(r.get("id", ""))
        typ = str(r.get("item_type", "fact"))
        content = str(r.get("content", "")).strip()
        if len(content) > 280:
            content = content[:280].rstrip() + "..."
        lines.append(f"- ({typ}) {content} [id:{rid}]")
    return "\n".join(lines)


def retrieve_memory_answer(query: str, project_slug: str, intent: str) -> dict:
    results = search_memory(query=query, project_slug=project_slug, limit=10)
    conf = get_confidence_score(results, query)
    mem_context = build_memory_context(results)

    mode = "llm_fallback"
    answer = ""
    clarification = None

    if conf >= 0.70:
        mode = "memory_only"
        answer = "I can answer this directly from project memory.\n\n" + mem_context
    elif conf >= 0.45:
        mode = "memory_plus_clarification"
        answer = "I found relevant memory, but I need quick clarification for accuracy.\n\n" + mem_context
        clarification = "Do you want memory-only output, or should I include latest code context before finalizing?"
    else:
        mode = "llm_fallback"

    return {
        "ok": True,
        "mode": mode,
        "intent": str(intent or "general"),
        "confidence": conf,
        "search_results": results,
        "memory_context": mem_context,
        "answer": answer,
        "clarification": clarification,
    }
