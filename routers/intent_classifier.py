#!/usr/bin/env python3
"""
Bosly Gov v4 - Intent Classifier
Python 3.12+
"""

from __future__ import annotations

import re

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "bugfix": [
        "bug", "error", "failing", "fails", "fix", "traceback", "exception",
        "stack trace", "broken", "regression", "not working", "type error",
    ],
    "architecture": [
        "architecture", "design", "structure", "flow", "how does", "how do",
        "system design", "component", "module", "dependency", "refactor plan",
    ],
    "report": [
        "report", "diary", "summary", "summarize", "weekly", "monthly",
        "annual", "retrospective", "notes", "write-up",
    ],
    "ops": [
        "deploy", "deployment", "ci", "pipeline", "build", "infra", "health",
        "uptime", "incident", "rollback", "restart", "ops", "monitoring",
    ],
}


def _score_intents(text: str) -> dict[str, float]:
    t = (text or "").strip().lower()
    scores = {k: 0.0 for k in ["bugfix", "architecture", "report", "ops", "general"]}

    for intent, kws in _INTENT_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                scores[intent] += 1.0

    if re.search(r"\b(src|app|components|pages|routes)/[\w./-]+\.(ts|tsx|js|jsx|py)\b", t):
        scores["bugfix"] += 1.0
    if re.search(r"\bwhy\b.*\barchitecture\b|\bhow\b.*\bwork\b", t):
        scores["architecture"] += 1.0

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] <= 0:
        scores["general"] = 1.0
    return scores


def classify_intent(user_message: str) -> str:
    scores = _score_intents(user_message)
    return max(scores, key=scores.get)


def intent_confidence(user_message: str) -> float:
    scores = _score_intents(user_message)
    ordered = sorted(scores.values(), reverse=True)
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else 0.0
    if top <= 0:
        return 0.2
    conf = 0.5 + min(0.49, (top - second) / max(1.0, top + second))
    return round(conf, 3)
