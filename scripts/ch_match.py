"""scripts/ch_match.py — match a business name to Companies House.

The scout finds businesses; this says which are companies. A match is
proof of corporate status (PECR: cold email is lawful to a corporate
subscriber); no match is evidence of not-corporate (a sole trader is an
individual subscriber and needs consent). The confidence is recorded,
not dropped, so the ranker decides what to trust.

Auth: HTTP Basic, the API key as the username, empty password.
Rate: 600 requests / 5 minutes. Cached by name in a JSON file so a
re-run does not burn the quota.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path("/mnt/bosly/bosly-data/.data/governor/ch-match-cache.json")
API = "https://api.company-information.service.gov.uk/search/companies"


def _key() -> str:
    k = (os.environ.get("COMPANIES_HOUSE_API_KEY") or "").strip()
    if not k:
        # Fall back to Accord's env file, the same way the tests do.
        try:
            for line in open("/home/bosly_accord/bosly-1.0/.env.production", encoding="utf-8"):
                if line.startswith("COMPANIES_HOUSE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
    return ""


def _normalise(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"\b(ltd|limited|plc|llp|the)\b", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(d: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def match(name: str, postcode: str = "") -> dict:
    """Return {ch_name, ch_number, ch_status, ch_incorporated,
    match_confidence} or {} if no plausible match.

    Confidence: high = exact normalised name; medium = the query is
    contained in the returned name (or vice versa); low = a fuzzy hit.
    A low match is recorded, not trusted.
    """
    q = _normalise(name)
    if not q:
        return {}
    cache = _load_cache()
    key = q + "|" + (postcode or "").upper()
    if key in cache:
        return cache[key]

    k = _key()
    if not k:
        return {}

    url = API + "?" + urllib.parse.urlencode({"q": name, "items_per_page": 5})
    auth = base64.b64encode((k + ":").encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read().decode())
    except Exception:
        cache[key] = {}
        _save_cache(cache)
        return {}

    items = (body.get("items") or [])[:5]
    best = None
    for it in items:
        title = it.get("title") or ""
        n = _normalise(title)
        conf = ""
        if n == q:
            conf = "high"
        elif q in n or n in q:
            conf = "medium"
        else:
            # A shared significant word is a fuzzy hit.
            qw = set(q.split())
            nw = set(n.split())
            if qw & nw - {"and", "of", "the"}:
                conf = "low"
        if not conf:
            continue
        # The postcode strengthens a medium match if the address matches.
        addr = (it.get("address") or {})
        pc = (addr.get("postal_code") or "").replace(" ", "").upper()
        wanted = (postcode or "").replace(" ", "").upper()
        if conf == "medium" and wanted and pc.startswith(wanted[:4]):
            conf = "high"
        status = (it.get("company_status") or "").lower()
        # A dissolved company is not a client. Demote it: it is a name
        # match, not a live business.
        if status in ("dissolved", "liquidation", "administration", "receivership"):
            conf = "low"
        if best is None or {"high": 3, "medium": 2, "low": 1}[conf] > {"high": 3, "medium": 2, "low": 1}[best["match_confidence"]]:
            best = {
                "ch_name": title,
                "ch_number": it.get("company_number", ""),
                "ch_status": it.get("company_status", ""),
                "ch_incorporated": it.get("date_of_creation", ""),
                "match_confidence": conf,
            }
    cache[key] = best or {}
    _save_cache(cache)
    # Be gentle: the API allows 600 per 5 minutes.
    time.sleep(0.15)
    return best or {}
