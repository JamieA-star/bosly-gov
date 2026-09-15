#!/usr/bin/env python3
"""
Bosly Gov v4 - Snippet Cache

In-memory, thread-safe snippet cache with TTL expiration.
Python 3.12+
"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any

_CACHE: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()


def get_cache_key(path: str, start: int | None, end: int | None, mtime: float | int | None) -> str:
    normalized_path = (path or "").strip().replace("\\", "/")
    start_s = "" if start is None else str(int(start))
    end_s = "" if end is None else str(int(end))
    mtime_s = "" if mtime is None else f"{float(mtime):.6f}"
    raw = f"{normalized_path}|{start_s}|{end_s}|{mtime_s}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()


def get_cached_snippet(key: str) -> dict | None:
    if not key:
        return None
    now = time.time()
    with _LOCK:
        entry = _CACHE.get(key)
        if not entry:
            return None
        expires_at = float(entry.get("expires_at", 0))
        if expires_at <= now:
            _CACHE.pop(key, None)
            return None
        value = entry.get("value")
        return value if isinstance(value, dict) else None


def set_cached_snippet(key: str, value: dict, ttl_s: int = 300) -> None:
    if not key or not isinstance(value, dict):
        return
    ttl = int(ttl_s)
    if ttl <= 0:
        with _LOCK:
            _CACHE.pop(key, None)
        return
    now = time.time()
    expires_at = now + ttl
    with _LOCK:
        _CACHE[key] = {
            "value": value,
            "created_at": now,
            "expires_at": expires_at,
        }


def evict_expired() -> None:
    now = time.time()
    with _LOCK:
        expired_keys = [k for k, v in _CACHE.items() if float(v.get("expires_at", 0)) <= now]
        for k in expired_keys:
            _CACHE.pop(k, None)
