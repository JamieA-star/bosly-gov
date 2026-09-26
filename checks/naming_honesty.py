#!/usr/bin/env python3
"""
Check: names that assert a crypto primitive the code doesn't use.

Three rules:

  RULE A — Prisma schema fields matching /^encrypted[A-Z]/ whose
    name mentions a specific crypto primitive (X25519, RSA,
    ECDH, ChaCha). Fail if the same primitive is not imported
    anywhere in lib/crypto/.

  RULE B — Any source comment or JSDoc containing an admission
    phrase ('was a lie', 'is a lie', 'actually stores',
    'actually holds', 'misnamed', 'despite the name',
    'not actually'). These are documentation of past naming
    drift. The known, historical ones are in ALLOWLIST. A new
    one means someone just wrote a misnamed field and admitted
    it — that fails.

  RULE C — Any interface field ending in X25519, RSA, ECDH, or
    ChaCha where the same file contains no reference to that
    primitive. Catches the pattern at the file level, not the
    codebase level. Less precise than RULE A, but covers
    types outside the Prisma schema.

Motivated by the 2026-09-21 rename: encryptedX25519PrivateKey
held the plaintext BIP39 recovery phrase (or a legacy hex
entropy blob). X25519 was not used anywhere in the runtime.
Field renamed to recoveryPhrase. See
incident-20260921-crypto-recovery-broken and
pattern-20260924-accord-vs-code-drift.

Exit 0 if no new findings, 1 otherwise.

Run:
    python3 checks/naming_honesty.py
    python3 checks/naming_honesty.py --dry-run
    python3 checks/naming_honesty.py --verbose
"""

import re
import sys
from pathlib import Path

ACCORD_ROOT = Path("/home/bosly_accord/bosly-1.0")
SCHEMA_PATH = ACCORD_ROOT / "prisma" / "schema.prisma"
CRYPTO_DIR = ACCORD_ROOT / "lib" / "crypto"

SCAN_DIRS = ["lib", "app"]
SKIP_DIRS = {"node_modules", ".next", "tests", "scripts", "legacy",
             "__tests__", "backups"}

# Primitives this check knows about. A name mentioning one of
# these, without the primitive appearing in the code, is drift.
PRIMITIVES = ["X25519", "RSA", "ECDH", "ChaCha"]

# RULE B — admission phrases. Any source comment containing one
# of these is documentation of past naming drift.
ADMISSION_PATTERNS = [
    re.compile(r"\bwas\s+a\s+lie\b", re.IGNORECASE),
    re.compile(r"\bis\s+a\s+lie\b", re.IGNORECASE),
    re.compile(r"\bactually\s+stores\b", re.IGNORECASE),
    re.compile(r"\bactually\s+holds\b", re.IGNORECASE),
    re.compile(r"\bmisnamed\b", re.IGNORECASE),
    re.compile(r"\bdespite\s+the\s+name\b", re.IGNORECASE),
    re.compile(r"\bnot\s+actually\b", re.IGNORECASE),
]

# Known, historical admissions. A new admission means new drift.
# (path, line_number) — must match exactly. If the file is edited
# and the comment moves, the check will report it. That's correct:
# the allowlist is line-specific on purpose.
ALLOWLIST_COMMENTS = [
    ("lib/crypto/types.ts", 5),   # 'actually stores the plaintext BIP39'
    ("lib/crypto/types.ts", 7),   # 'The name was a lie'
]

# RULE A — encrypted-prefixed fields that name a primitive
ENCRYPTED_FIELD_RE = re.compile(r"^\s*(encrypted[A-Z]\w+)\s")
FIELD_PRIMITIVE_HINT_RE = re.compile(
    r"(" + "|".join(PRIMITIVES) + r")",
    re.IGNORECASE,
)

# RULE C — interface fields ending in a primitive name
INTERFACE_FIELD_RE = re.compile(r"^\s*(\w+)[" + "".join(
    ["?"] ) + r"]?\s*[:?]\s*\w", re.MULTILINE)


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
            if p.suffix not in {".ts", ".tsx"}:
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


def primitive_used_in_crypto(primitive: str) -> bool:
    """RULE A helper: is this primitive referenced anywhere in lib/crypto/?"""
    if not CRYPTO_DIR.exists():
        return False
    pat = re.compile(primitive, re.IGNORECASE)
    for p in CRYPTO_DIR.rglob("*"):
        if p.is_dir() or p.suffix not in {".ts", ".tsx"}:
            continue
        if pat.search(read(p)):
            return True
    return False


