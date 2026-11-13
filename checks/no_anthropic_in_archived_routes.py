#!/usr/bin/env python3
"""
gov.no_anthropic_in_archived_routes

No route under an archived feature may call an external AI provider.
ARCHIVED is a list of app/ paths. Adding to it is a decision;
removing from it means the feature is coming back on purpose.
"""
import os, re, sys
from pathlib import Path

ACCORD = Path(os.environ.get("ACCORD_ROOT", "/home/bosly_accord/bosly-1.0"))
ARCHIVED = ["app/api/social"]
PATTERNS = [r"api\.anthropic\.com", r"CLAUDE_API_KEY", r"ANTHROPIC_API_KEY", r"@anthropic-ai/sdk"]

hits = []
for rel in ARCHIVED:
    root = ACCORD / rel
    if not root.exists():
        continue
    for p in root.rglob("*.ts"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in PATTERNS:
            if re.search(pat, text):
                hits.append(f"{p.relative_to(ACCORD)}: matches {pat}")

if hits:
    print("FAIL gov.no_anthropic_in_archived_routes")
    for h in hits: print("  " + h)
    sys.exit(1)
print("PASS gov.no_anthropic_in_archived_routes")
