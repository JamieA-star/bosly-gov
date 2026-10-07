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

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lib.intent_classify import classify


UNKNOWN_INTENTS_PATH = Path(
    "/mnt/bosly/bosly-data/.data/governor/unknown-intents.jsonl"
)
STATUS_PATH = Path(
    "/mnt/bosly/bosly-data/.data/governor/unknown-intents-status.json"
)
FEEDBACK_PATH = Path("/mnt/bosly/bosly-data/logs/feedback.jsonl")


def read_status() -> dict[str, dict[str, Any]]:
    if not STATUS_PATH.exists():
        return {}
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


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


@dataclass
class UnknownIntentGroup:
    key: str
    count: int
    recent: list[dict[str, Any]]


LABEL_ORDER = ["bug", "feature", "question", "other"]


def group_unknown_intents(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {label: [] for label in LABEL_ORDER}
    for row in rows:
        message = str(row.get("message", "")).strip()
        if not message:
            continue
        label = classify(message).label
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(row)
    for label in buckets:
        buckets[label].sort(
            key=lambda r: parse_ts(r.get("ts"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    return buckets


def _label_counts(buckets: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {label: len(items) for label, items in buckets.items()}


def _label_status(
    buckets: dict[str, list[dict[str, Any]]], status: dict[str, dict[str, Any]]
) -> dict[str, tuple[int, int]]:
    """Return {label: (open, fixed)}."""
    out: dict[str, tuple[int, int]] = {}
    for label, items in buckets.items():
        open_n = 0
        fixed_n = 0
        for row in items:
            s = status.get(str(row.get("ts", "")), {}).get("status", "new")
            if s == "fixed":
                fixed_n += 1
            else:
                open_n += 1
        out[label] = (open_n, fixed_n)
    return out


def format_summary(rows: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total = len(rows)
    recent = sum(
        1 for r in rows if (ts := parse_ts(r.get("ts"))) and ts >= week_ago
    )
    buckets = group_unknown_intents(rows)
    counts = _label_counts(buckets)
    status = read_status()
    by_status = _label_status(buckets, status)

    out: list[str] = []
    out.append(f"  Noted: {total} total, {recent} in the last 7 days")
    if total == 0:
        return "\n".join(out)

    parts = []
    for label in LABEL_ORDER:
        n = counts.get(label, 0)
        if n == 0:
            continue
        open_n, fixed_n = by_status.get(label, (n, 0))
        tag = f" ({open_n} open, {fixed_n} fixed)"
        parts.append(f"{label.capitalize()}s: {n}{tag}")
    out.append("  " + "    ".join(parts))

    open_labels = ["feature", "question", "bug", "other"]
    signals: list[str] = []
    for label in open_labels:
        items = [
            r for r in buckets.get(label, [])
            if status.get(str(r.get("ts", "")), {}).get("status", "new") != "fixed"
        ]
        if not items:
            continue
        latest = items[0]
        msg = str(latest.get("message", "")).strip()
        signals.append(f"    - {label}: \"{msg[:80]}\"")
    if signals:
        out.append("  Open signals:")
        out.extend(signals)

    return "\n".join(out)


def format_unknown_intents(rows: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total = len(rows)
    recent = sum(
        1 for r in rows if (ts := parse_ts(r.get("ts"))) and ts >= week_ago
    )
    buckets = group_unknown_intents(rows)
    counts = _label_counts(buckets)
    status = read_status()
    by_status = _label_status(buckets, status)

    out: list[str] = []
    out.append("UNKNOWN INTENTS")
    out.append(f"Total: {total}")
    out.append(f"Last 7 days: {recent}")
    out.append("")

    if total == 0:
        out.append("No unknown intents found.")
        return "\n".join(out)

    for label in LABEL_ORDER:
        items = buckets.get(label, [])
        if not items:
            continue
        open_n, fixed_n = by_status.get(label, (len(items), 0))
        out.append(f"{label.upper()} ({len(items)}, {open_n} open, {fixed_n} fixed)")
        for item in items:
            ts = item.get("ts", "unknown-ts")
            s = status.get(str(item.get("ts", "")), {}).get("status", "new")
            message = str(item.get("message", "")).strip()
            out.append(f"  [{s}] {ts} | {message}")
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
    parser = argparse.ArgumentParser(description="Bosly weekly digest")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="print only the unknown-intents summary (used by the orientation)",
    )
    args = parser.parse_args()

    unknown_rows = read_jsonl(UNKNOWN_INTENTS_PATH)

    if args.summary:
        print(format_summary(unknown_rows))
        return 0

    feedback_rows = read_jsonl(FEEDBACK_PATH)
    print("BOSLY WEEKLY DIGEST")
    print("")
    print(format_unknown_intents(unknown_rows))
    print("")
    print(format_feedback(feedback_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
