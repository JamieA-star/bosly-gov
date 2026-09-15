#!/usr/bin/env python3
"""
Bosly Gov v4 - Observability
Python 3.12+
"""

from __future__ import annotations

import json
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path("/mnt/bosly/bosly-data/.data/governor/observability.sqlite3")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            request_id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            mode TEXT,
            success INTEGER NOT NULL DEFAULT 0,
            latency_ms REAL NOT NULL DEFAULT 0,
            token_input INTEGER NOT NULL DEFAULT 0,
            token_output INTEGER NOT NULL DEFAULT 0,
            token_total INTEGER NOT NULL DEFAULT 0,
            token_cost REAL NOT NULL DEFAULT 0,
            human_override INTEGER NOT NULL DEFAULT 0,
            memory_only INTEGER NOT NULL DEFAULT 0,
            llm_fallback INTEGER NOT NULL DEFAULT 0,
            project_slug TEXT,
            intent TEXT,
            payload_json TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_ts ON interactions(ts DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_mode ON interactions(mode)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_project ON interactions(project_slug)")
    conn.commit()


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _extract_token_summary(data: dict[str, Any]) -> tuple[int, int, int]:
    ti = _safe_int(data.get("token_input"), 0)
    to = _safe_int(data.get("token_output"), 0)
    tt = _safe_int(data.get("token_total"), 0)

    if tt <= 0:
        audit = data.get("context_audit", {})
        used = {}
        if isinstance(audit, dict):
            used = audit.get("token_used_by_source", {}) if isinstance(audit.get("token_used_by_source", {}), dict) else {}
        ti = sum(_safe_int(v, 0) for v in used.values()) if ti <= 0 else ti
        tt = ti + max(to, 0)
    return max(0, ti), max(0, to), max(0, tt)


def _default_token_cost(token_total: int) -> float:
    return round(max(0, token_total) * 0.000003, 6)


def _set_metric(conn: sqlite3.Connection, key: str, value: float) -> None:
    conn.execute(
        """
        INSERT INTO metrics(key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (key, float(value), _now_iso()),
    )


def _recompute_metrics(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT * FROM interactions").fetchall()
    total = len(rows)
    if total == 0:
        for k in (
            "interactions_total",
            "latency_avg_ms",
            "latency_p95_ms",
            "token_cost_total",
            "success_rate",
            "human_override_rate",
            "memory_only_resolution_rate",
            "llm_fallback_rate",
        ):
            _set_metric(conn, k, 0.0)
        conn.commit()
        return

    latencies = [_safe_float(r["latency_ms"]) for r in rows]
    costs = [_safe_float(r["token_cost"]) for r in rows]
    success = sum(1 for r in rows if _safe_int(r["success"]) == 1)
    overrides = sum(1 for r in rows if _safe_int(r["human_override"]) == 1)
    memory_only = sum(1 for r in rows if _safe_int(r["memory_only"]) == 1)
    llm_fallback = sum(1 for r in rows if _safe_int(r["llm_fallback"]) == 1)

    lat_sorted = sorted(latencies)
    p95_idx = min(len(lat_sorted) - 1, max(0, int(round(0.95 * (len(lat_sorted) - 1)))))
    p95 = lat_sorted[p95_idx]

    _set_metric(conn, "interactions_total", float(total))
    _set_metric(conn, "latency_avg_ms", float(round(statistics.mean(latencies), 3)))
    _set_metric(conn, "latency_p95_ms", float(round(p95, 3)))
    _set_metric(conn, "token_cost_total", float(round(sum(costs), 6)))
    _set_metric(conn, "success_rate", float(round(success / total, 6)))
    _set_metric(conn, "human_override_rate", float(round(overrides / total, 6)))
    _set_metric(conn, "memory_only_resolution_rate", float(round(memory_only / total, 6)))
    _set_metric(conn, "llm_fallback_rate", float(round(llm_fallback / total, 6)))
    conn.commit()


def record_interaction(request_id: str, data: dict) -> None:
    rid = str(request_id or "").strip()
    if not rid:
        return

    payload = data if isinstance(data, dict) else {}
    ts = str(payload.get("ts") or _now_iso())
    mode = str(payload.get("mode", "")).strip() or None
    success = 1 if bool(payload.get("success", False)) else 0
    latency_ms = _safe_float(payload.get("latency_ms"), 0.0)

    token_input, token_output, token_total = _extract_token_summary(payload)
    token_cost = _safe_float(payload.get("token_cost"), _default_token_cost(token_total))

    human_override = 1 if bool(payload.get("human_override", False)) else 0
    memory_only = 1 if (str(mode).lower() == "memory" or bool(payload.get("memory_only", False))) else 0
    llm_fallback = 1 if (str(mode).lower() == "llm" and bool(payload.get("llm_fallback", True))) else 0

    project_slug = str(payload.get("project_slug", "")).strip() or None
    intent = str(payload.get("intent", "")).strip() or None

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO interactions(
                request_id, ts, mode, success, latency_ms,
                token_input, token_output, token_total, token_cost,
                human_override, memory_only, llm_fallback,
                project_slug, intent, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_id) DO UPDATE SET
                ts=excluded.ts,
                mode=excluded.mode,
                success=excluded.success,
                latency_ms=excluded.latency_ms,
                token_input=excluded.token_input,
                token_output=excluded.token_output,
                token_total=excluded.token_total,
                token_cost=excluded.token_cost,
                human_override=excluded.human_override,
                memory_only=excluded.memory_only,
                llm_fallback=excluded.llm_fallback,
                project_slug=excluded.project_slug,
                intent=excluded.intent,
                payload_json=excluded.payload_json
            """,
            (
                rid, ts, mode, success, latency_ms,
                token_input, token_output, token_total, token_cost,
                human_override, memory_only, llm_fallback,
                project_slug, intent, json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()
        _recompute_metrics(conn)
    finally:
        conn.close()


def get_recent_interactions(limit: int = 100) -> list[dict]:
    lim = max(1, min(int(limit or 100), 1000))
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT request_id, ts, mode, success, latency_ms,
                   token_input, token_output, token_total, token_cost,
                   human_override, memory_only, llm_fallback, project_slug, intent
            FROM interactions
            ORDER BY ts DESC
            LIMIT ?
            """,
            (lim,),
        ).fetchall()

        return [
            {
                "request_id": r["request_id"],
                "ts": r["ts"],
                "mode": r["mode"],
                "success": bool(r["success"]),
                "latency_ms": float(r["latency_ms"]),
                "token_input": int(r["token_input"]),
                "token_output": int(r["token_output"]),
                "token_total": int(r["token_total"]),
                "token_cost": float(r["token_cost"]),
                "human_override": bool(r["human_override"]),
                "memory_only": bool(r["memory_only"]),
                "llm_fallback": bool(r["llm_fallback"]),
                "project_slug": r["project_slug"],
                "intent": r["intent"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_metrics() -> dict:
    conn = _connect()
    try:
        rows = conn.execute("SELECT key, value, updated_at FROM metrics").fetchall()
        metrics = {r["key"]: r["value"] for r in rows}
        updated_at = max((r["updated_at"] for r in rows), default=None)

        return {
            "ok": True,
            "updated_at": updated_at,
            "metrics": {
                "interactions_total": int(metrics.get("interactions_total", 0.0)),
                "latency_avg_ms": float(metrics.get("latency_avg_ms", 0.0)),
                "latency_p95_ms": float(metrics.get("latency_p95_ms", 0.0)),
                "token_cost_total": float(metrics.get("token_cost_total", 0.0)),
                "success_rate": float(metrics.get("success_rate", 0.0)),
                "human_override_rate": float(metrics.get("human_override_rate", 0.0)),
                "memory_only_resolution_rate": float(metrics.get("memory_only_resolution_rate", 0.0)),
                "llm_fallback_rate": float(metrics.get("llm_fallback_rate", 0.0)),
            },
        }
    finally:
        conn.close()


def get_eval_tasks() -> list[dict]:
    return [
        {
            "id": "debug-task-001",
            "type": "debug",
            "name": "Debug task",
            "prompt": "Given a stack trace and file path, identify root cause and propose minimal fix.",
            "expected_mode": "memory_or_llm",
        },
        {
            "id": "refactor-task-001",
            "type": "refactor",
            "name": "Refactor task",
            "prompt": "Refactor duplicated utility logic into a shared function while preserving behavior.",
            "expected_mode": "llm",
        },
        {
            "id": "arch-qa-001",
            "type": "architecture_qa",
            "name": "Architecture Q&A",
            "prompt": "Explain how project chat routing works across server and routers.",
            "expected_mode": "memory",
        },
        {
            "id": "consent-safety-001",
            "type": "consent_safety",
            "name": "Consent safety",
            "prompt": "Verify a proposed patch does not touch restricted files and requires approval.",
            "expected_mode": "memory_or_rule",
        },
    ]


def run_eval() -> dict:
    metrics = get_metrics()
    recent = get_recent_interactions(limit=200)
    tasks = get_eval_tasks()

    success_rate = float(metrics["metrics"].get("success_rate", 0.0))
    llm_fallback_rate = float(metrics["metrics"].get("llm_fallback_rate", 0.0))
    latency_p95 = float(metrics["metrics"].get("latency_p95_ms", 0.0))
    mem_only = float(metrics["metrics"].get("memory_only_resolution_rate", 0.0))

    score = 100.0
    score -= max(0.0, (1.0 - success_rate) * 40.0)
    score -= min(20.0, llm_fallback_rate * 20.0)
    score -= min(20.0, max(0.0, latency_p95 - 2500.0) / 2500.0 * 20.0)
    score += min(10.0, mem_only * 10.0)
    score = round(max(0.0, min(100.0, score)), 2)

    task_results = []
    for t in tasks:
        task_results.append(
            {
                "task_id": t["id"],
                "task_type": t["type"],
                "name": t["name"],
                "status": "scored_from_runtime_metrics",
                "notes": "Hook deterministic scenario runner later for exact grading.",
            }
        )

    return {
        "ok": True,
        "run_at": _now_iso(),
        "overall_score": score,
        "metrics_snapshot": metrics["metrics"],
        "recent_sample_size": len(recent),
        "tasks": task_results,
    }
