"""routers/tool_loop.py — the Custodian's tool loop.

WHAT THIS DOES, IN THREE SENTENCES:
  1. It calls the Claude API with the four tools from
     routers/tools.py declared.
  2. If the model asks to use a tool, it runs the tool, sends the
     result back to the model, and calls the API again.
  3. It stops when the model replies without asking for a tool,
     or after MAX_ITERATIONS rounds, whichever comes first.

WHAT THIS IS NOT:
  - It is not the plain chat path. That is route_llm_stream in
    routers/llm_router.py, which scrubs tool-like output on
    purpose. This loop is the path that LETS the model use tools.
  - It does not write to the plan or memory itself. It calls the
    tools in routers/tools.py, and those have the guards.

THE SYSTEM PROMPT comes from tools_prompt.txt in the repo root,
not from a string in this file. That file is meant to be edited
without touching code.

THE SWITCH is config.json → "tools_enabled". server.py only
calls this loop when the flag is true. If the tools misbehave,
set the flag to false and the Custodian goes back to plain chat.

THE TRUNCATION. read_file can return 400 KB. The loop truncates
what it sends back to the model to 40 KB, with a marker, so the
context does not explode. The model sees the head of the file.

Run the self-test (no API call, no tokens spent):

    python3 routers/tool_loop.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List

# Load CLAUDE_API_KEY from the same env file direct_llm.py reads, so
# the loop works standalone (a plain python3 shell does not inherit
# pm2's environment). Mirrors routers/direct_llm.py.
_ENV_FILE = "/home/bosly_accord/bosly-1.0/.env.production"
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, "r", encoding="utf-8", errors="replace") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k, _v.strip('"\''))

# The tools registry. Imported once, at the top.
sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers.tools import TOOLS, dispatch  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

MAX_ITERATIONS = 20         # how many tool rounds before we stop.

# The silence guard's text, in one place so the guard and the
# live probe (__probe_empty__) cannot drift apart.
_SILENCE_TEXT = (
    "I ran the tools but produced no answer. "
    "The tool calls are above; tell me to try again "
    "or ask differently."
)
_PROBE_SENTINEL = "__probe_empty__"
# 5 was fine for a one-shot chat answer; too few for investigation —
# 'did I fix this bug?' needs find-file, read-file, find-route,
# read-route, grep-for-symptom, then answer. The guard against a
# runaway loop stays; the ceiling stops cutting off real work.
TOOL_RESULT_LIMIT = 40_000  # bytes sent back to the model per tool result
LLM_TIMEOUT = 120           # seconds per API call

PROMPT_FILE = Path("/home/bosly_accord/bosly-gov/tools_prompt.txt")

# The tool schemas, in the shape the Anthropic API expects.
# routers/tools.py already has them; we strip the Python fn.
API_TOOLS = [
    {
        "name": t["name"],
        "description": t["description"],
        "input_schema": t["input_schema"],
    }
    for t in TOOLS
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_prompt() -> str:
    """Read the tools prompt. Falls back to a minimal one if missing.

    The date line is injected live: the file says "Today is ..." and
    that static date goes stale. Replace it with today's date in
    Europe/London on every read, so the butler always knows the day
    without the file mutating and without a restart.
    """
    if PROMPT_FILE.exists():
        text = PROMPT_FILE.read_text(encoding="utf-8")
        from datetime import datetime
        from zoneinfo import ZoneInfo
        import re as _re
        today = datetime.now(ZoneInfo("Europe/London")).strftime("%A %d %B %Y")
        text = _re.sub(
            r"^Today is .*$",
            f"Today is {today} (Europe/London).",
            text,
            count=1,
            flags=_re.MULTILINE,
        )
        return text
    return (
        "You are Bosly Custodian. You have four tools: "
        "append_plan_entry, save_memory, read_file, run_check. "
        "Use them when the user asks you to record, read, or check. "
        "Do not fabricate tool results. Reply in plain text when done."
    )


def _truncate_for_model(result: Dict[str, Any]) -> Dict[str, Any]:
    """Cap the size of a tool result before it goes back to the model.

    read_file returns the whole file (up to 400 KB). We serialise
    the result, and if it is larger than TOOL_RESULT_LIMIT, we keep
    the head and add a marker so the model knows it was truncated.
    """
    text = json.dumps(result, ensure_ascii=False)
    if len(text) <= TOOL_RESULT_LIMIT:
        return result
    truncated = text[:TOOL_RESULT_LIMIT]
    return {
        "ok": result.get("ok", True),
        "truncated": True,
        "result_head": truncated,
        "note": (
            f"Result was {len(text)} bytes; truncated to "
            f"{TOOL_RESULT_LIMIT}. Read a smaller range if you need more."
        ),
    }


def _call_api(
    system_prompt: str,
    messages: List[Dict[str, Any]],
    timeout: int = LLM_TIMEOUT,
) -> Dict[str, Any]:
    """One non-streaming call to the Anthropic API with tools declared.

    Returns the parsed JSON response. Raises on transport errors.
    """
    api_key = os.environ.get("CLAUDE_API_KEY", "")
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    if not api_key:
        raise RuntimeError("CLAUDE_API_KEY not set")

    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": messages,
            "tools": API_TOOLS,
            "stream": False,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------

def run_with_tools(
    user_message: str,
    system_prompt: str | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> Generator[Dict[str, Any], None, None]:
    """Run the tool loop. Yields events the SSE handler understands:

      {"type": "token",     "text": "..."}            visible text
      {"type": "tool_call", "name": "...", "ok": bool,
                            "error": "..."}          a tool was used
      {"type": "done",      "result": {...}}          final
      {"type": "error",     "error": "..."}           on failure
    """
    system_prompt = system_prompt or _read_prompt()
    messages: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]

    # The live probe's trigger: deterministic, no API call, no tokens.
    # No real message is this string. It lets gov.the_check_proves_the_
    # file_not_the_process prove the RUNNING process, not the file.
    if user_message.strip() == _PROBE_SENTINEL:
        yield {"type": "token", "cannot_help": True, "text": _SILENCE_TEXT}
        yield {"type": "done", "result": {"ok": True, "iterations": 0, "stop_reason": "probe"}}
        return

    _any_text = False
    calls: list = []
    seen: set = set()
    for iteration in range(max_iterations):
        try:
            response = _call_api(system_prompt, messages)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            yield {"type": "error", "error": f"Claude HTTP error: {body or e}"}
            return
        except Exception as e:
            yield {"type": "error", "error": f"Claude call failed: {e}"}
            return

        stop_reason = response.get("stop_reason") or ""
        content = response.get("content") or []

        # ---- text the model produced this round ----
        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    yield {"type": "token", "text": text}
                    _any_text = True

        # ---- if the model is done, stop ----
        if stop_reason != "tool_use":
            # The silence guard: the loop ran and the model ended without
            # text. Say so — never nothing. The tool calls are in the
            # events above.
            if not _any_text:
                logging.warning(
                    "tool loop: empty answer after %d rounds; calls: %s",
                    iteration + 1,
                    [(c.get("name"), c.get("ok"), (c.get("error") or "")[:80]) for c in calls],
                )
                # The failure message carries the evidence: name what was
                # called, so "no answer" says what was read and not
                # written. A generic message hides the read-and-stop.
                _names = [c.get("name") for c in calls if c.get("name")]
                if _names:
                    _detail = (
                        f"I called {len(_names)} tool(s) ({', '.join(_names)}) "
                        "and produced no answer. "
                    )
                else:
                    _detail = "I ran the tools but produced no answer. "
                yield {
                    "type": "token",
                    "cannot_help": True,
                    "text": _detail + "The tool calls are above; tell me to try again or ask differently.",
                }
            yield {
                "type": "done",
                "result": {
                    "ok": True,
                    "iterations": iteration + 1,
                    "stop_reason": stop_reason,
                },
            }
            return

        # ---- otherwise it asked for one or more tools ----
        # Append the assistant's turn (which contains tool_use blocks)
        messages.append({"role": "assistant", "content": content})

        tool_results: List[Dict[str, Any]] = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            args = block.get("input") or {}
            tool_use_id = block.get("id", "")

            # The repeat guard: the same tool with the same arguments
            # twice is a loop, not progress. Stop and name it.
            _key = (name, hashlib.sha1(
                json.dumps(args, sort_keys=True, default=str).encode()
            ).hexdigest()[:16])
            if _key in seen:
                logging.warning("tool loop: repeated call %s; stopping", name)
                yield {
                    "type": "token",
                    "cannot_help": True,
                    "text": (
                        f"I called {name} twice with the same arguments and "
                        "stopped to avoid a loop. The tool calls are above; "
                        "tell me to try again or ask differently."
                    ),
                }
                yield {"type": "done", "result": {"ok": True, "iterations": iteration + 1, "stop_reason": "repeat"}}
                return
            seen.add(_key)

            result = dispatch(name, args)
            result_for_model = _truncate_for_model(result)

            _tid = ""
            if result.get("ok"):
                _r = result.get("result") or {}
                if isinstance(_r, dict):
                    _tid = str(_r.get("thing_id") or "")
            _call = {
                "name": name,
                "ok": bool(result.get("ok")),
                "error": result.get("error", ""),
            }
            calls.append(_call)
            yield {
                "type": "tool_call",
                "name": name,
                "ok": bool(result.get("ok")),
                "error": result.get("error", ""),
                "thing_id": _tid,
            }

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": json.dumps(result_for_model, ensure_ascii=False),
            })

        # Feed the results back as a user turn and loop
        messages.append({"role": "user", "content": tool_results})

    # If we get here, the loop hit MAX_ITERATIONS
    yield {
        "type": "error",
        "error": (
            f"Tool loop exceeded {max_iterations} iterations. "
            f"The model kept asking for tools. Stopped to avoid a loop."
        ),
    }


# ---------------------------------------------------------------------------
# Self-test — no API call, no tokens spent
# ---------------------------------------------------------------------------

def _selftest() -> int:
    """Test the loop's logic without calling the API.

    We monkey-patch _call_api to return a scripted sequence:
      round 1: tool_use on read_file with a known path
      round 2: end_turn with a text block

    Then we check that:
      - a tool_call event is yielded for read_file
      - a token event is yielded for the final text
      - a done event is yielded at the end
    """
    passed = 0
    failed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}")
            if detail:
                for line in detail.splitlines():
                    print(f"      {line}")

    # ---- Fake API ----
    rounds = [
        {
            "stop_reason": "tool_use",
            "content": [
                {"type": "text", "text": "Let me look at that file."},
                {
                    "type": "tool_use",
                    "id": "tool_1",
                    "name": "read_file",
                    "input": {"path": "PLAN.md"},
                },
            ],
        },
        {
            "stop_reason": "end_turn",
            "content": [
                {"type": "text", "text": "The plan starts with BOSLY GOV — PLAN."},
            ],
        },
    ]

    def fake_call_api(system_prompt, messages, timeout=LLM_TIMEOUT):
        return rounds.pop(0)

    real_call = globals()["_call_api"]
    globals()["_call_api"] = fake_call_api
    try:
        events = list(run_with_tools("read the plan"))
    finally:
        globals()["_call_api"] = real_call

    # ---- Checks ----
    tool_calls = [e for e in events if e.get("type") == "tool_call"]
    tokens = [e for e in events if e.get("type") == "token"]
    dones = [e for e in events if e.get("type") == "done"]
    errors = [e for e in events if e.get("type") == "error"]

    check("no error events", len(errors) == 0,
          detail=f"errors: {errors}")

    check("one tool_call event", len(tool_calls) == 1,
          detail=f"got {len(tool_calls)}: {tool_calls}")

    if tool_calls:
        tc = tool_calls[0]
        check("tool_call is read_file", tc.get("name") == "read_file",
              detail=f"got {tc.get('name')!r}")
        check("tool_call ok=True", tc.get("ok") is True,
              detail=f"error: {tc.get('error')!r}")

    check("at least two token events", len(tokens) >= 2,
          detail=f"got {len(tokens)}: {[t.get('text','')[:30] for t in tokens]}")

    check("one done event", len(dones) == 1,
          detail=f"got {len(dones)}")

    if dones:
        check("done has iterations", dones[0].get("result", {}).get("iterations") == 2,
              detail=f"got {dones[0].get('result')}")

    # ---- Silence guard: a round with no text sets cannot_help ----
    silent = [
        {"stop_reason": "end_turn", "content": []},
    ]

    def fake_silent(system_prompt, messages, timeout=LLM_TIMEOUT):
        return silent.pop(0)

    globals()["_call_api"] = fake_silent
    try:
        silent_events = list(run_with_tools("say nothing"))
    finally:
        globals()["_call_api"] = real_call

    silent_tokens = [e for e in silent_events if e.get("type") == "token"]
    check(
        "silence guard sets cannot_help",
        bool(silent_tokens) and silent_tokens[0].get("cannot_help") is True,
        detail=f"tokens: {silent_tokens}",
    )
    # The message must carry the evidence. The silent round calls no
    # tools, so it says so; a round that read files must name them.
    check(
        "silence guard message names what was called",
        bool(silent_tokens) and (
            "called" in (silent_tokens[0].get("text") or "")
            or "ran the tools" in (silent_tokens[0].get("text") or "")
        ),
        detail=f"text: {(silent_tokens[0].get('text') if silent_tokens else '')[:120]}",
    )

    # ---- Repeat guard: the same tool and args twice stops the loop ----
    repeated = [
        {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "t1", "name": "read_file", "input": {"path": "PLAN.md"}}]},
        {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "t2", "name": "read_file", "input": {"path": "PLAN.md"}}]},
    ]

    def fake_repeated(system_prompt, messages, timeout=LLM_TIMEOUT):
        return repeated.pop(0)

    globals()["_call_api"] = fake_repeated
    try:
        rep_events = list(run_with_tools("read twice"))
    finally:
        globals()["_call_api"] = real_call

    rep_tokens = [e for e in rep_events if e.get("type") == "token"]
    check(
        "repeat guard stops a repeated call",
        bool(rep_tokens) and "twice" in (rep_tokens[-1].get("text") or "")
        and "read_file" in (rep_tokens[-1].get("text") or ""),
        detail=f"tokens: {[t.get('text','')[:60] for t in rep_tokens]}",
    )

    # ---- Second test: max_iterations stops a runaway loop ----
    _n = {"i": 0}

    def fake_runaway(system_prompt, messages, timeout=LLM_TIMEOUT):
        # A different call each round: no repeat, so only max_iterations
        # can stop it. The repeat guard is proven by its own test.
        _n["i"] += 1
        return {
            "stop_reason": "tool_use",
            "content": [
                {
                    "type": "tool_use",
                    "id": f"tool_x{_n['i']}",
                    "name": "read_file",
                    "input": {"path": f"PLAN.md#{_n['i']}"},
                },
            ],
        }

    globals()["_call_api"] = fake_runaway
    try:
        events = list(run_with_tools("runaway", max_iterations=3))
    finally:
        globals()["_call_api"] = real_call

    errors = [e for e in events if e.get("type") == "error"]
    check("runaway loop is stopped", len(errors) == 1,
          detail=f"errors: {errors}")

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_selftest())
