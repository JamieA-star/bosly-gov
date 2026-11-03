#!/usr/bin/env python3
"""Run the active build to its next ending; email the founder if it parks.

Called by cron every 10 minutes. Safe to run when the build is done,
stuck, or already parked: it does nothing. When it parks, it sends ONE
email with the question, the options, and the sentence to paste back.
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

from routers import build as _build
from routers.build_loop import run_build
from routers.tools import send_draft_to_me

BUILD = "invoice-chips"


def main() -> int:
    loaded = _build.load_build(BUILD)
    if not loaded.get("ok"):
        print(f"no build {BUILD!r}; nothing to do")
        return 0
    state = loaded["result"]["state"]
    if state.get("status") in ("done", "stuck", "needs_founder"):
        print(f"{BUILD}: {state.get('status')}; nothing to do")
        return 0

    r = run_build(BUILD, use_batch=True)
    st = r.get("result", {}).get("state", {})
    status = st.get("status")

    if status == "needs_founder":
        opts = st.get("options") or []
        opt_lines = "\n".join(f"  {chr(65+i)}) {o}" for i, o in enumerate(opts)) or "  (no options given)"
        body = (
            f"Bosly stopped at step {st.get('current', 0) + 1} of {BUILD}.\n\n"
            f"Question: {st.get('question')}\n"
            f"Options:\n{opt_lines}\n\n"
            "Let me know and I'll continue. Reply in the app or the UI:\n"
            f'  "Hi Bosly, for {BUILD} I choose ..."\n'
        )
        send_draft_to_me(f"Bosly paused — needs one decision ({BUILD})", body)
        print(f"{BUILD}: parked, email sent")
    elif status == "stuck":
        print(f"{BUILD}: stuck — {st.get('question')}")
    elif status == "done":
        print(f"{BUILD}: done")
    else:
        print(f"{BUILD}: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
