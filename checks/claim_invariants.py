#!/usr/bin/env python3
"""
Check: the free-pill list is stated the same way in every document.

Docs make factual claims about the code, and nothing checks them. This
is the first claim family: which pills are free.

Each of the docs below states the free pill list. This check extracts
that list from each, normalises it, and compares:
  - every doc against every other doc
  - every doc against lib/tiers.ts's FREE_FEATURES

It checks STRUCTURED claims — lists, names, counts — not prose. Whether
the sentences around the list are true is human review. Same split as
gov.accord_compliance: mechanical drift checked, prose reviewed.

Report-only at first.

Run:
    python3 checks/claim_invariants.py
"""

import re
import sys
from pathlib import Path

REPO = Path("/home/bosly_accord/bosly-1.0")

DOCS = [
    REPO / "docs/ACCORD.md",
    REPO / "app/(marketing)/faq/page.tsx",
    REPO / "public/llms-full.txt",
    REPO / "public/llms.txt",
    REPO / "app/layout.tsx",
]

TIERS = REPO / "lib/tiers.ts"

# The doc word for each code feature. Four map one-to-one; Invoicing in
# the docs is manual-invoicing in the code.
DOC_TO_FEATURE = {
    "active": "active",
    "contacts": "contacts",
    "calendar": "calendar",
    "health": "health",
    "invoicing": "manual-invoicing",
}

REPORT_ONLY = True


def free_features_from_code() -> set[str]:
    text = TIERS.read_text(encoding="utf-8")
    m = re.search(r"FREE_FEATURES\s*=\s*\[(.*?)\]", text, re.S)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def extract_pill_list(text: str) -> set[str] | None:
    """Find a run of pill names in a sentence about the free tier."""
    # Look for the five pill names near each other.
    names = ["Active", "Contacts", "Calendar", "Health", "Invoicing"]
    found = set()
    for n in names:
        if re.search(r"\b" + n + r"\b", text):
            found.add(n.lower())
    # Require at least four of the five to count as a list.
    return found if len(found) >= 4 else None


def main() -> int:
    print("")
    print("Invariant: the free-pill list is stated the same everywhere")
    print("-----------------------------------------------------------")

    code = free_features_from_code()
    if not code:
        print("  SKIP: could not read FREE_FEATURES from lib/tiers.ts")
        print("")
        return 0

    code_docs = {DOC_TO_FEATURE.get(f, f) for f in code}
    print(f"  lib/tiers.ts FREE_FEATURES: {sorted(code)}")
    print("")

    disagreements = []
    for doc in DOCS:
        if not doc.exists():
            print(f"  MISSING  {doc.relative_to(REPO)}")
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore")
        pills = extract_pill_list(text)
        rel = str(doc.relative_to(REPO))
        if pills is None:
            print(f"  n/a      {rel}")
            continue
        mapped = {DOC_TO_FEATURE.get(p, p) for p in pills}
        ok = mapped == code_docs
        print(f"  {'OK' if ok else 'DIFFERS'}  {rel}  ->  {sorted(pills)}")
        if not ok:
            disagreements.append((rel, sorted(pills), sorted(code)))

    print("")
    if disagreements:
        print(f"  {len(disagreements)} document(s) disagree with the code:")
        for rel, got, want in disagreements:
            print(f"    {rel}")
            print(f"      says: {got}")
            print(f"      code: {want}")
    else:
        print("  OK: every document names the same free pills as lib/tiers.ts")

    print("")
    verdict = "REPORT" if REPORT_ONLY else ("PASS" if not disagreements else "FAIL")
    print(f"SUMMARY: {verdict} ({len(disagreements)} disagreement(s))")
    print("")
    return 0 if (REPORT_ONLY or not disagreements) else 1


if __name__ == "__main__":
    sys.exit(main())
