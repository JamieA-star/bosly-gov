#!/usr/bin/env python3
"""
Invariant: gov.consent_gating_holds

Verifies the Trust Contract at the code level: no file is written
inside an allowed root unless a pending action has been approved.

Four assertions:

  1. apply_patch_to_text is pure — it contains no disk writes. The
     gate relies on candidate patches being held in memory only.

  2. _safe_write_file (the only function that writes to targets) is
     called exclusively from approve_pending_action. No other code
     path can write files.

  3. ALLOWED_WRITE_ROOTS names every repo Gov might be asked to fix.
     A missing entry means Gov silently cannot write there, or can
     write somewhere it should not.

  4. DENY_PATH_PATTERNS covers the standard sensitive file set.
     A missing pattern means an approval could theoretically
     overwrite credentials.

Failing (1) or (2) means the gate has been structurally broken.
Failing (3) means the gate is scoped wrongly.
Failing (4) means the deny list has gaps.

Run:
  python3 checks/consent_gating.py

Exit code: 0 if all hold, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

GOV_ROOT = Path("/home/bosly_accord/bosly-gov")
ROUTERS = GOV_ROOT / "routers"
CONSENT = ROUTERS / "consent_store.py"
PATCH = ROUTERS / "patch_engine.py"

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print("PASS: " + name)
    else:
        failed += 1
        print("FAIL: " + name + (" — " + detail if detail else ""))


def note(msg: str) -> None:
    print("NOTE: " + msg)


# ─── 1. apply_patch_to_text is pure ─────────────────────────────

print("")
print("── 1. apply_patch_to_text is pure ──")

if not PATCH.exists():
    check("patch_engine.py exists", False, str(PATCH))
else:
    src = PATCH.read_text(encoding="utf-8")
    # Find the function body by regex
    m = re.search(
        r"def apply_patch_to_text\([^)]*\)[^:]*:(.*?)(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    if not m:
        check("apply_patch_to_text found", False, "function definition not located")
    else:
        body = m.group(1)
        # Any of these patterns means it writes to disk
        write_patterns = [
            (r"\.write_text\s*\(", ".write_text()"),
            (r"\.write_bytes\s*\(", ".write_bytes()"),
            (r"open\s*\([^)]*[\"'][wa][\"']", "open(..., 'w'/'a')"),
            (r"Path\s*\([^)]*\)\.write_", "Path(...).write_*"),
        ]
        hits = []
        for pat, label in write_patterns:
            for match in re.finditer(pat, body):
                # Get line number relative to the whole file
                abs_pos = m.start(1) + match.start()
                line_no = src[:abs_pos].count("\n") + 1
                hits.append(f"{label} at line {line_no}")
        check(
            "apply_patch_to_text contains no disk writes",
            len(hits) == 0,
            "; ".join(hits) if hits else "",
        )


# ─── 2. _safe_write_file is only called from approve ─────────────

print("")
print("── 2. _safe_write_file gated behind approval ──")

if not CONSENT.exists():
    check("consent_store.py exists", False, str(CONSENT))
else:
    src = CONSENT.read_text(encoding="utf-8")
    # Find calls to _safe_write_file in the file
    calls = []
    for match in re.finditer(r"(?<!def )_safe_write_file\s*\(", src):
        # Skip the definition line — we want calls, not the def.
        line_start = src.rfind("\n", 0, match.start()) + 1
        line_prefix = src[line_start : match.start()]
        if "def " in line_prefix:
            continue
        line_no = src[: match.start()].count("\n") + 1
        calls.append(line_no)

    # Find the span of approve_pending_action
    apm = re.search(
        r"def approve_pending_action\([^)]*\)[^:]*:(.*?)(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    if not apm:
        check("approve_pending_action found", False, "function not located")
    else:
        start_line = src[: apm.start()].count("\n") + 1
        end_line = src[: apm.end()].count("\n") + 1
        outside = [ln for ln in calls if not (start_line <= ln <= end_line)]
        check(
            "_safe_write_file only called inside approve_pending_action",
            len(outside) == 0,
            f"calls outside approval at lines: {outside}" if outside else "",
        )
        note(f"_safe_write_file calls total: {len(calls)}")

    # Also: check no other file in routers/ imports or calls _safe_write_file
    other_callers = []
    for py in ROUTERS.glob("*.py"):
        if py.name == "consent_store.py":
            continue
        body = py.read_text(encoding="utf-8")
        if "_safe_write_file" in body:
            other_callers.append(py.name)
    check(
        "_safe_write_file not referenced from other routers",
        len(other_callers) == 0,
        ", ".join(other_callers) if other_callers else "",
    )


# ─── 3. ALLOWED_WRITE_ROOTS covers all three repos ──────────────

print("")
print("── 3. ALLOWED_WRITE_ROOTS covers all three repos ──")

if CONSENT.exists():
    src = CONSENT.read_text(encoding="utf-8")
    m = re.search(
        r"ALLOWED_WRITE_ROOTS\s*=\s*\[(.*?)\]",
        src,
        re.DOTALL,
    )
    if not m:
        check("ALLOWED_WRITE_ROOTS is declared", False)
    else:
        block = m.group(1)
        for repo in ["bosly-1.0", "bosly-keep", "bosly-gov"]:
            check(
                f"ALLOWED_WRITE_ROOTS includes {repo}",
                repo in block,
                "missing — Gov cannot write here, or the omission is unintended",
            )

        # Duplicate detection
        entries = re.findall(r'Path\([\'"]([^\'"]+)[\'"]\)', block)
        seen = set()
        dups = []
        for e in entries:
            if e in seen:
                dups.append(e)
            seen.add(e)
        check(
            "ALLOWED_WRITE_ROOTS has no duplicate entries",
            len(dups) == 0,
            f"duplicates: {dups}" if dups else "",
        )


# ─── 4. DENY_PATH_PATTERNS covers the standard set ─────────────

print("")
print("── 4. DENY_PATH_PATTERNS covers the standard sensitive set ──")

if CONSENT.exists():
    src = CONSENT.read_text(encoding="utf-8")
    m = re.search(
        r"DENY_PATH_PATTERNS\s*=\s*\[(.*?)\]",
        src,
        re.DOTALL,
    )
    if not m:
        check("DENY_PATH_PATTERNS is declared", False)
    else:
        block = m.group(1)
        # Each pattern is a regex. We look for the tokens in the block.
        required = [
            ("env", ".env"),
            ("id_rsa", "id_rsa"),
            ("authorized_keys", "authorized_keys"),
            ("shadow", "shadow"),
            ("passwd", "passwd"),
            ("pem", ".pem certificates/keys"),
            ("ssh", ".ssh directory"),
            ("credentials", "credentials files"),
            ("npmrc", ".npmrc (registry token)"),
            ("pypirc", ".pypirc (registry token)"),
        ]
        for token, label in required:
            check(
                f"DENY_PATH_PATTERNS covers {label}",
                token in block,
                f"no pattern matching '{token}'",
            )


# ─── Summary ───────────────────────────────────────────────────

print("")
print(f"{passed} passed, {failed} failed")
print("")
sys.exit(failed > 0)
