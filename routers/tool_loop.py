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
TOOLS_NOTES_FILE = Path("/home/bosly_accord/bosly-gov/tools_prompt.tools.md")

# ecosystem_state reads a 383KB plan and the pile; the tool list is a list
# comprehension. Cache only what is expensive, keyed on the mtimes of the
# files that change it. The tool list regenerates every read so it cannot
# drift as Bosly grows — that drift is the bug this fixes ("EIGHT TOOLS",
# 13 listed, 23 in TOOLS).
_ECO_CACHE = {"key": None, "text": ""}
_REPO_PATHS = {
    "Accord": "/home/bosly_accord/bosly-1.0",
    "Keep":   "/home/bosly_accord/bosly-keep",
    "Gov":    "/home/bosly_accord/bosly-gov",
}


def _mtimes_key():
    key = []
    for f in ("PLAN.md", "things.db"):
        pth = Path("/home/bosly_accord/bosly-gov") / f
        try:
            key.append((f, pth.stat().st_mtime_ns))
        except OSError:
            key.append((f, 0))
    return tuple(key)


def _ecosystem_section() -> str:
    key = _mtimes_key()
    if _ECO_CACHE["key"] == key and _ECO_CACHE["text"]:
        return _ECO_CACHE["text"]
    try:
        from routers.tools import ecosystem_state as _eco
        r = _eco(section="all")
        res = r.get("result", {}) if r.get("ok") else {}
        plan = res.get("plan", {}) or {}
        things = res.get("things", {}) or {}
        # One source: plan_query. The ecosystem's own count disagreed
        # with the tool — 14 vs 29 active — so the context block and the
        # tool told the founder two numbers. The tool is the truth now;
        # the summary quotes it.
        from routers.tools import plan_query as _pq
        active = _pq(status="active", brief=True).get("result", {}) or {}
        parked = _pq(status="parked", brief=True).get("result", {}) or {}
        a_rows = active.get("rows") or []
        lines = ["=== THE ECOSYSTEM (current) ==="]
        lines.append(
            f"Plan: {active.get('count', 0)} active, "
            f"{parked.get('count', 0)} parked. "
            "Active is the to-do list; parked is LIVE or GATED."
        )
        for row in a_rows[:8]:
            lines.append(f"  [ ] {row.get('id')} — {row.get('first', '')}")
        ip = plan.get("in_progress") or []
        if ip:
            lines.append(f"  In progress ({len(ip)}): " + ", ".join(
                (item.get("title") or item.get("id") or "?") for item in ip[:8]))
        if isinstance(things, dict):
            bits = ", ".join(f"{k} {v}" if not isinstance(v, dict) else k for k, v in things.items())
            if bits:
                lines.append(f"Things: {bits}.")
        text = "\n".join(lines)
    except Exception as e:
        text = f"=== THE ECOSYSTEM ===\n(unavailable: {e})"
    _ECO_CACHE["key"], _ECO_CACHE["text"] = key, text
    return text


