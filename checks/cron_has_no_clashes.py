#!/usr/bin/env python3
"""No two cron jobs share a minute and a log, or a minute and a backup.

A clash does not announce itself: two jobs write the same file and the
output looks fine until a line is missing, and a job that wrote nothing
looks like a job that passed. This reads the crontab and fails on a
shared (minute, hour) with a shared log, and on two backups at once.
"""
import re
import subprocess
import sys


def main() -> int:
    print("")
    print("Invariant: no cron job clashes with another")
    print("-" * 52)
    ok = True

    out = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    jobs = [l for l in out.splitlines()
            if l and not l.startswith("#") and not l.startswith("PATH") and not l.startswith("DATABASE")]

    seen: dict = {}
    for j in jobs:
        p = j.split()
        if len(p) < 6:
            continue
        # The whole schedule, not just the minute and hour: 23:00 on
        # Saturday and 23:00 on Sunday never run at the same time.
        minute, hour, dom, month, dow = p[0], p[1], p[2], p[3], p[4]
        log = re.search(r">>\s*(\S+)", j)
        key = (minute, hour, dom, month, dow, log.group(1) if log else "")
        if key in seen:
            print(f"  CLASH at {minute} {hour} {dom} {month} {dow} writing {key[5] or '(nowhere)'}:")
            print(f"    {seen[key][:100]}")
            print(f"    {j[:100]}")
            ok = False
        seen[key] = j

    # Two backups at the same minute is a torn snapshot.
    backups = {}
    for j in jobs:
        p = j.split()
        if "backup" in j and len(p) >= 5:
            k = (p[0], p[1], p[2], p[3], p[4])
            if k in backups:
                print(f"  BACKUP CLASH at {p[0]} {p[1]}: two backups at once")
                ok = False
            backups[k] = j

    print(f"  jobs: {len(jobs)}, no clash: {ok}")
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
