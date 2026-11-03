#!/usr/bin/env python3
"""The cost trend can only go down.

A green tier says the code should be cheap. This says it IS cheap, or
that something changed: it reads the usage log, prices each call from
the table, and fails if the average pence per turn rose week-on-week.

It prints the breakdown, so the check output is the picture: which
model, how many turns, what each turn cost.
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: the cost per turn is not rising")
    print("-" * 52)
    ok = True
    try:
        from routers import usage as u
    except Exception as e:
        print(f"  FAIL: cannot import usage: {e}")
        print("SUMMARY: FAIL")
        return 1

    t = u.trend()["result"]
    this, last = t["this_week"], t["last_week"]
    print(f"  this week: {this['turns']} turns, {this['pence']}p, {this['avg']}p/turn")
    print(f"  last week: {last['turns']} turns, {last['pence']}p, {last['avg']}p/turn")

    if last["turns"] < 5:
        print("  NOTE: not enough history yet; the trend starts once there are turns")
    else:
        rising = t["rising"]
        print(f"  rising: {rising}")
        ok = ok and not rising

    tot = u.total()["result"]
    for model, m in sorted(tot.get("by_model", {}).items()):
        print(f"  {model}: {m['turns']} turns, {m['pence']}p, {m['batch']} in batch")
    for build, b in sorted(tot.get("by_build", {}).items()):
        print(f"  build {build}: {b['turns']} turns, {b['pence']}p")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
