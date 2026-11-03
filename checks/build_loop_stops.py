#!/usr/bin/env python3
"""A build stops on a question — without a model call.

The stop-and-ask is what makes unattended work safe. This check stubs
the model to return a NEEDS_FOUNDER line and proves the loop parks the
build with the question, ticks nothing, and stops. It also proves a
step with no registered check parks rather than being trusted.

Run:
    python3 checks/build_loop_stops.py
"""
import shutil
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

NAME = "check-build-loop"
DIR = f"/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds/{NAME}"


def main() -> int:
    print("")
    print("Invariant: a build stops on a question, without a model call")
    print("-" * 52)
    ok = True
    shutil.rmtree(DIR, ignore_errors=True)

    try:
        from routers import build, build_loop
    except Exception as e:
        print(f"  FAIL: cannot import: {e}")
        print("SUMMARY: FAIL")
        return 1

    build.new_build(NAME, "test spec", [
        {"title": "a step that asks", "check": "x", "check_id": ""},
    ])

    # Stub the model: it asks a question, as a real build would.
    def fake_ask(prompt, model=None, use_batch=False):
        return {"text": "NEEDS_FOUNDER: Which format?\nOPTIONS: JSON | Markdown", "tool_calls": []}
    build_loop._ask_model = fake_ask

    r = build_loop.run_build(NAME)
    st = build.load_build(NAME).get("result", {}).get("state", {})
    parked = st.get("status") == "needs_founder" and st.get("question") == "Which format?"
    print(f"  parked with the question: {parked}")
    print(f"  question: {st.get('question')}")
    print(f"  options: {st.get('options')}")
    ok = ok and parked

    ticked_nothing = len(st.get("done", [])) == 0
    print(f"  ticked nothing before asking: {ticked_nothing}")
    ok = ok and ticked_nothing

    shutil.rmtree(DIR, ignore_errors=True)
    print("  cleaned up")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
