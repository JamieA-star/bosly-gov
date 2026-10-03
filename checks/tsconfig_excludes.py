#!/usr/bin/env python3
"""
Check: directories excluded from tsconfig do not contain live code.

An excluded directory is invisible to tsc. If it contains source the
app imports, that source is never type-checked — which is how the
iCloud calendar routes sat broken for weeks (3 Oct).

This lists every excluded directory that contains .ts/.tsx source,
except an explicit deliberate-list (dependencies, build output, the
legacy archive). Everything it reports is a question worth asking:
is this exclusion deliberate, or is live code being hidden?

Report-only at first.

Run:
    python3 checks/tsconfig_excludes.py
"""

import re
import sys
from pathlib import Path

REPO = Path("/home/bosly_accord/bosly-1.0")
TSCONFIG = REPO / "tsconfig.json"

# Excluded, and correctly so: not our source, or deliberately retired.
DELIBERATE = [
    "node_modules",
    ".next",
    "backups",
    "tools",
    "src",
    "legacy",
    "./legacy",
    "test-",
]

REPORT_ONLY = True


def is_deliberate(entry: str) -> bool:
    e = entry.lstrip("./")
    return any(e.startswith(d.lstrip("./")) for d in DELIBERATE)


def main() -> int:
    print("")
    print("Invariant: tsconfig excludes do not hide live source")
    print("----------------------------------------------------")

    if not TSCONFIG.exists():
        print(f"  SKIP: {TSCONFIG} not found")
        print("")
        return 0

    text = TSCONFIG.read_text(encoding="utf-8")
    m = re.search(r'"exclude"\s*:\s*\[(.*?)\]', text, re.S)
    if not m:
        print("  SKIP: no exclude block in tsconfig")
        print("")
        return 0

    entries = re.findall(r'"([^"]+)"', m.group(1))

    flagged = []
    for e in entries:
        if is_deliberate(e):
            continue
        p = REPO / e.replace("/**", "").replace("*", "")
        if not p.exists() or not p.is_dir():
            continue
        srcs = list(p.rglob("*.ts")) + list(p.rglob("*.tsx"))
        if srcs:
            flagged.append((e, len(srcs)))

    print(f"  {len(entries)} exclude entries, {len(flagged)} not deliberate")
    print("")
    if flagged:
        print("  Excluded directories that contain source:")
        for e, n in flagged:
            print(f"    {e}  ({n} file(s))")
        print("")
        print("  Each is a question: deliberate exclusion, or hidden live code?")
    else:
        print("  OK: no non-deliberate exclude contains source")

    print("")
    verdict = "REPORT" if REPORT_ONLY else ("PASS" if not flagged else "FAIL")
    print(f"SUMMARY: {verdict} ({len(flagged)} flagged)")
    print("")
    return 0 if (REPORT_ONLY or not flagged) else 1


if __name__ == "__main__":
    sys.exit(main())
