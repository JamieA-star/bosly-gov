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


def _load_base_spec() -> List[str]:
    """The standing decisions every build inherits, one per line.

    Read once per call. A missing base is an error the caller handles;
    an empty list here would silently un-gate every build."""
    p = Path(__file__).resolve().parent.parent / "specs" / "base.md"
    if not p.exists():
        raise FileNotFoundError(f"base spec missing: {p}")
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("- "):
            out.append(s[2:].strip())
    return out

MEMORY = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json")

UNIVERSAL_CAP = 12


def _load_universal_decisions() -> List[str]:
    """The decisions marked true of every build, newest first, capped.

    A decision is universal when the founder sets metadata_json.universal
    on it. A build writes its lesson; the founder decides whether it is
    true beyond that build. The cap keeps the spec from becoming a corpus
    dump: past UNIVERSAL_CAP, a decision must be promoted to the base or
    retired."""
    if not MEMORY.exists():
        return []
    try:
        data = json.loads(MEMORY.read_text(encoding="utf-8"))
    except Exception:
        return []
    marked = [e for e in data
              if e.get("item_type") == "decision"
              and (e.get("metadata_json") or {}).get("universal") is True
              and (e.get("content") or "").strip()]
    marked.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    return [e["content"].strip() for e in marked[:UNIVERSAL_CAP]]


LESSON_STEP = {
    "title": "Write the lesson",
    "check": "the corpus has a build entry for this build",
    "check_id": "gov.a_build_writes_its_lesson",
}


def record_lesson(name: str, content: str, item_type: str = "build") -> Dict[str, Any]:
    """A build's lesson, written to the corpus in the same shape the founder keeps.

    The id is dated and names the build, so the entry is citeable from the
    build's spec, a commit, or the next session's handover. The content is
    the generalisation, not the story — a lesson true beyond this build.
    """
    if not (content or "").strip():
        return {"ok": False, "error": "content required: a lesson is a generalisation, not silence"}
    if item_type not in ("build", "pattern", "decision", "fact", "incident"):
        return {"ok": False, "error": f"unknown item_type {item_type!r}"}
    stem = (name or "").strip().strip("-_").replace("_", "-").lower()
    if not stem or not stem.replace("-", "").isalnum():
        return {"ok": False, "error": "build name must be a bare alnum stem with - or _"}
    now = _now()
    day = now[:10].replace("-", "")
    entry_id = f"{item_type}-{day}-{stem}"
    try:
        data = json.loads(MEMORY.read_text(encoding="utf-8")) if MEMORY.exists() else []
    except Exception as e:
        return {"ok": False, "error": f"memory unreadable: {e}"}
    if any(e.get("id") == entry_id for e in data):
        return {"ok": False, "error": f"entry {entry_id!r} already exists"}
    data.append({
        "id": entry_id,
        "project_slug": "bosly-gov",
        "item_type": item_type,
        "content": content.strip(),
        "metadata_json": {"build": name},
        "created_at": now,
        "updated_at": now,
    })
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "result": {"id": entry_id, "total": len(data)}}

def write_spec(name: str, goal: str, decisions: List[str],
               permissions: List[str], escape_hatch: str) -> Dict[str, Any]:
    """Write a build's spec before it starts. An overnight build cannot
    ask a question, so the answers are written down first: the goal, the
    decisions it would otherwise ask about, the permissions it has, and
    the escape hatch when it is truly stuck."""
    if not (goal or "").strip():
        return {"ok": False, "error": "goal required"}
    if not decisions:
        return {"ok": False, "error": "decisions required: what would it ask?"}
    if not permissions:
        return {"ok": False, "error": "permissions required: what may it do alone?"}
    if not (escape_hatch or "").strip():
        return {"ok": False, "error": "escape_hatch required: what to do when stuck"}
    d = _dir(name)
    d.mkdir(parents=True, exist_ok=True)
    _base = _load_base_spec()
    _universal = _load_universal_decisions()
    text = (
        f"# Build spec — {name}\n\n"
        f"## The goal\n{goal.strip()}\n\n"
        "## The standing decisions (inherited from the base)\n"
        + "\n".join(f"- {x}" for x in _base)
        + "\n\n"
        + (
            ("## The decisions that are true of every build\n"
             + "\n".join(f"- {x}" for x in _universal)
             + "\n\n")
            if _universal else ""
        )
        + "## The decisions (the questions the build would ask)\n"
        + "\n".join(f"- {x.strip()}" for x in decisions if str(x).strip())
        + "\n\n## The permissions (what it may do without asking)\n"
        + "\n".join(f"- {x.strip()}" for x in permissions if str(x).strip())
        + f"\n\n## The escape hatch\n{escape_hatch.strip()}\n"
        + "\n## The lesson\n"
        + "After the last step ticks, call record_lesson(name, the generalisation, \"build\").\n"
        + "What is true beyond this build? Not the story. If it taught nothing, say so \u2014\n"
        + "an honest empty lesson is better than a fake one.\n"
    )
    (d / "spec.md").write_text(text, encoding="utf-8")
    return {"ok": True, "result": {"name": name, "bytes": len(text)}}


def has_spec(name: str) -> bool:
    try:
        d = _dir(name)
        p = d / "spec.md"
        return p.exists() and len(p.read_text(encoding="utf-8")) > 80
    except Exception:
        return False


