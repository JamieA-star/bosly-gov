#!/usr/bin/env python3
"""plan_query counts what it returns, and the brief form is small.

The butler answered "what's on the plan?" five times with five different
numbers — 14 open, 88 open, 88 open, 88 open — because it was
summarising 88 full rows into 54 tokens and paraphrasing from memory.
The tool already derives the rows; what it lacked was a count the model
can quote and a brief form it can fit.

Two assertions:
  - the count in the result equals the number of rows;
  - the brief form's rows are under 200 characters each, so a full list
    is quotable rather than summarisable.
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: plan_query counts what it returns, and brief is small")
    print("-" * 52)
    ok = True

    try:
        from routers.tools import plan_query
    except Exception as e:
        print(f"  FAIL: cannot import plan_query: {e}")
        print("SUMMARY: FAIL")
        return 1

    full = plan_query(status="open")
    rows = (full.get("result") or {}).get("rows") or []
    count = (full.get("result") or {}).get("count")
    print(f"  full open rows: {len(rows)}, count field: {count}")
    ok = ok and count == len(rows)

    brief = plan_query(status="open", brief=True)
    brows = (brief.get("result") or {}).get("rows") or []
    bcount = (brief.get("result") or {}).get("count")
    print(f"  brief open rows: {len(brows)}, count field: {bcount}")
    ok = ok and bcount == len(brows)

    longest = max((len(str(r.get("first", ""))) for r in brows), default=0)
    print(f"  longest brief row: {longest} chars (target under 200)")
    ok = ok and longest < 200

    # Every brief row must still carry the id, so the model can quote it.
    all_have_id = all(r.get("id") for r in brows) if brows else True
    print(f"  every brief row has an id: {all_have_id}")
    ok = ok and all_have_id

    # The tool's schema is the interface the model reads. If it does not
    # name 'active', the model will call 'open' and subtract in its head.
    desc = next((t.get("description", "") for t in
                 __import__("routers.tools", fromlist=["TOOLS"]).TOOLS
                 if t.get("name") == "plan_query"), "")
    names_active = "active" in desc and "parked" in desc
    print(f"  description names active and parked: {names_active}")
    ok = ok and names_active

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
