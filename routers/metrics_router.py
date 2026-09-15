#!/usr/bin/env python3
"""
Bosly Gov v4 - Metrics Router (Phase 3 + P3 status split)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

SESSIONS_DIR = Path("/mnt/bosly/bosly-data/.data/governor/agent-sessions/sessions")


def _load_sessions(limit: int = 500) -> List[Dict[str, Any]]:
    if not SESSIONS_DIR.exists():
        return []
    files = sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: List[Dict[str, Any]] = []
    for p in files[: max(1, min(limit, 2000))]:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8", errors="replace")))
        except Exception:
            continue
    return out


def get_metrics(limit: int = 500) -> Dict[str, Any]:
    sessions = _load_sessions(limit=limit)
    if not sessions:
        return {
            "ok": True,
            "sample_size": 0,
            "terminal_success_rate": None,
            "pipeline_completion_rate": None,
            "mean_attempts_to_success": None,
            "consent_approve_rate": None,
            "deploy_success_rate": None,
            "status_counts": {},
        }

    status_counts: Dict[str, int] = {}
    done = 0
    done_with_deploy_failure = 0
    failed = 0
    awaiting = 0
    approve_events = 0
    deny_events = 0
    deploy_attempts = 0
    deploy_successes = 0
    attempts_success_total = 0
    attempts_success_n = 0

    for s in sessions:
        status = str(s.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

        if status == "done":
            done += 1
        elif status == "done_with_deploy_failure":
            done_with_deploy_failure += 1
        elif status == "failed":
            failed += 1
        elif status == "awaiting_consent":
            awaiting += 1

        attempts = s.get("attempts") if isinstance(s.get("attempts"), list) else []
        if status in {"done", "done_with_deploy_failure"} and attempts:
            attempts_success_total += len(attempts)
            attempts_success_n += 1

        events = s.get("events") if isinstance(s.get("events"), list) else []
        for ev in events:
            k = str((ev or {}).get("kind") or "")
            if k == "consent_denied":
                deny_events += 1

        result = s.get("result") if isinstance(s.get("result"), dict) else {}
        apply_res = result.get("consent_apply_result") if isinstance(result.get("consent_apply_result"), dict) else None
        if apply_res is not None:
            approve_events += 1

        deploy = result.get("deploy") if isinstance(result.get("deploy"), dict) else None
        if deploy and deploy.get("attempted"):
            deploy_attempts += 1
            if deploy.get("success"):
                deploy_successes += 1

    total_terminal = done + done_with_deploy_failure + failed
    terminal_success_rate = ((done + done_with_deploy_failure) / total_terminal) if total_terminal > 0 else None
    pipeline_denominator = done + done_with_deploy_failure + failed + awaiting
    pipeline_completion_rate = ((done + done_with_deploy_failure) / pipeline_denominator) if pipeline_denominator > 0 else None
    mean_attempts = (attempts_success_total / attempts_success_n) if attempts_success_n > 0 else None
    consent_approve_rate = (approve_events / (approve_events + deny_events)) if (approve_events + deny_events) > 0 else None
    deploy_success_rate = (deploy_successes / deploy_attempts) if deploy_attempts > 0 else None

    return {
        "ok": True,
        "sample_size": len(sessions),
        "terminal_success_rate": terminal_success_rate,
        "pipeline_completion_rate": pipeline_completion_rate,
        "fix_success_rate": terminal_success_rate,  # backward-compat
        "mean_attempts_to_success": mean_attempts,
        "consent_approve_rate": consent_approve_rate,
        "deploy_success_rate": deploy_success_rate,
        "status_counts": status_counts,
        "awaiting_consent_count": awaiting,
        "done_with_deploy_failure_count": done_with_deploy_failure,
    }
