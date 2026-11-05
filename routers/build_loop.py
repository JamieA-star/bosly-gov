"""routers/build_loop.py — run a build to its next ending.

The loop reads the state on disk, takes the current step, and asks
run_with_tools to do that one step with the spec and its check in view.
Then it runs the check. Pass -> tick and continue. Fail -> retry once.
Fail twice -> stuck. The model says NEEDS_FOUNDER: and the build parks
with the question, waiting.

Three rules and they matter:
  - one step per turn: the model is told to do this step and stop, not
    to plan the whole build;
  - the check is the manifest's, never the model's claim;
  - the budget stops it. A build that costs more than the budget without
    finishing is a build to look at, not to let run.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from routers import build
from routers.tool_loop import run_with_tools

_STEP_PROMPT = """You are building a product change for the founder. This is
step {n} of {total}.

THE SPEC (read it; it is the whole brief):
{spec}

THIS STEP: {title}
ITS CHECK: {check}

THE FOUNDER'S ANSWERS (decisions already made; follow them):
{answers}

Do this one step with the tools. When the step is done, stop — do not
start the next step, do not plan the rest of the build. If you need a
decision the spec does not answer, reply with exactly:

NEEDS_FOUNDER: <the question>
OPTIONS: <one> | <two>

and stop. Do not guess a decision.
"""


_DECISION_HINTS = ("decide", "choose", "design", "should", "which",
                   "trade-off", "architect", "restructure", "review")


def _step_model(step: Dict[str, Any]) -> str:
    """Haiku for a mechanical step, Sonnet for a decision.

    In a build, the mechanical steps outnumber the decisions, and every
    tool continuation inherits the step's model — so a Sonnet step
    bills every turn of its history at Sonnet rates. The build runs on
    Haiku by default; a step whose TITLE names a decision goes to
    Sonnet. build_uses_haiku.

    A build runs dozens of steps and most are mechanical — write this
    file, run this check, read this error. Only the steps that DECIDE
    need the strong model. The step's own title and check say which.
    """
    import os
    text = (step.get('title', '') or '').lower()
    if any(h in text for h in _DECISION_HINTS):
        return os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    return os.environ.get("CHEAP_MODEL", "claude-haiku-5-5")


def _ask_model(step_prompt: str, model: str | None = None,
               use_batch: bool = False, build: str = "") -> Dict[str, Any]:
    """One step through the butler's own loop. Returns text and tool calls."""
    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    for ev in run_with_tools(step_prompt, model=model, use_batch=use_batch, build=build):
        et = ev.get("type")
        if et == "token":
            text_parts.append(str(ev.get("text", "")))
        elif et == "tool_call":
            tool_calls.append(ev)
    return {"text": "".join(text_parts), "tool_calls": tool_calls}


def _parse_question(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r"NEEDS_FOUNDER:\s*(.+)", text or "")
    if not m:
        return None
    question = m.group(1).strip().splitlines()[0]
    opts = re.search(r"OPTIONS:\s*(.+)", text or "")
    options = [o.strip() for o in opts.group(1).split("|")] if opts else []
    return {"question": question, "options": options}


