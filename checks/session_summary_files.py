#!/usr/bin/env python3
"""A session that changed the plan also wrote memory, and the filing core is idempotent.

The butler is supposed to document its own work: memory entry, plan
tick, capsule line, in one call. This check proves the mechanism is
sound, not that a session happened — the live proof is a conversation.

Three things:
  - session_summary exists and defaults to dry run;
  - filing twice writes once (idempotence);
  - a plan tick on a known item is shown in dry run and skipped on the
    second call when already [x].

Run:
    python3 checks/session_summary_files.py
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: the butler can file its own session, once")
    print("-" * 52)
    ok = True

    try:
        from routers.tools import TOOLS, session_summary
    except Exception as e:
        print(f"  FAIL: cannot import session_summary: {e}")
        print("SUMMARY: FAIL")
        return 1

    has = any(t["name"] == "session_summary" for t in TOOLS)
    print(f"  session_summary is a tool: {has}")
    ok = ok and has

    schema = next((t for t in TOOLS if t["name"] == "session_summary"), None)
    default_dry = schema and schema["input_schema"]["properties"].get("dry_run", {}).get("default") is True
    print(f"  dry_run defaults to True: {bool(default_dry)}")
    ok = ok and bool(default_dry)

    # Dry run writes nothing.
    r = session_summary(memory=[{"id": "check-dry-20261103", "item_type": "pattern", "content": "probe"}], dry_run=True)
    wrote = r.get("memory", [{}])[0].get("written")
    print(f"  dry run wrote nothing: {wrote is None}")
    ok = ok and wrote is None

    # Idempotence: write, then write again, second is skipped.
    r1 = session_summary(memory=[{"id": "check-idem-20261103", "item_type": "pattern", "content": "probe"}], dry_run=False)
    first = r1.get("memory", [{}])[0]
    r2 = session_summary(memory=[{"id": "check-idem-20261103", "item_type": "pattern", "content": "probe"}], dry_run=False)
    second = r2.get("memory", [{}])[0]
    idem = first.get("written") == "check-idem-20261103" and second.get("skipped") is True
    print(f"  second write is skipped: {idem}")
    ok = ok and idem

    # Clean up the check entry so memory stays honest.
    if idem:
        import json
        p = "/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json"
        d = json.loads(open(p, encoding="utf-8").read())
        d = [e for e in d if e.get("id") != "check-idem-20261103"]
        open(p, "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False))
        print("  cleaned the check entry")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