def rule_a() -> list[dict]:
    """RULE A — Prisma encrypted-prefixed fields naming an unused primitive."""
    findings: list[dict] = []
    if not SCHEMA_PATH.exists():
        return findings
    schema = read(SCHEMA_PATH)
    for line_no, line in enumerate(schema.splitlines(), start=1):
        m = ENCRYPTED_FIELD_RE.match(line)
        if not m:
            continue
        field_name = m.group(1)
        pm = FIELD_PRIMITIVE_HINT_RE.search(field_name)
        if not pm:
            continue
        primitive = pm.group(1)
        if primitive_used_in_crypto(primitive):
            continue
        findings.append({
            "rule": "A",
            "file": "prisma/schema.prisma",
            "line": line_no,
            "name": field_name,
            "primitive": primitive,
            "detail": f"field '{field_name}' names {primitive} but {primitive} is not used in lib/crypto/",
        })
    return findings


def rule_b(verbose: bool) -> tuple[list[dict], list[dict]]:
    """
    RULE B — source comments admitting past naming drift.
    Returns (new_findings, allowlist_hits).
    """
    new_findings: list[dict] = []
    allowlist_hits: list[dict] = []
    for path in walk_ts(ACCORD_ROOT):
        rel_path = rel(path)
        text = read(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            # Only scan comment-ish lines to keep this focused
            stripped = line.lstrip()
            if not (stripped.startswith("//")
                    or stripped.startswith("*")
                    or stripped.startswith("/*")):
                continue
            for pat in ADMISSION_PATTERNS:
                if pat.search(line):
                    entry = {
                        "rule": "B",
                        "file": rel_path,
                        "line": line_no,
                        "phrase": pat.pattern,
                        "text": line.strip()[:140],
                    }
                    if (rel_path, line_no) in ALLOWLIST_COMMENTS:
                        allowlist_hits.append(entry)
                    else:
                        new_findings.append(entry)
                    break
    return new_findings, allowlist_hits


def rule_c(verbose: bool) -> list[dict]:
    """
    RULE C — interface field ending in a primitive name, with no
    reference to that primitive in the same file.
    """
    findings: list[dict] = []
    field_re = re.compile(
        r"^\s*(\w+)\??\s*:\s*[^;]+;",
        re.MULTILINE,
    )
    for path in walk_ts(ACCORD_ROOT):
        text = read(path)
        # Skip files that are obviously not types
        if "interface " not in text and "type " not in text:
            continue
        rel_path = rel(path)
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            # Skip comment lines
            s = line.lstrip()
            if s.startswith("//") or s.startswith("*"):
                continue
            m = field_re.match(line)
            if not m:
                continue
            fname = m.group(1)
            for prim in PRIMITIVES:
                if prim.lower() not in fname.lower():
                    continue
                # Field names a primitive. Is that primitive
                # referenced elsewhere in the file?
                if re.search(prim, text, re.IGNORECASE):
                    # Count occurrences: field itself doesn't count
                    occurrences = len(re.findall(prim, text, re.IGNORECASE))
                    if occurrences <= 1:
                        findings.append({
                            "rule": "C",
                            "file": rel_path,
                            "line": i,
                            "name": fname,
                            "primitive": prim,
                            "detail": f"field '{fname}' names {prim} but {prim} is not referenced elsewhere in the file",
                        })
                else:
                    findings.append({
                        "rule": "C",
                        "file": rel_path,
                        "line": i,
                        "name": fname,
                        "primitive": prim,
                        "detail": f"field '{fname}' names {prim} but the file contains no reference to {prim}",
                    })
                break
    return findings


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    a_findings = rule_a()
    b_new, b_hits = rule_b(verbose)
    c_findings = rule_c(verbose)

    all_findings = a_findings + b_new + c_findings

    print("")
    print("Invariant: naming honesty")
    print("----------------------------------------------------")
    print(f"scanned:          {len(walk_ts(ACCORD_ROOT))} ts/tsx files")
    print(f"rule A findings:  {len(a_findings)}")
    print(f"rule B findings:  {len(b_new)}  (allowlist hits: {len(b_hits)})")
    print(f"rule C findings:  {len(c_findings)}")
    print(f"allowlist size:   {len(ALLOWLIST_COMMENTS)}")
    print("")

    if verbose and b_hits:
        print("Allowlisted admissions (known, historical):")
        for e in b_hits:
            print(f"  OK  {e['file']}:{e['line']}  {e['text']}")
        print("")

    if not all_findings:
        print("PASS: no naming drift found")
        print("")
        print("SUMMARY: 0 findings")
        print("")
        return 0

    if dry_run:
        print("── DRY RUN — findings that would be flagged ──")
        for e in all_findings:
            print(
                f"  [{e['rule']}] {e['file']}:{e['line']}  {e.get('name', '')}  "
                f"{e.get('detail', e.get('text', ''))}"
            )
        print("")
        print(f"SUMMARY: {len(all_findings)} findings (dry-run, exit 0)")
        print("")
        return 0

    for e in all_findings:
        print(
            f"FAIL [{e['rule']}] {e['file']}:{e['line']}  "
            f"{e.get('name', '')}  {e.get('detail', e.get('text', ''))}"
        )
    print("")
    print(f"SUMMARY: {len(all_findings)} findings")
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
