#!/usr/bin/env python3
"""The founder token is in the processes that need it.

It has gone missing from a running process four times in two days, and
each time it was found by something downstream — a 404, a JSON parse
error, a /proc read that came back zero. This check is the sentinel.

Accord's next-server must carry FOUNDER_SERVICE_TOKEN to accept the
butler's request. Gov sends it; it falls back to the file, so Gov's env
is not load-bearing, but if it is present it should be present.

Reads /proc/<pid>/environ as the same user; no sudo needed for one's
own processes. Never prints the value.

Run:
    python3 checks/founder_token_in_process.py
"""
import os
import re
import sys


def proc_env(pid: int) -> dict:
    out = {}
    try:
        raw = open(f"/proc/{pid}/environ", "rb").read().decode("utf-8", "replace")
    except OSError:
        return out
    for kv in raw.split("\0"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            out[k] = v
    return out


def owner_of_3100() -> int | None:
    """The pid that LISTENS on 3100 — Accord's server, by identity.

    Two apps on this box run a process called next-server (Accord and
    Keep). Matching the name found Keep's server three times in one
    session and made the founder token look missing when it was not.
    The port is the identity: only one process owns 3100.
    """
    try:
        import subprocess
        out = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return None
    for line in out.splitlines():
        if ":3100 " in line and "pid=" in line:
            m = re.search(r"pid=(\d+)", line)
            if m:
                return int(m.group(1))
    return None


def other_next_servers(exclude: int | None) -> list[tuple[int, str]]:
    """Every other next-server, with its cwd, as a NOTE not a failure."""
    found = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            cmd = open(f"/proc/{d}/cmdline", "rb").read().decode("utf-8", "replace")
        except OSError:
            continue
        if "next-server" not in cmd:
            continue
        pid = int(d)
        if pid == exclude:
            continue
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError:
            cwd = "?"
        found.append((pid, cwd))
    return found


def main() -> int:
    print("")
    print("Invariant: the founder token is in the process that serves 3100")
    print("-" * 52)

    pid = owner_of_3100()
    ok = True
    if pid is None:
        print("  FAIL: nothing is listening on 3100 (Accord down?)")
        ok = False
    else:
        env = proc_env(pid)
        has = "FOUNDER_SERVICE_TOKEN" in env
        print(f"  Accord pid {pid} (owns 3100): token {'present' if has else 'MISSING'}")
        if not has:
            ok = False

    others = other_next_servers(pid)
    for opid, cwd in others:
        print(f"  NOTE: another next-server pid {opid} at {cwd} (not this check's business)")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
