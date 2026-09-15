#!/usr/bin/env python3
"""
Check: every memory file item is well-formed.

Walks /mnt/bosly/bosly-data/copilot-knowledge/*/memory.json and asserts
each item is a dict with the required fields: id, project_slug,
item_type, content.

Catches the class of bug where the memory consolidator writes
transcript-shaped objects (summary/facts/updatedAt) instead of proper
memory items. Found on 11 September (Keep, one item) and 15 September
(Accord, sixteen items).

Exit 0 if every file is well-formed, 1 otherwise.

Run:
    python3 checks/memory_schema.py
"""

import json
import sys
from pathlib import Path

KNOWLEDGE_ROOT = Path("/mnt/bosly/bosly-data/copilot-knowledge")
REQUIRED_FIELDS = ["id", "project_slug", "item_type", "content"]


def check_file(path: Path) -> tuple[int, int, list[str]]:
    """Returns (total, malformed_count, error_messages)."""
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return (0, 0, [f"{path.name}: could not parse JSON: {e}"])

    if not isinstance(data, list):
        return (0, 0, [f"{path.name}: top level is not a list"])

    malformed = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            malformed.append(f"{path.name}[{i}]: not a dict")
            continue
        missing = [f for f in REQUIRED_FIELDS if f not in item]
        if missing:
            malformed.append(f"{path.name}[{i}]: missing {', '.join(missing)}")

    return (len(data), len(malformed), malformed)


def main() -> int:
    if not KNOWLEDGE_ROOT.exists():
        print(f"FAIL: {KNOWLEDGE_ROOT} does not exist")
        return 1

    memory_files = sorted(KNOWLEDGE_ROOT.glob("*/memory.json"))
    if not memory_files:
        print(f"FAIL: no memory.json files found under {KNOWLEDGE_ROOT}")
        return 1

    print("")
    print("Invariant: memory file schema")
    print("----------------------------------------------------")

    total_items = 0
    total_malformed = 0
    all_errors: list[str] = []

    for path in memory_files:
        slug = path.parent.name
        total, malformed, errors = check_file(path)
        total_items += total
        total_malformed += malformed
        status = "PASS" if malformed == 0 else "FAIL"
        print(f"{status}: {slug}/memory.json ({total} items, {malformed} malformed)")
        all_errors.extend(errors)

    print("")
    if all_errors:
        print("Malformed items:")
        for e in all_errors:
            print(f"  {e}")
        print("")

    print(f"SUMMARY: {len(memory_files)} files, {total_items} items, {total_malformed} malformed")
    print("")
    return 1 if total_malformed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