def run_build(name: str, max_attempts: int = 2, max_steps: int = 20, use_batch: bool = False) -> Dict[str, Any]:
    """Run a build until it is done, stuck, or needs the founder.

    Returns the final state. The caller (a tool, or the night job) reads
    the status and the question from it.
    """
    loaded = build.load_build(name)
    if not loaded.get("ok"):
        return loaded
    spec = loaded["result"]["spec"]
    steps = loaded["result"]["steps"]
    state = loaded["result"]["state"]

    if state.get("status") in ("done", "needs_founder", "stuck"):
        return {"ok": True, "result": {"state": state, "stopped": state.get("status")}}

    attempts = 0
    calls = 0
    BUDGET_CALLS = int(state.get("budget_calls") or 12)
    BUDGET_PENCE = float(state.get("budget_pence") or 0)
    spent_pence = 0.0
    while state.get("current", 0) < len(steps) and state.get("current", 0) < max_steps:
        if calls >= BUDGET_CALLS:
            build.park_for_founder(
                name,
                f"the build used its {BUDGET_CALLS} model calls before finishing "
                f"step {state.get('current', 0) + 1}. It stopped rather than "
                "spending more. Say 'continue the build' to give it another budget.",
                ["continue with another budget", "leave it parked"],
            )
            logging.info("build %s: budget spent after %d calls", name, calls)
            break
        i = state["current"]
        step = steps[i]
        answers = state.get("answers") or []
        answer_text = "\n".join(
            f"- {a.get('question')} -> {a.get('answer')}" for a in answers
        ) or "(none yet)"
        prompt = _STEP_PROMPT.format(
            n=i + 1, total=len(steps), spec=spec[:6000],
            title=step.get("title", ""), check=step.get("check", ""),
            answers=answer_text,
        )
        logging.info("build %s: step %d/%d — %s", name, i + 1, len(steps), step.get("title"))

        calls += 1
        answer = _ask_model(prompt, model=_step_model(step), use_batch=use_batch, build=name)
        # The agreed budget is in pence. The cost of the call is on the
        # usage record, priced from the table.
        try:
            from routers import usage as _u
            _recs = _u._read()
            _created = state.get("created", "")
            # Spend since the build was created or reset, not all time.
            spent_since = sum(r.get("pence", 0) for r in _recs
                              if r.get("build") == name
                              and (not _created or r.get("ts", "") >= _created))
            spent_pence = spent_since
        except Exception:
            pass
        if BUDGET_PENCE and spent_pence >= BUDGET_PENCE:
            build.park_for_founder(
                name,
                f"the build has spent its agreed budget of {BUDGET_PENCE:.2f}p "
                f"(spent {spent_pence:.2f}p) at step {state.get('current', 0) + 1}. "
                "It stopped rather than spending more.",
                ["agree a larger budget", "leave it parked"],
            )
            logging.info("build %s: budget %.2fp spent", name, BUDGET_PENCE)
            break
        text = answer["text"]

        q = _parse_question(text)
        if q:
            build.park_for_founder(name, q["question"], q["options"])
            logging.info("build %s: parked for the founder: %s", name, q["question"])
            break

        # The check is the manifest's, not the model's claim.
        check_id = step.get("check_id", "")
        if check_id:
            from routers.tools import run_check
            rc = run_check(check_id)
            if not rc.get("ok") and "unknown check" in str(rc.get("error", "")):
                attempts += 1
                if attempts >= max_attempts:
                    build.park_for_founder(
                        name,
                        f"step {i + 1} ({step.get('title')}) did not create its check {check_id}",
                        ["write the check", "skip this step"],
                    )
                    break
                continue
            passed = bool(rc.get("ok")) and rc.get("exit_code", 0) == 0
        else:
            # No registered check: trust nothing. A step with no check is
            # not buildable unattended; park it.
            build.park_for_founder(
                name,
                f"step {i + 1} ({step.get('title')}) has no registered check id",
                ["add a check id", "skip this step"],
            )
            break

        if passed:
            ev = (str(rc.get("stdout", "")) + str(rc.get("stderr", ""))).strip()
            ticked = build.tick_step(name, i, evidence=ev)
            if not ticked.get("ok"):
                # A pass with no evidence is not a proof. Park it.
                build.park_for_founder(
                    name,
                    f"step {i + 1} passed its check but produced no evidence: {ticked.get('error')}",
                    ["tighten the check so it prints a proof", "skip this step"],
                )
                break
            attempts = 0
            # reload after the tick — the next loop must see the new current
            state = build.load_build(name)["result"]["state"]
            continue

        attempts += 1
        if attempts >= max_attempts:
            ev = (str(rc.get("stdout", "")) + "\n" + str(rc.get("stderr", ""))).strip()
            if not ev:
                ev = ("the check ran and failed with no output. The model said: "
                      + (text or "(nothing)")[:400])
            build.mark_stuck(
                name,
                f"step {i + 1} failed its check {attempts} times: {ev[:600]}",
            )
            logging.info("build %s: stuck on step %d", name, i + 1)
            break

    final = build.load_build(name).get("result", {}).get("state", state)
    return {"ok": True, "result": {"state": final, "stopped": final.get("status")}}
