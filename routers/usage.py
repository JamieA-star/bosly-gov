"""routers/usage.py — every model call, costed, on disk.

A bill tells you what you spent after it is gone. This writes one line
per call with the model, the tokens and the batch flag, prices it from
a table, and lets a day, a build or a conversation be totalled. The
table is the provider's published rate; the Admin API reconciles it
monthly, so the table cannot drift unnoticed.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

USAGE = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/usage.jsonl")

# Per million tokens, published rates. Batch is half the standard rate.
RATES: Dict[str, Dict[str, float]] = {
    "claude-haiku-5-5": {"in": 0.10, "out": 0.50, "batch_in": 0.05, "batch_out": 0.25},
    "claude-haiku-4-5-20251001": {"in": 1.00, "out": 5.00, "batch_in": 0.50, "batch_out": 2.50},
    "claude-sonnet-5": {"in": 3.00, "out": 15.00, "batch_in": 1.50, "batch_out": 7.50},
}
GBP_PER_USD = 0.79


def rate_for(model: str) -> Optional[Dict[str, float]]:
    for k in RATES:
        if k in model or model in k:
            return RATES[k]
    return None


def cost_pence(model: str, usage: Dict[str, Any], batch: bool = False) -> float:
    """The cost of one call, in pence, from the table."""
    r = rate_for(model)
    if not r:
        return -1.0
    inp = usage.get("input_tokens", 0) or 0
    out = usage.get("output_tokens", 0) or 0
    cr = usage.get("cache_read_input_tokens", 0) or 0
    cw = usage.get("cache_creation_input_tokens", 0) or 0
    in_rate = r["batch_in"] if batch else r["in"]
    out_rate = r["batch_out"] if batch else r["out"]
    # A cache read is a tenth of input; a cache write is a quarter more.
    usd = (
        (inp / 1_000_000) * in_rate
        + (out / 1_000_000) * out_rate
        + (cr / 1_000_000) * (in_rate / 10)
        + (cw / 1_000_000) * (in_rate * 1.25)
    )
    return round(usd * GBP_PER_USD * 100, 4)


def record(model: str, usage: Dict[str, Any], batch: bool = False,
           label: str = "", build: str = "") -> Dict[str, Any]:
    """Write one line. Never raises: a tracking failure is not a dead butler."""
    try:
        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model": model,
            "in": usage.get("input_tokens", 0) or 0,
            "out": usage.get("output_tokens", 0) or 0,
            "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
            "cache_write": usage.get("cache_creation_input_tokens", 0) or 0,
            "batch": bool(batch),
            "label": label,
            "build": build,
            "pence": cost_pence(model, usage, batch),
        }
        USAGE.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry
    except Exception:
        return {}


def _read(since: Optional[str] = None) -> List[Dict[str, Any]]:
    if not USAGE.exists():
        return []
    out = []
    for line in USAGE.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if since and e.get("ts", "") < since:
            continue
        out.append(e)
    return out


def total(since: Optional[str] = None) -> Dict[str, Any]:
    """Every call since a date, totalled by model and by build."""
    rows = _read(since)
    by_model: Dict[str, Dict[str, Any]] = {}
    by_build: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        m = by_model.setdefault(r["model"], {"turns": 0, "pence": 0.0, "batch": 0})
        m["turns"] += 1
        m["pence"] = round(m["pence"] + r.get("pence", 0), 4)
        m["batch"] += 1 if r.get("batch") else 0
        b = by_build.setdefault(r.get("build") or "conversation", {"turns": 0, "pence": 0.0})
        b["turns"] += 1
        b["pence"] = round(b["pence"] + r.get("pence", 0), 4)
    return {
        "ok": True,
        "result": {
            "turns": len(rows),
            "pence": round(sum(r.get("pence", 0) for r in rows), 4),
            "by_model": by_model,
            "by_build": by_build,
        },
    }


def trend(days: int = 14) -> Dict[str, Any]:
    """Average pence per turn, this week against last."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    this_week = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    last_week = (now - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    a = total(this_week)["result"]
    b = total(last_week)["result"]
    # b includes a; subtract for last week alone
    b_turns = b["turns"] - a["turns"]
    b_pence = round(b["pence"] - a["pence"], 4)
    a_avg = round(a["pence"] / a["turns"], 4) if a["turns"] else 0
    b_avg = round(b_pence / b_turns, 4) if b_turns else 0
    rising = a_avg > b_avg and b_turns > 0
    return {
        "ok": True,
        "result": {
            "this_week": {"turns": a["turns"], "pence": a["pence"], "avg": a_avg},
            "last_week": {"turns": b_turns, "pence": b_pence, "avg": b_avg},
            "rising": rising,
        },
    }


def real_turns_per_step() -> float:
    """Measured from past builds. The quote learns from the last one."""
    rows = [r for r in _read() if r.get("build")]
    by_build: Dict[str, int] = {}
    for r in rows:
        by_build[r["build"]] = by_build.get(r["build"], 0) + 1
    if not by_build:
        return 0.0
    return round(sum(by_build.values()) / len(by_build) / 6, 2)


def quote(steps: List[Dict[str, Any]], turns_per_step: int = 0) -> Dict[str, Any]:
    """Price a build from its steps, before it runs.

    Mechanical steps run on Haiku 5.5 in batch, about a tenth of a penny
    a turn. Decisions run on Sonnet synchronously, about two and a half
    pence a turn. The quote is the sum, and it is the budget the founder
    agrees to.
    """
    from routers.build_loop import _step_model
    mech = [s for s in steps if "sonnet" not in _step_model(s)]
    dec = [s for s in steps if "sonnet" in _step_model(s)]
    measured = real_turns_per_step()
    if measured:
        turns_per_step = max(1, round(measured))
    turns_per_step = turns_per_step or 5
    mech_turns = len(mech) * turns_per_step
    dec_turns = len(dec) * turns_per_step
    mech_p = cost_pence("claude-haiku-5-5",
                        {"input_tokens": 10_000, "output_tokens": 400}, batch=True)
    dec_p = cost_pence("claude-sonnet-5",
                       {"input_tokens": 10_000, "output_tokens": 400}, batch=False)
    pence = round(mech_turns * mech_p + dec_turns * dec_p, 2)
    return {
        "ok": True,
        "result": {
            "steps": len(steps),
            "mechanical": len(mech),
            "decisions": len(dec),
            "turns_estimate": mech_turns + dec_turns,
            "pence": pence,
            "gbp": round(pence / 100, 2),
            "note": (
                f"{len(mech)} mechanical steps on Haiku 5.5 batch "
                f"({mech_turns} turns at {mech_p}p), "
                f"{len(dec)} decisions on Sonnet ({dec_turns} turns at {dec_p}p). "
                "Agree the budget, or reduce the decisions before starting."
            ),
        },
    }
