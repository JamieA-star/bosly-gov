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

Do this one step with the tools. When the step is done, stop — do not
start the next step, do not plan the rest of the build. If you need a
decision the spec does not answer, reply with exactly:

NEEDS_FOUNDER: <the question>
OPTIONS: <one> | <two>

and stop. Do not guess a decision.
"""


def _ask_model(step_prompt: str) -> Dict[str, Any]:
    """One step through the butler's own loop. Returns text and tool calls."""
    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    for ev in run_with_tools(step_prompt):
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


def run_build(name: str, max_attempts: int = 2, max_steps: int = 20) -> Dict[str, Any]:
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
    while state.get("current", 0) < len(steps) and state.get("current", 0) < max_steps:
        i = state["current"]
        step = steps[i]
        prompt = _STEP_PROMPT.format(
            n=i + 1, total=len(steps), spec=spec[:6000],
            title=step.get("title", ""), check=step.get("check", ""),
        )
        logging.info("build %s: step %d/%d — %s", name, i + 1, len(steps), step.get("title"))

        answer = _ask_model(prompt)
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
            build.tick_step(name, i, evidence=str(rc.get("stdout", ""))[:800])
            attempts = 0
            state = build.load_build(name)["result"]["state"]
            continue

        attempts += 1
        if attempts >= max_attempts:
            build.mark_stuck(
                name,
                f"step {i + 1} failed its check {attempts} times: "
                + str(rc.get("stdout", ""))[:300],
            )
            logging.info("build %s: stuck on step %d", name, i + 1)
            break

    final = build.load_build(name).get("result", {}).get("state", state)
    return {"ok": True, "result": {"state": final, "stopped": final.get("status")}}
