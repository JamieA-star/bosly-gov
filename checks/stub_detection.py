#!/usr/bin/env python3
"""
Check: production-named functions that admit they're stubs.

A function whose name implies a real capability (reconstruct,
derive, generate, render, extract, parse, fetch, encrypt,
decrypt, send, build, request) but whose body or docstring
contains "stub", "placeholder", "TODO", "FIXME", "not
implemented", or "not yet implemented" is a lie the user
experiences: the caller expects real output, the function
returns a placeholder.

This is not the same as:
  - A guard clause (`if (!x) return []`) — the function is
    real; that's a valid empty case.
  - A feature flag (`isFeatureEnabled() { return true }`) —
    the name doesn't claim production capability.
  - A stub nobody calls — dead but harmless. Noted, not
    failed.

Motivated by the deletion of lib/inboxStore.js (255 bytes,
four no-op exports, zero callers) on 24 Sept 2026, and by
the dead mailparser block in the old enrich-contacts route.

A function is flagged when all three are true:
  1. The name matches a capability pattern.
  2. The body or adjacent comments admit it's a stub.
  3. The function is called from live code (not its own file,
     not tests, not scripts).

Existing, documented stubs are in ALLOWLIST below. Any new
stub fails.

Exit 0 if no new stubs, 1 otherwise.

Run:
    python3 checks/stub_detection.py
    python3 checks/stub_detection.py --dry-run   # show all candidates
    python3 checks/stub_detection.py --verbose   # show matches + allowlist hits
"""

import re
import sys
from pathlib import Path

ACCORD_ROOT = Path("/home/bosly_accord/bosly-1.0")

# Directories to scan (relative to ACCORD_ROOT).
SCAN_DIRS = ["lib", "app/api"]

# Directories/files to skip during the walk.
SKIP_DIRS = {"node_modules", ".next", "tests", "scripts", "legacy", "__tests__"}

# Only these extensions.
SCAN_EXTS = {".ts", ".tsx"}

# Function names matching these prefixes are "production capability"
# claims. A stub with one of these names is what this check looks for.
CAPABILITY_PREFIXES = [
    "reconstruct", "derive", "generate", "render",
    "extract", "parse", "fetch", "encrypt", "decrypt",
    "send", "build", "request",
]

# Phrases that admit a stub. Case-insensitive.
#
# 'for now' is deliberately NOT in this list. It means too many
# things: 'this is a stub' (a bug), 'we're doing X for now, will
# change later' (not a bug), or 'this fallback will be removed'
# (a documented short-term decision). The signal-to-noise ratio
# on 'for now' is poor. The remaining phrases mean one thing:
# this function does not do what its name implies.
ADMISSION_PATTERNS = [
    re.compile(r"\bstub\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bnot\s+(yet\s+)?implemented\b", re.IGNORECASE),
]

# Functions we know are stubs, that are documented, and that
# should not fail this check. Any function not in this list
# that matches the rule is a new stub — it fails.
ALLOWLIST = [
    ("lib/workflow/bridges/language.ts", "requestFromLanguage"),
    ("lib/workflow/bridges/vault.ts", "requestFromVault"),
    ("lib/social/render.ts", "renderSocialMediaImage"),
]

# ─── extraction ───

# Matches: export async function name(...)  /  export function name(...)
FUNC_RE = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*[<(]",
)


def is_capability(name: str) -> bool:
    lower = name.lower()
    return any(lower.startswith(p) for p in CAPABILITY_PREFIXES)


def admits_stub(text: str) -> str | None:
    for pat in ADMISSION_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def read_body_and_comment(lines: list[str], start_idx: int) -> str:
    """
    From the function's `function name(` line, gather the next
    ~30 lines, plus the preceding ~15 lines for docstring
    comments. Bounded so we don't grab the whole file.
    """
    pre = lines[max(0, start_idx - 15):start_idx]
    post = lines[start_idx:min(len(lines), start_idx + 30)]
    return "\n".join(pre + post)


def find_functions(path: Path) -> list[tuple[str, int, str]]:
    """Returns [(name, line_number_1based, context_text), ...]"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = text.splitlines()
    found: list[tuple[str, int, str]] = []
    for i, line in enumerate(lines):
        for m in FUNC_RE.finditer(line):
            name = m.group(1)
            context = read_body_and_comment(lines, i)
            found.append((name, i + 1, context))
    return found


def walk(root: Path) -> list[Path]:
    out: list[Path] = []
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_dir():
                continue
            if p.suffix not in SCAN_EXTS:
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            out.append(p)
    return sorted(out)


def is_called_elsewhere(root: Path, func_name: str, own_file: Path) -> bool:
    """
    Search for `func_name` in any .ts/.tsx under SCAN_DIRS except
    the function's own file. Return True on first match.
    """
    for p in walk(root):
        if p == own_file:
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if func_name in content:
            return True
    return False


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ACCORD_ROOT))
    except ValueError:
        return str(path)


# ─── main ───

def main() -> int:
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    candidates: list[dict] = []
    allowlist_hits: list[dict] = []

    for file in walk(ACCORD_ROOT):
        rel_path = rel(file)
        for name, line_no, context in find_functions(file):
            if not is_capability(name):
                continue
            admission = admits_stub(context)
            if not admission:
                continue

            called = is_called_elsewhere(ACCORD_ROOT, name, file)
            is_allowlisted = (rel_path, name) in ALLOWLIST

            entry = {
                "file": rel_path,
                "name": name,
                "line": line_no,
                "admission": admission,
                "called": called,
                "allowlisted": is_allowlisted,
            }
            if is_allowlisted:
                allowlist_hits.append(entry)
            else:
                candidates.append(entry)

    print("")
    print("Invariant: stub detection")
    print("----------------------------------------------------")
    print(f"scanned:          {len(walk(ACCORD_ROOT))} files")
    print(f"allowlist size:   {len(ALLOWLIST)}")
    print(f"allowlist hits:   {len(allowlist_hits)}")
    print(f"unallowlisted:    {len(candidates)}")
    print("")

    if verbose and allowlist_hits:
        print("Allowlisted (known, documented):")
        for e in allowlist_hits:
            print(f"  OK  {e['file']}:{e['line']}  {e['name']}()")
        print("")

    if not candidates:
        print("PASS: no unallowlisted stubs in production-named functions")
        print("")
        print("SUMMARY: 0 findings")
        print("")
        return 0

    if dry_run:
        print("── DRY RUN — candidates that would be flagged ──")
        for e in candidates:
            called = "called" if e["called"] else "NOT called"
            print(
                f"  {e['file']}:{e['line']}  "
                f"{e['name']}()  [{e['admission']}]  ({called})"
            )
        print("")
        print(f"SUMMARY: {len(candidates)} candidates (dry-run, exit 0)")
        print("")
        return 0

    real = [c for c in candidates if c["called"]]
    uncalled = [c for c in candidates if not c["called"]]

    if real:
        print("── Stubs called from live code (FAIL) ──")
        for e in real:
            print(
                f"FAIL: {e['file']}:{e['line']}  "
                f"{e['name']}()  [{e['admission']}]"
            )
        print("")

    if uncalled:
        print("── Stubs not called anywhere (NOTE) ──")
        for e in uncalled:
            print(
                f"NOTE: {e['file']}:{e['line']}  "
                f"{e['name']}()  [{e['admission']}]"
            )
        print("")

    if real:
        print(f"SUMMARY: {len(real)} failures, {len(uncalled)} notes")
        print("")
        return 1

    print(f"SUMMARY: 0 failures, {len(uncalled)} notes")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
