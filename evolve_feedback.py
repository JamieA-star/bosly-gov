#!/usr/bin/env python3
"""
evolve_feedback.py

Standalone, read-only weekly digest for Bosly Gov.

Reads:
  - unknown-intents.jsonl   (questions the chatbot could not answer)
  - feedback.jsonl          (user sentiment + flagged replies)

Outputs:
  - total counts and last-7-days counts
  - crude deterministic grouping of similar unknown intents
  - feedback split by type, with recent flagged reports

No dependencies beyond the Python standard library.
No writes. No network. No AI.

The two logs live under different roots:
  unknown-intents.jsonl  -> /mnt/bosly/bosly-data/.data/governor/
     (hardcoded in lib/workflow/index.ts)
  feedback.jsonl         -> /mnt/bosly/bosly-data/logs/
     (written via dataPath("logs") in app/api/feedback/route.ts)
"""

from __future__ import annotations

import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


UNKNOWN_INTENTS_PATH = Path(
    "/mnt/bosly/bosly-data/.data/governor/unknown-intents.jsonl"
)
FEEDBACK_PATH = Path("/mnt/bosly/bosly-data/logs/feedback.jsonl")


def parse_ts(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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


_DATEISH_RE = re.compile(
    r"""
    \b(
        \d{4}-\d{2}-\d{2} |
        \d{4}/\d{2}/\d{2} |
        \d{1,2}/\d{1,2}/\d{2,4} |
        \d{1,2}:\d{2}(?:\s?[ap]m)? |
        january|february|march|april|may|june|july|august|september|october|november|december |
        mon|tue|wed|thu|fri|sat|sun |
        today|tomorrow|yesterday |
        last\s+week|last\s+month|this\s+month|this\s+week |
        next\s+week|next\s+month
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_NUM_RE = re.compile(r"\b\d+\b")
_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^a-z0-9\s]")


def normalise_message(message: str) -> str:
    msg = message.lower().strip()
    msg = _DATEISH_RE.sub(" ", msg)
    msg = _NUM_RE.sub(" ", msg)
    msg = _PUNCT_RE.sub(" ", msg)
    msg = _SPACE_RE.sub(" ", msg).strip()
    return msg


@dataclass
class UnknownIntentGroup:
    key: str
    count: int
    recent: list[dict[str, Any]]


def group_unknown_intents(rows: list[dict[str, Any]]) -> list[UnknownIntentGroup]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        message = str(row.get("message", "")).strip()
        if not message:
            continue
        key = normalise_message(message)
        if not key:
            key = "(empty after normalisation)"
        buckets[key].append(row)

    groups: list[UnknownIntentGroup] = []
    for key, items in buckets.items():
        items_sorted = sorted(
            items,
            key=lambda r: parse_ts(r.get("ts"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        groups.append(
            UnknownIntentGroup(
                key=key, count=len(items_sorted), recent=items_sorted[:3]
            )
        )
    groups.sort(key=lambda g: (-g.count, g.key))
    return groups


def format_unknown_intents(rows: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total = len(rows)
    recent = sum(
        1 for r in rows if (ts := parse_ts(r.get("ts"))) and ts >= week_ago
    )
    groups = group_unknown_intents(rows)

    out: list[str] = []
    out.append("UNKNOWN INTENTS")
    out.append(f"Total: {total}")
    out.append(f"Last 7 days: {recent}")
    out.append(f"Themes: {len(groups)}")
    out.append("")

    if not groups:
        out.append("No unknown intents found.")
        return "\n".join(out)

    for idx, group in enumerate(groups[:20], start=1):
        out.append(f"{idx}. {group.key}  ({group.count})")
        for item in group.recent:
            ts = item.get("ts", "unknown-ts")
            user_id = item.get("userId", "unknown-user")
            message = str(item.get("message", "")).strip()
            out.append(f"   - {ts} | {user_id} | {message}")
        out.append("")

    return "\n".join(out).rstrip()


def classify_feedback(row: dict[str, Any]) -> str:
    source = str(row.get("source", "")).strip().lower()
    rating = str(row.get("rating", "")).strip().lower()
    text = str(row.get("text", "")).strip().lower()

    if source == "chat_drawer" or rating == "flagged":
        return "chat report / flagged reply"
    if source == "ui":
        return f"ui rating: {rating or 'unknown'}"
    if text:
        return "free-text feedback"
    return "other"


def format_feedback(rows: list[dict[str, Any]]) -> str:
    out: list[str] = []
    out.append("FEEDBACK")
    out.append(f"Total: {len(rows)}")

    if not rows:
        out.append("No feedback found.")
        return "\n".join(out)

    counts = Counter(classify_feedback(r) for r in rows)
    out.append("By type:")
    for key, count in counts.most_common():
        out.append(f"  - {key}: {count}")
    out.append("")

    flagged = [
        r for r in rows if classify_feedback(r) == "chat report / flagged reply"
    ]
    if flagged:
        out.append("Recent flagged reports:")
        flagged_sorted = sorted(
            flagged,
            key=lambda r: parse_ts(r.get("ts"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        for row in flagged_sorted[:10]:
            out.append(
                f"  - {row.get('ts', 'unknown-ts')} | "
                f"{row.get('text', '').strip() or '(no text)'}"
            )
        out.append("")

    return "\n".join(out).rstrip()


def main() -> int:
    unknown_rows = read_jsonl(UNKNOWN_INTENTS_PATH)
    feedback_rows = read_jsonl(FEEDBACK_PATH)

    print("BOSLY WEEKLY DIGEST")
    print("")
    print(format_unknown_intents(unknown_rows))
    print("")
    print(format_feedback(feedback_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