def _repos_section() -> str:
    import subprocess
    lines = ["=== THE REPOS ==="]
    for name, path in _REPO_PATHS.items():
        head = ""
        try:
            head = subprocess.run(
                ["git", "-C", path, "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=2,
            ).stdout.strip()
        except Exception:
            head = ""
        lines.append(f"  {name}: {path}" + (f" at {head}" if head else ""))
    return "\n".join(lines)


def _tools_section() -> str:
    try:
        from routers.tools import TOOLS
    except Exception as e:
        return f"=== THE TOOLS ===\n(unavailable: {e})"
    notes = ""
    try:
        notes = TOOLS_NOTES_FILE.read_text(encoding="utf-8")
    except OSError:
        notes = ""
    # Split the .md into {tool_name: body}, keyed on "## name".
    import re as _re
    blocks = _re.split(r"^## ", notes, flags=_re.MULTILINE)
    by_tool = {}
    for b in blocks[1:]:
        name, _, body = b.partition("\n")
        by_tool[name.strip()] = body.strip()
    out = [f"=== THE TOOLS ({len(TOOLS)}) ==="]
    for t in TOOLS:
        name = t["name"]
        desc = (t.get("description") or "").strip().replace("\n", " ")
        out.append(f"\n{name} — {desc}")
        extra = by_tool.get(name)
        if extra:
            out.append(extra)
    return "\n".join(out)

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
    # The system prompt is the STATIC PREFIX — the standing rules and the
    # tool list, and nothing that changes. A prompt cache is a prefix
    # match: the date, the ecosystem and the repos used to live here, and
    # each changed on a schedule (daily, per plan write, per commit), so
    # every call re-billed the whole 15KB. They now go in the first user
    # message (see run_with_tools), where the variable part belongs. The
    # static_prefix is what gets cached; everything after it is small.
    if PROMPT_FILE.exists():
        text = PROMPT_FILE.read_text(encoding="utf-8")
        # Drop the date line from the file if present; it is no longer
        # substituted here. The date comes from the user message now.
        import re as _re
        text = _re.sub(r"^Today is .*$\n?", "", text, count=1, flags=_re.MULTILINE)
        static_prefix = (
            text.rstrip()
            + "\n\n"
            + _tools_section()
            + "\n"
        )
        return static_prefix
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


# The model is chosen at the door, not mid-session. Switching models
# destroys the cache: each has its own, and a switch re-processes the
# conversation at full price. Classify once, on the founder's words,
# and stay on that model for the whole loop.
#
# Conservative: anything that looks like a decision, a build, or a
# correction goes to the strong model. The cheap model handles shaped
# questions — read a tool, format the answer — where the cost is the
# round-trip, not the judgement.
_STRONG_HINTS = (
    "build", "design", "decide", "plan the", "architect", "refactor",
    "fix", "correct", "should we", "what do you think", "trade-off",
    "restructure", "migrate", "replace", "the best way", "review",
)
_CHEAP_MODEL = os.environ.get("CHEAP_MODEL", "claude-haiku-5-5")
_STRONG_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")


def classify_task(user_message: str) -> str:
    """The model for this turn. Chosen once, at the door."""
    low = (user_message or "").lower()
    if any(h in low for h in _STRONG_HINTS):
        return _STRONG_MODEL
    return _CHEAP_MODEL


BATCH_URL = "https://api.anthropic.com/v1/messages/batches"


def _call_api_batch(
    system_prompt: str,
    messages: List[Dict[str, Any]],
    model: str | None = None,
    max_wait: int = 3600,
) -> Dict[str, Any]:
    """One call through the batch API: half the rate, for work that waits.

    The night build has nothing waiting on a turn, so each turn is a
    batch of one. Submit, poll, read. On any failure, fall back to the
    synchronous call — a batch failure must not stop a build.
    """
    import time
    import uuid
    api_key = os.environ.get("CLAUDE_API_KEY", "")
    model = model or os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    if not api_key:
        raise RuntimeError("CLAUDE_API_KEY not set")

    custom_id = "turn-" + uuid.uuid4().hex[:8]
    req = {
        "custom_id": custom_id,
        "params": {
            "model": model,
            "max_tokens": 4000,
            "system": [{"type": "text", "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}}],
            "messages": messages,
            "tools": API_TOOLS,
        },
    }
    body = json.dumps({"requests": [req]}).encode("utf-8")
    r = urllib.request.Request(
        BATCH_URL, data=body,
        headers={"Content-Type": "application/json", "x-api-key": api_key,
                 "anthropic-version": ANTHROPIC_VERSION},
    )
    with urllib.request.urlopen(r, timeout=60) as resp:
        batch = json.loads(resp.read().decode("utf-8"))
    batch_id = batch.get("id")
    if not batch_id:
        raise RuntimeError("no batch id returned")

    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(10)
        poll = urllib.request.Request(
            f"{BATCH_URL}/{batch_id}",
            headers={"x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION},
        )
        with urllib.request.urlopen(poll, timeout=60) as resp:
            state = json.loads(resp.read().decode("utf-8"))
        if state.get("processing_status") == "ended":
            results_url = f"{BATCH_URL}/{batch_id}/results"
            with urllib.request.urlopen(
                urllib.request.Request(results_url, headers={
                    "x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION}),
                timeout=60,
            ) as resp:
                line = resp.read().decode("utf-8").strip().splitlines()[0]
            out = json.loads(line)
            data = (out.get("result") or {}).get("message") or {}
            data["_usage"] = data.get("usage") or {}
            data["_model"] = model
            data["_batch"] = True
            try:
                from routers import usage as _usage
                _usage.record(model, data["_usage"], batch=True, label="batch turn")
            except Exception:
                pass
            return data
    raise TimeoutError("batch did not finish within the wait")


def _call_api(
    system_prompt: str,
    messages: List[Dict[str, Any]],
    timeout: int = LLM_TIMEOUT,
    model: str | None = None,
) -> Dict[str, Any]:
    """One non-streaming call to the Anthropic API with tools declared.

    model is chosen at the door and never changed mid-loop: switching
    models destroys the prompt cache. The response's usage is attached
    to the parsed JSON under "_usage" so the loop can log the cost.
    """
    api_key = os.environ.get("CLAUDE_API_KEY", "")
    model = model or os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    if not api_key:
        raise RuntimeError("CLAUDE_API_KEY not set")

    # Prompt caching is not automatic: the request must name the
    # breakpoints. The system prompt and the tool list are the stable
    # prefix — they get cache_control, the conversation does not. Cached
    # input is a tenth of the price and the prefix is 12,000 tokens, so
    # this one block is the largest cost saving in the system.
    system_blocks = [{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"},
    }]
    cached_tools = [dict(t) for t in API_TOOLS]
    if cached_tools:
        # The breakpoint goes on the LAST tool, so the whole tool block
        # is the cached prefix.
        cached_tools[-1] = dict(cached_tools[-1])
        cached_tools[-1]["cache_control"] = {"type": "ephemeral"}
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 4000,
            "system": system_blocks,
            "messages": messages,
            "tools": cached_tools,
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
        data = json.loads(resp.read().decode("utf-8"))
    # The cost model: input, output, and the two cache numbers. Kept
    # beside the response, not inside it, so the loop's parsing is
    # unchanged.
    data["_usage"] = data.get("usage") or {}
    data["_model"] = model
    # Every call is costed and written down. A tracking failure is not a
    # dead butler — record() never raises.
    try:
        from routers import usage as _usage
        _usage.record(model, data["_usage"], batch=False,
                      label=(messages[-1].get("content", "")[:60] if messages else ""))
    except Exception:
        pass
    return data


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------

def _context_block() -> str:
    """The current state: date, ecosystem, repos. Goes in the first user
    message, after the static system prompt, so the cache holds.

    This is the variable part of every turn. Small, and bounded by the
    mtime caches inside _ecosystem_section and _repos_section.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Europe/London")).strftime("%A %d %B %Y")
    return (
        f"Today is {today} (Europe/London).\n\n"
        + _ecosystem_section()
        + "\n\n"
        + _repos_section()
    )


# The deterministic floor for tool calls. A read-only tool with the same
# arguments returns its stored result instead of running again: the
# butler does not re-read the same file or re-query the same plan twice
# in a session.
#
# NEVER cache a write. This list is explicit so the next reader can see
# what is excluded and why: every one of these changes the world, and a
# cached write would silently drop the change.
_WRITE_TOOLS = frozenset({
    "append_plan_entry", "save_memory", "save_thing", "link_things",
    "plan_write", "write_file", "patch_file", "draft_email",
    "send_draft_to_me", "send_email", "roll_transcript", "session_summary",
})
_TOOL_CACHE: Dict[tuple, Dict[str, Any]] = {}


def run_with_tools(
    user_message: str,
    system_prompt: str | None = None,
    max_iterations: int = MAX_ITERATIONS,
    model: str | None = None,
    use_batch: bool = False,
) -> Generator[Dict[str, Any], None, None]:
    """Run the tool loop. Yields events the SSE handler understands:

      {"type": "token",     "text": "..."}            visible text
      {"type": "tool_call", "name": "...", "ok": bool,
                            "error": "..."}          a tool was used
      {"type": "done",      "result": {...}}          final
      {"type": "error",     "error": "..."}           on failure
    """
    system_prompt = system_prompt or _read_prompt()
    # Chosen once, at the door. Never changed mid-loop: switching models
    # destroys the prompt cache.
    model = model or classify_task(user_message)
    # The static system prompt is the cache prefix. Everything that
    # changes — the date, the ecosystem, the repos — rides on the first
    # user message, after the breakpoint, where it is small.
    messages: List[Dict[str, Any]] = [{
        "role": "user",
        "content": _context_block() + "\n\n" + user_message,
    }]

    # The learned-answer cache, before the model. A hit means no model
    # call: the loop answers and returns. Deterministic — the model is
    # never given the chance to skip it. A cache failure is a miss, not
    # a dead butler: the try/except is the whole point.
    try:
        from routers.tools import answer_cache as _answer_cache
        _cached = _answer_cache(user_message)
        # ONE shape, ONE read. answer_cache returns {ok, result: {hit: {answer}}}.
        # The old code logged a top-level "hit" (always absent, so always
        # False) and read result.hit for the hit path — two keys, one of
        # them wrong. Read the payload once and use it for both.
        _hit_payload = (_cached.get("result") or {}).get("hit") if _cached.get("ok") else None
        _hit_answer = (_hit_payload or {}).get("answer") if isinstance(_hit_payload, dict) else _hit_payload
        logging.info(
            "answer_cache hit=%s question=%s",
            bool(_hit_answer), (user_message or "")[:80],
        )
        if _hit_answer:
            yield {"type": "token", "text": str(_hit_answer)}
            yield {"type": "done", "result": {"ok": True, "iterations": 0, "stop_reason": "cache"}}
            return
    except Exception as _ce:
        logging.warning("answer_cache check failed: %s", _ce)

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
            if use_batch:
                try:
                    response = _call_api_batch(system_prompt, messages, model=model)
                except Exception as _be:
                    logging.warning("batch failed, falling back to sync: %s", _be)
                    response = _call_api(system_prompt, messages, model=model)
            else:
                response = _call_api(system_prompt, messages, model=model)
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
                # The final turn. The model stopped with tool results in
                # hand and wrote nothing — the read-and-stop the log has
                # shown since 31 Oct. Before giving up, ask it once, in
                # plain words, to compose. The tool results are already
                # in messages; this adds no tool call, just a nudge. If
                # it still writes nothing, the cannot_help below is
                # honest. Bounded: one extra call, only on the failure
                # path, never on a normal run.
                try:
                    nudge = _call_api(
                        system_prompt,
                        messages + [{
                            "role": "user",
                            "content": (
                                "You have the tool results above. Reply to the "
                                "founder now, in plain text, using what you read. "
                                "Do not call another tool."
                            ),
                        }],
                    )
                    for block in (nudge.get("content") or []):
                        if block.get("type") == "text" and block.get("text"):
                            yield {"type": "token", "text": block["text"]}
                            _any_text = True
                    if _any_text:
                        yield {
                            "type": "done",
                            "result": {
                                "ok": True,
                                "iterations": iteration + 1,
                                "stop_reason": "final_turn",
                            },
                        }
                        return
                except Exception as e:
                    logging.warning("tool loop: final turn failed: %s", e)

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

            _cache_key = (name, __import__("hashlib").sha1(
                json.dumps(args, sort_keys=True, default=str).encode()
            ).hexdigest()[:16])
            if name not in _WRITE_TOOLS and _cache_key in _TOOL_CACHE:
                result = _TOOL_CACHE[_cache_key]
                logging.info("tool call: %s cached=True", name)
            else:
                result = dispatch(name, args)
                if name not in _WRITE_TOOLS and result.get("ok"):
                    _TOOL_CACHE[_cache_key] = result
            # Every tool call is logged, success and failure. Without this,
            # "did the tool fire?" is answerable only by the reply, and the
            # reply can lie. The warnings record failures; this records the
            # fact. 2 Nov: the shaped test could not prove read_accord ran
            # because nothing logged a successful call.
            _u = (locals().get("response") or {}).get("_usage") or {}
            _m = (locals().get("response") or {}).get("_model") or model
            logging.info(
                "tool call: %s ok=%s model=%s in=%s out=%s cache_read=%s cache_write=%s args=%s",
                name,
                bool(result.get("ok")),
                _m,
                _u.get("input_tokens", "?"),
                _u.get("output_tokens", "?"),
                _u.get("cache_read_input_tokens", "?"),
                _u.get("cache_creation_input_tokens", "?"),
                json.dumps(args, default=str)[:120],
            )
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
                    "input": {"path": "NEXT.md"},
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

    def fake_call_api(system_prompt, messages, timeout=LLM_TIMEOUT, model=None, build=""):
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
        # the final-turn nudge gets its own (still silent) round, so the
        # guard is proven by the model staying silent twice — not by the
        # nudge raising on an exhausted script.
        {"stop_reason": "end_turn", "content": []},
    ]

    def fake_silent(system_prompt, messages, timeout=LLM_TIMEOUT, model=None, build=""):
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

    def fake_repeated(system_prompt, messages, timeout=LLM_TIMEOUT, model=None, build=""):
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

    def fake_runaway(system_prompt, messages, timeout=LLM_TIMEOUT, model=None, build=""):
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

    # ---- final-turn test: a tool round, then silence, then compose ----
    # The stall proven by the log: the model calls a tool, stops with no
    # text, and the loop used to give up. The fix asks once, in plain
    # words, before cannot_help. This is that test.
    final_rounds = [
        {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "f1", "name": "read_file", "input": {"path": "PLAN.md"}}]},
        {"stop_reason": "end_turn", "content": []},   # silence — the stall
        {"stop_reason": "end_turn", "content": [
            {"type": "text", "text": "Here is what the plan says."}]},  # the nudge works
    ]

    def fake_final(system_prompt, messages, timeout=LLM_TIMEOUT, model=None, build=""):
        return final_rounds.pop(0)

    globals()["_call_api"] = fake_final
    try:
        final_events = list(run_with_tools("read the plan and tell me"))
    finally:
        globals()["_call_api"] = real_call

    final_tokens = [e for e in final_events if e.get("type") == "token"]
    final_dones = [e for e in final_events if e.get("type") == "done"]
    check(
        "final turn composes after a silent round",
        any("Here is what the plan says." in (t.get("text") or "") for t in final_tokens),
        detail=f"tokens: {[t.get('text','')[:60] for t in final_tokens]}",
    )
    check(
        "final turn stops with stop_reason final_turn",
        bool(final_dones) and final_dones[-1].get("result", {}).get("stop_reason") == "final_turn",
        detail=f"done: {final_dones[-1].get('result') if final_dones else None}",
    )
    check(
        "final turn does not set cannot_help",
        not any(t.get("cannot_help") for t in final_tokens),
        detail=f"tokens: {[t.get('cannot_help') for t in final_tokens]}",
    )

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_selftest())
