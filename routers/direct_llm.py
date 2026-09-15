"""Direct LLM call utilities with Claude streaming support."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable, Dict, Generator, Iterable, Optional, Tuple

ENV_FILE = "/home/bosly_accord/bosly-1.0/.env.production"
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"\'')
                
StreamEvent = Dict[str, object]
TokenCallback = Optional[Callable[[str], None]]

def call_llm_direct(system_prompt: str, user_message: str, timeout: int = 120) -> Tuple[int, str, str]:
    claude_key = os.environ.get("CLAUDE_API_KEY", "")
    if claude_key:
        return _call_claude(system_prompt, user_message, timeout)
    return _call_civo(system_prompt, user_message, timeout)

def stream_llm_direct(system_prompt: str, user_message: str, timeout: int = 120) -> Generator[StreamEvent, None, None]:
    claude_key = os.environ.get("CLAUDE_API_KEY", "")
    if claude_key:
        yield from _stream_claude(system_prompt, user_message, timeout)
    else:
        rc, text, err = _call_civo(system_prompt, user_message, timeout)
        if rc != 0:
            yield {"type": "error", "error": err or "LLM call failed"}
            return
        if text:
            yield {"type": "token", "text": text}
        yield {"type": "done", "text": text}

def _call_claude(system_prompt: str, user_message: str, timeout: int) -> Tuple[int, str, str]:
    parts = []
    err_text = ""
    for event in _stream_claude(system_prompt, user_message, timeout):
        et = event.get("type")
        if et == "token":
            parts.append(str(event.get("text") or ""))
        elif et == "error":
            err_text = str(event.get("error") or "Claude call failed")
    final = "".join(parts).strip()
    if err_text and not final:
        return 1, "", err_text
    if not final:
        return 1, "", "Empty Claude response"
    return 0, final, ""

def _stream_claude(system_prompt: str, user_message: str, timeout: int) -> Generator[StreamEvent, None, None]:
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    api_key = os.environ.get("CLAUDE_API_KEY", "")

    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 8000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
            "stream": True,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "accept": "text/event-stream",
        },
    )

    buffer_text_parts = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                except Exception:
                    continue

                ev_type = str(event.get("type") or "")
                if ev_type == "content_block_delta":
                    delta = event.get("delta") or {}
                    text = str(delta.get("text") or "")
                    if text:
                        buffer_text_parts.append(text)
                        yield {"type": "token", "text": text}
                elif ev_type == "message_delta":
                    # ignore token accounting here
                    pass
                elif ev_type == "error":
                    err = event.get("error") or {}
                    msg = str(err.get("message") or "Claude stream error")
                    yield {"type": "error", "error": msg}
                    return

    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(e)
        yield {"type": "error", "error": f"Claude HTTP error: {detail[:500]}"}
        return
    except Exception as e:
        yield {"type": "error", "error": f"Claude call failed: {str(e)[:500]}"}
        return

    final_text = "".join(buffer_text_parts).strip()
    yield {"type": "done", "text": final_text}

def _call_civo(system_prompt: str, user_message: str, timeout: int) -> Tuple[int, str, str]:
    api_url = os.environ.get("OPENAI_BASE_URL", "https://api.relax.ai/v1") + "/chat/completions"
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("OPENAI_MODEL", "Llama-4-Maverick-17B-128E")

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 8000,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))

        choice = body.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "") or msg.get("reasoning_content", "")
        if not content:
            return 1, "", f"Empty response: {json.dumps(body)[:500]}"
        return 0, str(content).strip(), ""
    except Exception as e:
        return 1, "", f"Civo call failed: {str(e)[:500]}"
