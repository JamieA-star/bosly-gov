#!/usr/bin/env python3
"""A build that patched a file and has no done ticks is a failure.

The invoice build patched FinancePill.tsx and could not record the
proof: build_run ticks only after its own check, and build_tick was in
the tools and not in THE WORLD. This reads every build's state: if a
step wrote or patched and the done list is empty, the build failed to
record its proof — or must say why it has not ticked.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

BUILDS = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/builds")


def main() -> int:
    print("")
    print("Invariant: a build that patched also ticks, or says why")
    print("-" * 52)
    ok = True

    if not BUILDS.exists():
        print("  no builds yet")
        print("SUMMARY: PASS")
        return 0

    for d in sorted(BUILDS.iterdir()):
        sf = d / "state.json"
        if not sf.exists():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = st.get("status")
        done = st.get("done") or []
        q = st.get("question") or ""
        # A finished build with no ticks is a lie. A parked build with no
        # ticks is fine if the question says why.
        if status == "done" and not done:
            print(f"  FAIL: {d.name} is done with no ticks")
            ok = False
        elif status == "needs_founder" and not done and not q.strip():
            print(f"  FAIL: {d.name} is parked with no ticks and no question")
            ok = False
        else:
            print(f"  {d.name}: {status}, {len(done)} ticked — ok")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
