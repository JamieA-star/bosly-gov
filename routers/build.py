"""routers/build.py — a build's state, on disk, so a night survives.

The model cannot carry state between two calls. A build that runs for
hours cannot live in the model's head: it lives in a directory, with a
spec, a list of steps, and a state file that says where it got to and
what it needs. Every step is ticked with its evidence; a step that
fails twice stops the build and parks it with a question for the
founder.

Three endings, and they are different: done, stuck, and needs-the-founder.
The third is the one that makes unattended work safe.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BUILDS = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dir(name: str) -> Path:
    """A build directory. The name is a bare stem; no traversal."""
    stem = (name or "").strip()
    if not stem or "/" in stem or ".." in stem or not stem.replace("-", "").replace("_", "").isalnum():
        raise ValueError("build name must be a bare alnum stem with - or _")
    return BUILDS / stem


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def new_build(name: str, spec: str, steps: List[Dict[str, str]]) -> Dict[str, Any]:
    """Create a build. steps: [{title, check}] — each step has its own check.

    Refuses if the build exists: a build is created once and resumed,
    never silently restarted.
    """
    d = _dir(name)
    if d.exists() and (d / "state.json").exists():
        return {"ok": False, "error": f"build {name!r} already exists"}
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.md").write_text(spec.strip() + "\n", encoding="utf-8")
    _write(d / "steps.json", {"steps": steps})
    _write(d / "state.json", {
        "name": name,
        "created": _now(),
        "status": "new",            # new | running | done | stuck | needs_founder
        "current": 0,
        "done": [],                 # [{index, title, evidence, at}]
        "question": None,
        "options": [],
        "report": None,
    })
    return {"ok": True, "result": {"name": name, "steps": len(steps)}}


def load_build(name: str) -> Dict[str, Any]:
    """The spec, the steps and the state, in one read."""
    d = _dir(name)
    if not (d / "state.json").exists():
        return {"ok": False, "error": f"no build {name!r}"}
    return {
        "ok": True,
        "result": {
            "name": name,
            "spec": (d / "spec.md").read_text(encoding="utf-8"),
            "steps": _read(d / "steps.json", {"steps": []}).get("steps", []),
            "state": _read(d / "state.json", {}),
        },
    }


def _set_state(name: str, **patch) -> Dict[str, Any]:
    d = _dir(name)
    state = _read(d / "state.json", None)
    if state is None:
        return {"ok": False, "error": f"no build {name!r}"}
    state.update(patch)
    _write(d / "state.json", state)
    return {"ok": True, "result": state}


def tick_step(name: str, index: int, evidence: str = "") -> Dict[str, Any]:
    """Mark a step done, with the evidence that proves it.

    The evidence is the check's own output, not the model's claim. A
    step without evidence is a claim, and claims are what the Custodian
    exists to doubt.
    """
    d = _dir(name)
    state = _read(d / "state.json", None)
    if state is None:
        return {"ok": False, "error": f"no build {name!r}"}
    steps = _read(d / "steps.json", {"steps": []}).get("steps", [])
    if index < 0 or index >= len(steps):
        return {"ok": False, "error": f"step {index} out of range"}
    entry = {"index": index, "title": steps[index].get("title", ""),
             "evidence": (evidence or "")[:1000], "at": _now()}
    state.setdefault("done", []).append(entry)
    state["current"] = index + 1
    state["status"] = "done" if index + 1 >= len(steps) else "running"
    _write(d / "state.json", state)
    return {"ok": True, "result": {"current": state["current"], "status": state["status"]}}


def park_for_founder(name: str, question: str, options: List[str]) -> Dict[str, Any]:
    """The third ending: a decision the spec does not answer.

    The build stops and waits. It does not guess. A night that ends with
    a good question is a good night.
    """
    if not (question or "").strip():
        return {"ok": False, "error": "question required"}
    return _set_state(
        name,
        status="needs_founder",
        question=question.strip(),
        options=[o.strip() for o in (options or []) if o.strip()],
    )


def mark_stuck(name: str, reason: str) -> Dict[str, Any]:
    """The second ending: a step failed twice. Stop; do not thrash."""
    return _set_state(name, status="stuck", question=(reason or "").strip())


def finish(name: str, report: str) -> Dict[str, Any]:
    """The first ending: every step ticked. Write the report."""
    return _set_state(name, status="done", report=(report or "").strip())


def list_builds() -> Dict[str, Any]:
    """Every build and where it stands. The front door for the founder."""
    out = []
    if BUILDS.exists():
        for d in sorted(BUILDS.iterdir()):
            if not d.is_dir():
                continue
            st = _read(d / "state.json", {})
            if st:
                out.append({
                    "name": st.get("name", d.name),
                    "status": st.get("status"),
                    "current": st.get("current"),
                    "question": st.get("question"),
                })
    return {"ok": True, "result": {"builds": out}}
