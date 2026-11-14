#!/usr/bin/env python3
"""
gov.accord_route_uses_the_session

A route that reads the legacy bosly_uid cookie must also call
getSession. The legacy cookie is a fallback, never the only auth.

Found 14 Nov: app/api/auth/key-backup read bosly_uid alone and
returned 401 in a tab that was fully signed in — setSession writes
both cookies and bosly_uid can be absent while bosly_session is not.
The client read the 401 as "no backup" and offered the founder the
one prompt that overwrites the key it was meant to restore.

ARCHIVED is not needed: every route in app/api is in scope.
"""
import os
import re
import sys
from pathlib import Path

ACCORD = Path(os.environ.get("ACCORD_ROOT", "/home/bosly_accord/bosly-1.0"))
API = ACCORD / "app" / "api"

LEGACY = re.compile(r"cookies\.get\(\s*['\"]bosly_uid['\"]")
SESSION = re.compile(r"\bgetSession\s*\(")

hits = []
if API.exists():
    for p in API.rglob("*.ts"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if LEGACY.search(text) and not SESSION.search(text):
            hits.append(str(p.relative_to(ACCORD)))

if hits:
    print("FAIL gov.accord_route_uses_the_session")
    for h in hits:
        print(f"  {h} reads bosly_uid without getSession")
    sys.exit(1)

print("PASS gov.accord_route_uses_the_session")