def budget_rule(quote_pence: float) -> float:
    """Twice the quote, rounded up to the next penny.

    The quote is the estimate. A build that spends twice it has lost
    its way, and the loop should park and say so. Not three times —
    that is a third of the budget spent on 'just in case'.
    """
    import math
    return max(1.0, math.ceil(quote_pence * 2 * 100) / 100)


def base_gap(name: str) -> Optional[str]:
    """The one rule for a base-carrying spec. None when the spec for
    `name` exists and carries every standing decision in specs/base.md;
    otherwise the refusal, naming the fix. The door (new_build) calls it;
    the loop's gate reads the same _load_base_spec."""
    try:
        base = _load_base_spec()
    except FileNotFoundError as e:
        return f"base spec missing: {e}"
    sp = _dir(name) / "spec.md"
    spec = sp.read_text(encoding="utf-8") if sp.exists() else ""
    if not spec.strip():
        return "no base spec — call write_spec first"
    missing = [line for line in base if line not in spec]
    if missing:
        return (f"no base spec — call write_spec first "
                f"({len(missing)} of {len(base)} standing decisions missing)")
    return None


def new_build(name: str, spec: str, steps: List[Dict[str, str]],
              budget_pence: float = 0) -> Dict[str, Any]:
    """Create a build. steps: [{title, check}] — each step has its own check.

    Refuses if the build exists: a build is created once and resumed,
    never silently restarted.
    """
    d = _dir(name)
    if d.exists() and (d / "state.json").exists():
        return {"ok": False, "error": f"build {name!r} already exists"}
    # The door: a build is created only on a base-carrying spec that
    # write_spec wrote. new_build no longer writes a spec; the `spec`
    # argument is ignored and kept only for the signature.
    gap = base_gap(name)
    if gap:
        return {"ok": False, "error": gap}
    # The lesson is not a choice: every build ends by writing what it
    # learned to the corpus. If the caller's last step already names the
    # lesson check, keep it; otherwise append it. A caller who passes the
    # lesson check with a different check_id is overridden, not obeyed.
    steps = list(steps or [])
    if not steps or steps[-1].get("check_id") != LESSON_STEP["check_id"]:
        steps = steps + [dict(LESSON_STEP)]
    d.mkdir(parents=True, exist_ok=True)
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
        "budget_pence": float(budget_pence or 0),
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
            "spec": ((d / "spec.md").read_text(encoding="utf-8")
                     if (d / "spec.md").exists() else ""),
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
    # refuse a tick with no evidence: a tick is a proof, not a claim.
    # And refuse a tick on a step already done: a step ticks once.
    if not (evidence or "").strip():
        return {"ok": False, "error": "evidence is required: a tick is a proof, not a claim"}
    if any(d.get("index") == index for d in state.get("done", [])):
        return {"ok": False, "error": f"step {index} is already ticked"}
    entry = {"index": index, "title": steps[index].get("title", ""),
             "evidence": (evidence or "")[:1000], "at": _now()}
    state.setdefault("done", []).append(entry)
    state["current"] = index + 1
    # A step that ticks has nothing left to ask; a stale question is
    # worse than none.
    state["question"] = None
    state["options"] = []
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
    d = _dir(name)
    state = _read(d / "state.json", {})
    return _set_state(
        name,
        status="needs_founder",
        question=question.strip(),
        options=[o.strip() for o in (options or []) if o.strip()],
        step_at_park=state.get("current", 0),
    )


def set_steps(name: str, steps: List[Dict[str, str]]) -> Dict[str, Any]:
    """Replace a build's steps, before it has ticked any.

    A build that has done nothing can be re-scoped: the first step was
    too big, or the spec was read wrong. Once a step is ticked, the
    steps are frozen — re-scoping a running build loses its evidence.
    """
    d = _dir(name)
    state = _read(d / "state.json", None)
    if state is None:
        return {"ok": False, "error": f"no build {name!r}"}
    if state.get("done"):
        return {"ok": False, "error": "steps are frozen once a step is ticked"}
    _write(d / "steps.json", {"steps": steps})
    state["status"] = "running"
    state["question"] = None
    state["options"] = []
    state["current"] = 0
    _write(d / "state.json", state)
    return {"ok": True, "result": {"name": name, "steps": len(steps)}}


def build_answer(name: str, answer: str) -> Dict[str, Any]:
    """Apply the founder's answer to a parked build and resume it.

    The answer is kept as the founder's own words: the next step's
    prompt includes it, so the model reads the decision rather than
    parsing it. No clever matching — the founder answered, and the
    build continues from where it stopped.
    """
    if not (answer or "").strip():
        return {"ok": False, "error": "answer required"}
    d = _dir(name)
    state = _read(d / "state.json", None)
    if state is None:
        return {"ok": False, "error": f"no build {name!r}"}
    if state.get("status") != "needs_founder":
        return {"ok": False, "error": f"build {name!r} is not parked (status {state.get('status')})"}
    answers = state.setdefault("answers", [])
    answers.append({"question": state.get("question"), "answer": answer.strip(), "at": _now()})
    state["question"] = None
    state["options"] = []
    state["status"] = "running"
    _write(d / "state.json", state)
    return {"ok": True, "result": {"name": name, "status": "running", "answers": len(answers)}}


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
