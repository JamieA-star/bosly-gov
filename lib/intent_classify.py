# lib/intent_classify.py
#
# Classifies an unanswered chatbot question into one of four labels:
# bug, feature, question, other.
#
# Consumers:
#   - evolve_feedback.py — the weekly digest, groups unknown intents
#     by label instead of by exact text
#   - /usr/local/bin/bosly — the orientation, via the digest's
#     --summary flag
#
# Rules are data. To teach the classifier a new signal, add a pattern
# to the relevant rule below — not a new branch in code. First match
# wins; order matters, and the order is visible in RULES.
#
# Run standalone to see the classifier against the current log:
#   python3 -m lib.intent_classify

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

UNKNOWN_INTENTS_PATH = Path(
    "/mnt/bosly/bosly-data/.data/governor/unknown-intents.jsonl"
)


@dataclass(frozen=True)
class Rule:
    label: str
    description: str
    patterns: list[re.Pattern[str]] = field(default_factory=list)


@dataclass(frozen=True)
class Classification:
    label: str
    matched: str | None
    rule: str


# First matching rule wins. Ordered: bug, feature, question, other.
RULES: list[Rule] = [
    Rule(
        label="bug",
        description="Something is broken — it failed, it is wrong, it changed, it will not do what it should.",
        patterns=[
            re.compile(r"\bfailed\b", re.I),
            re.compile(r"\bfail(ing|ure)?\b", re.I),
            re.compile(r"\bcut(s|ting)? off\b", re.I),
            re.compile(r"\bdoes ?n[o']t work\b", re.I),
            re.compile(r"\bdoes ?not work\b", re.I),
            re.compile(r"\bis ?n[o']t work", re.I),
            re.compile(r"\bwon[o']?t\b.*\bwork\b", re.I),
            re.compile(r"\berror\b", re.I),
            re.compile(r"\bbroken\b", re.I),
            re.compile(r"\bwrong\b", re.I),
            re.compile(r"\bchanges? .*?(back|further|wrong)\b", re.I),
            re.compile(r"\bthe more i .* the (further|more)\b", re.I),
            re.compile(r"\bcut off\b", re.I),
        ],
    ),
    Rule(
        label="feature",
        description="A request for something that does not exist yet.",
        patterns=[
            re.compile(r"\bwould be (good|nice|great|useful|helpful)\b", re.I),
            re.compile(r"\bit would be\b", re.I),
            re.compile(r"\bcan you add\b", re.I),
            re.compile(r"\bcould you add\b", re.I),
            re.compile(r"\bplease add\b", re.I),
            re.compile(r"\bis there a way\b", re.I),
            re.compile(r"\bi wish\b", re.I),
            re.compile(r"\bi[' ]?d like (a|to be able)\b", re.I),
            re.compile(r"\b(it'?s|its) not possible\b", re.I),
            re.compile(r"\bevery (week|month|day)\b", re.I),
            re.compile(r"\bbi-?weekly\b", re.I),
            re.compile(r"\brecurring\b", re.I),
            re.compile(r"\bselect every\b", re.I),
        ],
    ),
    Rule(
        label="question",
        description="The user is asking the chatbot for information it does not have a workflow for.",
        patterns=[
            re.compile(r"^\s*(hi|hello|hey|morning|afternoon|evening)\b", re.I),
            re.compile(r"\bwhat can you (help|do)\b", re.I),
            re.compile(r"\bwhat can you help me with\b", re.I),
            re.compile(r"\bhow do i\b", re.I),
            re.compile(r"\bhow can i\b", re.I),
            re.compile(r"\bcan you tell me\b", re.I),
            re.compile(r"\bcan you (help|show|explain)\b", re.I),
            re.compile(r"\bwhat('?s| is) the\b", re.I),
        ],
    ),
    Rule(
        label="other",
        description="Fallback. If this grows, the rules above need attention.",
        patterns=[],
    ),
]


def classify(message: str) -> Classification:
    text = (message or "").strip()
    for rule in RULES:
        for pattern in rule.patterns:
            if pattern.search(text):
                return Classification(
                    label=rule.label,
                    matched=pattern.pattern,
                    rule=rule.description,
                )
        if not rule.patterns:
            return Classification(
                label=rule.label, matched=None, rule=rule.description
            )
    return Classification(label="other", matched=None, rule="fallback")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _main() -> int:
    rows = read_jsonl(UNKNOWN_INTENTS_PATH)
    if not rows:
        print(f"no rows in {UNKNOWN_INTENTS_PATH}")
        return 0
    for row in rows:
        msg = str(row.get("message", "")).strip()
        c = classify(msg)
        snippet = msg[:70].replace("\n", " ")
        matched = c.matched or "(fallback)"
        print(f"  [{c.label:8}] {snippet}")
        print(f"             matched: {matched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
