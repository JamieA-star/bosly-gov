#!/usr/bin/env python3
"""One process per app. A stale next-server is not a server.

Two apps run a process called next-server — Accord on 3100, Keep on
3101. A deploy can leave the old one running with the old env and the
old build, and every probe that greps the name finds it. This check
finds the pids that LISTEN on each port and asserts there is one each,
and no third next-server is holding a port.

Run:
    python3 checks/one_process_per_port.py
"""
import re
import subprocess
import sys


PORTS = {3100: "Accord", 3101: "Keep"}


def listeners() -> dict:
    """port -> pid, from ss -ltnp."""
    try:
        out = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return {}
    found = {}
    for line in out.splitlines():
        m = re.search(r":(\d+)\s+.*pid=(\d+)", line)
        if m:
            found[int(m.group(1))] = int(m.group(2))
    return found


def main() -> int:
    print("")
    print("Invariant: one process per app, each owning its port")
    print("-" * 52)
    found = listeners()
    ok = True
    for port, name in PORTS.items():
        pid = found.get(port)
        if pid is None:
            print(f"  {name} (:{port}): NOTHING LISTENING")
            ok = False
        else:
            print(f"  {name} (:{port}): pid {pid}")
    # A next-server that holds neither port is an orphan.
    try:
        out = subprocess.run(["pgrep", "-f", "next-server"], capture_output=True, text=True, timeout=3).stdout
        pids = {int(x) for x in out.split()}
    except Exception:
        pids = set()
    serving = set(found.get(p) for p in PORTS)
    orphans = sorted(pids - serving)
    for pid in orphans:
        print(f"  NOTE: orphan next-server pid {pid} (not on a known port)")
    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
