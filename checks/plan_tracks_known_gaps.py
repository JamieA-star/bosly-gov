#!/usr/bin/env python3
"""
Check: code comments that admit a known gap must be tracked.

Any source comment containing an admission phrase ("this is
broken", "known bug", "doesn't work", "known limitation",
"won't work", "broken since", "known issue") must be either:

  (a) mentioned in bosly-gov/PLAN.md (by file path, bare
      filename, or module name), or
  (b) mentioned in the memory store, or
  (c) in the allowlist below.

If none of those is true, the comment is an acknowledgment
that isn't tracked. It fails.

Only comment syntax is scanned — lines starting with //, /*,
or JSDoc * lines. String literals (including email body
templates) are ignored. This was a calibration lesson from
the first draft: mailer.ts embeds the phrase "This part is
broken." inside an email body as an example of user feedback.

Motivated by VaultProvider.tsx:94 which (at the time)
acknowledged bug #3 in a comment and was never tracked as a
plan item or memory. See gov.plan_tracks_known_gaps in
PLAN.md.

Exit 0 if every admission is tracked, 1 otherwise.

Run:
    python3 checks/plan_tracks_known_gaps.py
    python3 checks/plan_tracks_known_gaps.py --dry-run
    python3 checks/plan_tracks_known_gaps.py --verbose
"""

import json
import re
import sys
from pathlib import Path

ACCORD_ROOT = Path("/home/bosly_accord/bosly-1.0")
PLAN_PATH = Path("/home/bosly_accord/bosly-gov/PLAN.md")
MEMORY_PATH = Path(
    "/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/memory.json"
)

SCAN_DIRS = ["lib", "app", "components"]
SKIP_DIRS = {"node_modules", ".next", "tests", "scripts", "legacy",
             "__tests__", "backups"}
SCAN_EXTS = {".ts", ".tsx"}

# Admission phrases. Deliberately NOT including 'stub' —
# gov.stub_detection owns that class. This check owns
# broken-and-known.
ADMISSION_PATTERNS = [
    re.compile(r"\bthis\s+is\s+broken\b", re.IGNORECASE),
    re.compile(r"\bis\s+broken\b", re.IGNORECASE),
    re.compile(r"\bbroken\s+since\b", re.IGNORECASE),
    re.compile(r"\bknown\s+bug\b", re.IGNORECASE),
    re.compile(r"\bknown\s+issue\b", re.IGNORECASE),
    re.compile(r"\bknown\s+limitation\b", re.IGNORECASE),
    re.compile(r"\bdoesn't\s+work\b", re.IGNORECASE),
    re.compile(r"\bdoes\s+not\s+work\b", re.IGNORECASE),
    re.compile(r"\bwon't\s+work\b", re.IGNORECASE),
    re.compile(r"\bwill\s+not\s+work\b", re.IGNORECASE),
]

# Known-and-accepted admissions. (file, line, pattern_substring).
ALLOWLIST = [
    # lib/social/render.ts:27 — the render pipeline is known
    # broken; the placeholder renderer exists to keep builds
    # green. Tracked as accord.social_render_pipeline in
    # PLAN.md.
    ("lib/social/render.ts", 27, "broken"),
]


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def walk_ts(root: Path) -> list[Path]:
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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ACCORD_ROOT))
    except ValueError:
        return str(path)


def is_comment_line(line: str) -> bool:
    """Only scan lines that are comment syntax."""
    s = line.lstrip()
    return (
        s.startswith("//")
        or s.startswith("/*")
        or s.startswith("*")
    )


def identifier_tokens(rel_path: str) -> list[str]:
    """
    Tokens to search for in PLAN.md and memory.json. Order is
    most-specific first. If ANY token matches, the admission
    is considered tracked.
    """
    p = Path(rel_path)
    tokens: list[str] = []
    # Full relative path
    tokens.append(rel_path)
    # Bare filename with extension
    tokens.append(p.name)
    # Filename without extension
    tokens.append(p.stem)
    # Immediate parent + stem (e.g. 'social/render')
    if p.parent.name:
        tokens.append(f"{p.parent.name}/{p.stem}")
    # Dedup preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def is_tracked_in(rel_path: str, haystack: str) -> str | None:
    """Returns the matching token if tracked, else None."""
    for token in identifier_tokens(rel_path):
        # Word-boundary-ish match; accept substring for paths
        if token in haystack:
            return token
    return None


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    plan_text = read(PLAN_PATH)
    try:
        memory_items = json.loads(read(MEMORY_PATH) or "[]")
        memory_text = json.dumps(memory_items, ensure_ascii=False)
    except Exception:
        memory_text = ""

    findings: list[dict] = []
    allowlist_hits: list[dict] = []
    tracked_hits: list[dict] = []

    for path in walk_ts(ACCORD_ROOT):
        rel_path = rel(path)
        text = read(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not is_comment_line(line):
                continue
            for pat in ADMISSION_PATTERNS:
                m = pat.search(line)
                if not m:
                    continue
                matched_phrase = m.group(0)
                entry = {
                    "file": rel_path,
                    "line": line_no,
                    "phrase": matched_phrase,
                    "text": line.strip()[:160],
                }

                # 1. allowlist?
                for af, al, apat in ALLOWLIST:
                    if (af == rel_path
                            and al == line_no
                            and apat.lower() in matched_phrase.lower()):
                        allowlist_hits.append(entry)
                        break
                else:
                    # 2. tracked in PLAN or memory?
                    token = (is_tracked_in(rel_path, plan_text)
                             or is_tracked_in(rel_path, memory_text))
                    if token:
                        entry["tracked_by"] = token
                        tracked_hits.append(entry)
                    else:
                        findings.append(entry)
                break  # one phrase per comment

    print("")
    print("Invariant: plan tracks known gaps")
    print("----------------------------------------------------")
    print(f"scanned:          {len(walk_ts(ACCORD_ROOT))} ts/tsx files")
    print(f"admissions:       "
          f"{len(findings) + len(allowlist_hits) + len(tracked_hits)}")
    print(f"  tracked (PLAN or memory): {len(tracked_hits)}")
    print(f"  allowlisted:               {len(allowlist_hits)}")
    print(f"  untracked:                 {len(findings)}")
    print("")

    if verbose and tracked_hits:
        print("Tracked admissions:")
        for e in tracked_hits:
            print(f"  OK  {e['file']}:{e['line']}  "
                  f"[{e['phrase']}] tracked by '{e['tracked_by']}'")
        print("")

    if verbose and allowlist_hits:
        print("Allowlisted admissions:")
        for e in allowlist_hits:
            print(f"  OK  {e['file']}:{e['line']}  "
                  f"[{e['phrase']}]")
        print("")

    if not findings:
        print("PASS: every code admission is tracked in PLAN or memory")
        print("")
        print("SUMMARY: 0 findings")
        print("")
        return 0

    if dry_run:
        print("── DRY RUN — untracked admissions ──")
        for e in findings:
            print(f"  {e['file']}:{e['line']}  [{e['phrase']}]")
            print(f"      {e['text']}")
        print("")
        print(f"SUMMARY: {len(findings)} untracked (dry-run, exit 0)")
        print("")
        return 0

    print("── Untracked admissions (FAIL) ──")
    for e in findings:
        print(f"FAIL: {e['file']}:{e['line']}  [{e['phrase']}]")
        print(f"      {e['text']}")
        print(f"      Not found in PLAN.md or memory. Add a plan item "
              f"or a memory entry, or allowlist this line.")
        print("")
    print(f"SUMMARY: {len(findings)} findings")
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
