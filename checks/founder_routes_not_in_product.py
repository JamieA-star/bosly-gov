#!/usr/bin/env python3
"""
gov.accord_founder_routes_not_in_product

Nothing in the product bundle names /api/founder/. The founder's
routes are gated on isFounder on the server, and this is the second
barrier: a customer's component does not contain the URL, so it
cannot call it even if the gate were wrong.

ChatDrawer is the one exception until it is split into FounderChat
and ProductChat — it holds both paths in one file today. When the
split lands, remove ChatDrawer from ALLOWED and this check becomes
the proof that the product chat cannot reach the butler.

Found 14 Nov: ChatDrawer called /api/executive/proxy for every user
and relied on hasProduct — a row a grant can set — to refuse.
"""
import os
import sys
from pathlib import Path

ACCORD = Path(os.environ.get("ACCORD_ROOT", "/home/bosly_accord/bosly-1.0"))

ALLOWED = {
    "components/chat/ChatDrawer.tsx",  # until the FounderChat/ProductChat split
}
SKIP_PREFIX = "app/api/founder/"  # the routes themselves

hits = []
for base in (ACCORD / "app", ACCORD / "components"):
    if not base.exists():
        continue
    for p in base.rglob("*.ts*"):
        rel = str(p.relative_to(ACCORD))
        if rel.startswith(SKIP_PREFIX) or rel in ALLOWED:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "/api/founder/" in text:
            hits.append(rel)

if hits:
    print("FAIL gov.accord_founder_routes_not_in_product")
    for h in hits:
        print(f"  {h} names /api/founder/")
    print("  The product bundle must not know the butler's door.")
    sys.exit(1)

print("PASS gov.accord_founder_routes_not_in_product")
print(f"  allowed: {', '.join(sorted(ALLOWED))}")
