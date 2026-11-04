#!/usr/bin/env python3
"""Companies House matching is honest: a real company matches, a made-up
name does not, and a dissolved company is not trusted.

A match is proof of corporate status (PECR: cold email is lawful to a
corporate subscriber); no match is evidence of not-corporate. A wrong
high match would let a sole trader onto the email list; a dissolved
company is not a client.
"""
import sys

sys.path.insert(0, "/home/bosly_accord/bosly-gov")


def main() -> int:
    print("")
    print("Invariant: Companies House matching is honest")
    print("-" * 52)
    ok = True
    try:
        from scripts.ch_match import match
    except Exception as e:
        print(f"  FAIL: cannot import ch_match: {e}")
        print("SUMMARY: FAIL")
        return 1

    real = match("Lintzford Garden Centre", "NE39")
    real_ok = real.get("match_confidence") in ("high", "medium") and real.get("ch_status") == "active"
    print(f"  a real active company matches: {real_ok} ({real.get('ch_name')}, {real.get('match_confidence')})")
    ok = ok and real_ok

    fake = match("Zzxq Nonexistent Widgets Ltd", "NE1")
    fake_ok = not fake or fake.get("match_confidence") == "low"
    print(f"  a made-up name is not a trusted match: {fake_ok} ({fake.get('match_confidence')})")
    ok = ok and fake_ok

    # A name that matches a DISSOLVED company exactly: the status rule
    # must demote it, whatever the name similarity.
    diss = match("Garden Shop London Limited", "SE1")
    diss_ok = diss.get("match_confidence") == "low"
    print(f"  a dissolved company is demoted to low: {diss_ok} "
          f"({diss.get('ch_status')}, {diss.get('match_confidence')})")
    ok = ok and diss_ok

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
