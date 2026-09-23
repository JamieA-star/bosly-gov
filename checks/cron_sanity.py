#!/usr/bin/env python3
"""
Check: cron-invoked scripts are runnable under cron.

Two assertions:

  1. SHEBANG ON BYTE 1 — every cron-invoked SCRIPT (not binary)
     has '#!' as its first two bytes. The kernel only reads
     bytes 0-1 for '#!'. If they aren't there, the file is
     treated as plain text and executed by the user's default
     shell (dash on Ubuntu). This is the class of bug that left
     bosly-monitor silently dead for 36 days.

  2. SELF-PROVIDED PATH FOR BINARIES — if a cron script calls a
     binary that isn't on cron's minimal PATH (/usr/bin:/bin),
     the script itself must load that binary onto PATH (e.g. by
     sourcing nvm). We detect this by looking for nvm.sh or a
     PATH export in the script's body.

Exit 0 if all assertions hold, 1 otherwise.

Run:
    python3 checks/cron_sanity.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

CRON_PATH = "/usr/bin:/bin"

# Binaries we care about. If a cron script calls one of these and
# it's not reachable under CRON_PATH, the script must provide it.
WATCHED_BINARIES = ["node", "pm2", "psql", "curl", "python3", "bash", "git"]

# Patterns in a script that indicate it loads its own PATH.
SELF_PATH_PATTERNS = [
    re.compile(r"nvm\.sh"),
    re.compile(r"export\s+PATH="),
    re.compile(r"PATH=.*:\$PATH"),
    re.compile(r"^\.\s+/.*nvm"),
    re.compile(r"source\s+.*nvm"),
]

passed = 0
failed = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}")
        if detail:
            for line in detail.splitlines():
                print(f"      {line}")


def is_text_script(path: Path) -> bool:
    """Return True if the file looks like a text script we should
    treat as a script (not a compiled binary).

    Heuristic: readable as text, and either has a shebang on byte 1
    or has a script-like extension (.sh, .py, .cjs, .js, .ts) or
    has no extension at all.
    """
    try:
        with path.open("rb") as f:
            head = f.read(4)
        # If the first two bytes are '#!' it's definitely a script.
        if head[:2] == b"#!":
            return True
        # If the first byte is 0x7F (ELF magic starts with 0x7F)
        # it's a binary.
        if head[:1] == b"\x7f":
            return False
        # Extension-based heuristic
        ext = path.suffix.lower()
        if ext in {".sh", ".bash", ".py", ".cjs", ".js", ".ts", ".mjs"}:
            return True
        if ext == "":
            return True
        return False
    except Exception:
        return False


def has_shebang(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(2) == b"#!"
    except Exception:
        return False


def is_binary(path: Path) -> bool:
    """Return True if this looks like a compiled binary, not a script."""
    try:
        with path.open("rb") as f:
            head = f.read(4)
        # ELF magic
        if head[:4] == b"\x7fELF":
            return True
        # Mach-O / PE etc. — not relevant here but be conservative
        return False
    except Exception:
        return False


def get_crontab() -> str:
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, timeout=10
        )
        return result.stdout
    except Exception:
        return ""


def extract_cron_script_paths(crontab: str) -> list[Path]:
    """From a crontab, return absolute paths of SCRIPTS invoked.

    Excludes compiled binaries (like /usr/bin/python3). Those are
    always executed by the kernel without a shebang requirement.
    """
    paths: list[Path] = []
    for raw_line in crontab.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        cmd = " ".join(parts[5:])
        for m in re.finditer(r"(/[^\s'\"|&;<>()]+)", cmd):
            candidate = m.group(1)
            p = Path(candidate)
            if not (p.exists() and p.is_file() and os.access(p, os.X_OK)):
                continue
            # Skip compiled binaries
            if is_binary(p):
                continue
            if p not in paths:
                paths.append(p)
    return paths


def binaries_in_script(path: Path) -> set[str]:
    """Return the WATCHED_BINARIES this script appears to call.

    Only reads text files. Skips binaries.
    """
    found: set[str] = set()
    if is_binary(path):
        return found
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return found
    for i, line in enumerate(text.splitlines()):
        if i == 0 and line.startswith("#!"):
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for binary in WATCHED_BINARIES:
            if re.search(rf"\b{re.escape(binary)}\b", stripped):
                found.add(binary)
    return found


def script_provides_own_path(path: Path) -> bool:
    """Return True if the script body loads a PATH or nvm itself."""
    if is_binary(path):
        return False
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return False
    for pattern in SELF_PATH_PATTERNS:
        if pattern.search(text):
            return True
    return False


def binary_reachable_under_cron(binary: str) -> bool:
    for d in CRON_PATH.split(":"):
        p = Path(d) / binary
        if p.exists() and os.access(p, os.X_OK):
            return True
    return False


def main() -> int:
    print("")
    print("Invariant: cron scripts are runnable under cron")
    print("-" * 52)
    print("")

    crontab = get_crontab()
    cron_scripts = extract_cron_script_paths(crontab)

    print(f"  cron-invoked scripts found: {len(cron_scripts)}")
    for s in cron_scripts:
        print(f"    {s}")
    print("")

    # --- 1. Shebang on byte 1 ---
    for script in cron_scripts:
        check(f"{script} shebang on byte 1", has_shebang(script),
              detail="First two bytes are not '#!/'.")

    # --- 2. Binaries callable, OR the script provides its own PATH ---
    for script in cron_scripts:
        provides_path = script_provides_own_path(script)
        binaries = binaries_in_script(script)
        for binary in sorted(binaries):
            if binary_reachable_under_cron(binary):
                check(f"{script.name} can find '{binary}' (on cron PATH)", True)
            elif provides_path:
                check(
                    f"{script.name} provides '{binary}' via its own PATH",
                    True,
                )
            else:
                check(
                    f"{script.name} can find '{binary}'",
                    False,
                    detail=f"'{binary}' is not on /usr/bin:/bin and the "
                           f"script does not load its own PATH. Add a "
                           f"PATH export or nvm sourcing at the top.",
                )

    # --- 3. /usr/local/bin/bosly-* scripts have shebangs ---
    bin_dir = Path("/usr/local/bin")
    bosly_scripts = [
        p for p in sorted(bin_dir.glob("bosly*"))
        if p.is_file() and os.access(p, os.X_OK) and is_text_script(p)
    ]
    for script in bosly_scripts:
        check(f"{script} shebang on byte 1", has_shebang(script),
              detail="First two bytes are not '#!/'.")

    print("")
    print("-" * 52)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
