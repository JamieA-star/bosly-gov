#!/usr/bin/env python3
"""
Bosly Gov v4 - Provenance Helpers

Creates and attaches file snippet provenance metadata to responses.
Python 3.12+
"""

from __future__ import annotations

from typing import Any


def make_provenance_entry(path: str, start: int, end: int, reason: str) -> dict[str, Any]:
    """
    Build a normalized provenance entry.

    Output format:
    {
      "path": str,
      "start_line": int,
      "end_line": int,
      "reason": str
    }
    """
    p = (path or "").strip().replace("\\", "/")
    r = (reason or "").strip()

    try:
        s = int(start)
    except Exception:
        s = 1
    try:
        e = int(end)
    except Exception:
        e = s

    if s < 1:
        s = 1
    if e < 1:
        e = 1
    if e < s:
        s, e = e, s

    return {
        "path": p,
        "start_line": s,
        "end_line": e,
        "reason": r,
    }


def attach_provenance(response: dict[str, Any], provenance: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Attach normalized provenance list to a response dict and return it.

    - Preserves existing response keys.
    - Ensures response['provenance'] is always present as a list.
    """
    if not isinstance(response, dict):
        response = {"ok": False, "error": "Invalid response object."}

    normalized: list[dict[str, Any]] = []

    for item in provenance or []:
        if not isinstance(item, dict):
            continue
        entry = make_provenance_entry(
            path=str(item.get("path", "")),
            start=int(item.get("start_line", item.get("start", 1)) or 1),
            end=int(item.get("end_line", item.get("end", 1)) or 1),
            reason=str(item.get("reason", "")),
        )
        if entry["path"]:
            normalized.append(entry)

    response["provenance"] = normalized
    return response
