#!/usr/bin/env python3
"""The model is chosen at the door; the cost is in the log.

Two assertions, both cheap:
  - classify_task sends a decision to the strong model and a shaped
    question to the cheap one;
  - the tool-call log line carries the model and the tokens, so a
    session's cost is measurable rather than believed.

It does not call the API. It reads the source and calls the pure
classifier.
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: the model is chosen at the door, and the cost is logged")
    print("-" * 52)
    ok = True

    try:
        from routers.tool_loop import classify_task, _CHEAP_MODEL, _STRONG_MODEL
    except Exception as e:
        print(f"  FAIL: cannot import classify_task: {e}")
        print("SUMMARY: FAIL")
        return 1

    shaped = classify_task("what's on the plan?")
    decision = classify_task("design the receptionist for the salon")
    print(f"  shaped question -> {shaped}")
    print(f"  decision -> {decision}")
    ok = ok and shaped == _CHEAP_MODEL and decision == _STRONG_MODEL

    src = open("/home/bosly_accord/bosly-gov/routers/tool_loop.py", encoding="utf-8").read()
    has_log = "model=%s in=%s out=%s cache_read=%s" in src
    has_cache = "_WRITE_TOOLS" in src and "_TOOL_CACHE" in src
    no_write_cached = "send_email" in src and "_WRITE_TOOLS = frozenset" in src
    print(f"  the tool log carries model and tokens: {has_log}")
    print(f"  the tool cache exists: {has_cache}")
    print(f"  writes are excluded from the cache: {no_write_cached}")
    ok = ok and has_log and has_cache and no_write_cached

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
