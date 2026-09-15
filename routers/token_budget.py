#!/usr/bin/env python3
"""
Bosly Gov v4 - Adaptive Token Budgeting
Python 3.12+
"""

from __future__ import annotations

import math
from typing import Any

_MODEL_CHAR_PER_TOKEN = {
    "claude": 3.8,
    "gpt": 4.0,
    "default": 4.0,
}


def _chars_per_token(model: str) -> float:
    m = (model or "").lower()
    if "claude" in m:
        return _MODEL_CHAR_PER_TOKEN["claude"]
    if "gpt" in m or "o1" in m or "o3" in m:
        return _MODEL_CHAR_PER_TOKEN["gpt"]
    return _MODEL_CHAR_PER_TOKEN["default"]


def estimate_tokens(text: str, model: str) -> int:
    if not text:
        return 0
    cpt = _chars_per_token(model)
    return max(1, math.ceil(len(text) / cpt))


def estimate_message_tokens(messages: list[dict], model: str) -> int:
    total = 0
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "user"))
        content = str(m.get("content", m.get("message", m.get("text", ""))))
        total += 6
        total += estimate_tokens(role, model)
        total += estimate_tokens(content, model)
    total += 3
    return total


def build_budget(total_ctx: int, reserve_output: int) -> dict[str, int]:
    total_ctx = max(1024, int(total_ctx or 0))
    reserve_output = max(256, int(reserve_output or 0))
    if reserve_output >= total_ctx:
        reserve_output = total_ctx // 3
    available_input = max(256, total_ctx - reserve_output)
    return {
        "total_ctx": total_ctx,
        "reserve_output": reserve_output,
        "available_input": available_input,
    }


def allocate_budget(intent: str, available_tokens: int) -> dict[str, int]:
    t = max(256, int(available_tokens or 0))
    i = (intent or "general").strip().lower()

    ratios: dict[str, float] = {
        "accord": 0.10,
        "report": 0.20,
        "memory": 0.15,
        "recent_chat": 0.15,
        "file_snippets": 0.30,
        "user_message": 0.10,
    }

    if i == "bugfix":
        ratios.update({"file_snippets": 0.45, "report": 0.10, "memory": 0.15, "recent_chat": 0.15, "accord": 0.07, "user_message": 0.08})
    elif i == "architecture":
        ratios.update({"file_snippets": 0.35, "report": 0.18, "memory": 0.17, "recent_chat": 0.12, "accord": 0.10, "user_message": 0.08})
    elif i == "report":
        ratios.update({"report": 0.40, "memory": 0.20, "recent_chat": 0.18, "accord": 0.10, "file_snippets": 0.05, "user_message": 0.07})
    elif i == "ops":
        ratios.update({"recent_chat": 0.25, "memory": 0.20, "report": 0.15, "accord": 0.15, "file_snippets": 0.15, "user_message": 0.10})

    raw = {k: int(t * v) for k, v in ratios.items()}
    used = sum(raw.values())
    rem = t - used
    for k in ("file_snippets", "report", "memory", "recent_chat", "accord", "user_message"):
        if rem <= 0:
            break
        raw[k] += 1
        rem -= 1
    return raw


def trim_to_budget(text: str, max_tokens: int, model: str) -> str:
    if not text:
        return ""
    max_tokens = max(1, int(max_tokens or 1))
    if estimate_tokens(text, model) <= max_tokens:
        return text

    cpt = _chars_per_token(model)
    max_chars = max(32, int(max_tokens * cpt))
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncated]..."
