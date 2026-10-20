#!/usr/bin/env python3
"""ch_enrich.py — enrich OSM business rows with Companies House data.

WHAT THIS DOES. Given a business name and a town (from the lead
scout's OSM rows), it searches Companies House for matching
companies, picks the most likely one, and returns:
    - company number
    - company name (as registered)
    - status (active / dissolved / ...)
    - incorporation date
    - SIC codes
    - directors (first few)
    - a match confidence: high / medium / low

WHY CONFIDENCE MATTERS. OSM names are informal ("A Cut Above") and
Companies House names are legal ("A CUT ABOVE (NEWCASTLE) LTD").
A wrong match enriches the wrong business, and a wrong email goes
to a stranger. So a low-confidence match is recorded as low, not
silently used. The Executive (or the founder) decides whether to
act on it.

THE MATCHER:
    1. Search Companies House by the OSM name, restricted to
       active companies, limited to 5 results.
    2. Score each result:
         +3 if the normalised names are identical
         +2 if one contains the other
         +1 if the location word appears in the address
         +1 if the company's SIC looks like a business (not dormant)
         -5 if status is not 'active'
    3. Pick the highest score. High if >= 4, medium if >= 2, else low.
    4. If nothing scores above 0, return no match.

LEGAL: Companies House API, free, 600 requests per 5 minutes.
The key is in .env.production. The script sleeps between requests
when used in bulk (see enrich_rows).

USAGE:
    python3 scripts/ch_enrich.py --name "A Cut Above" --town "Newcastle upon Tyne"
    python3 scripts/ch_enrich.py --csv-in lead-scout.csv --csv-out enriched.csv

SELF-TEST:
    python3 scripts/ch_enrich.py --selftest
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ENV_FILE = Path("/home/bosly_accord/bosly-1.0/.env.production")
API_BASE = "https://api.company-information.service.gov.uk"
USER_AGENT = "bosly-lead-scout/0.1 (contact: jr-arnott@outlook.com)"
HTTP_TIMEOUT = 20
SLEEP_BETWEEN = 0.25  # ~4 req/s; well under the 600/5min limit


def _load_key() -> str:
    if not ENV_FILE.exists():
        raise SystemExit(f"env file not found: {ENV_FILE}")
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("COMPANIES_HOUSE_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if not key:
                raise SystemExit("COMPANIES_HOUSE_API_KEY is empty")
            return key
    raise SystemExit("COMPANIES_HOUSE_API_KEY not found in .env.production")


def _get(path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    key = _load_key()
    auth = base64.b64encode((key + ":").encode()).decode()
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": "Basic " + auth,
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:200]
        except Exception:
            pass
        raise RuntimeError(f"Companies House HTTP {e.code}: {body}") from None
    except Exception as e:
        raise RuntimeError(f"Companies House request failed: {e}") from None


def _norm(s: str) -> str:
    """Lowercase, strip punctuation, collapse spaces."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def search_companies(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search Companies House by name. Returns the raw items."""
    d = _get("/search/companies", {"q": name, "items_per_page": str(limit)})
    return d.get("items") or []


def get_company(company_number: str) -> Dict[str, Any]:
    return _get("/company/" + urllib.parse.quote(company_number))


def get_officers(company_number: str, limit: int = 5) -> List[Dict[str, Any]]:
    d = _get("/company/" + urllib.parse.quote(company_number) + "/officers",
             {"items_per_page": str(limit)})
    return d.get("items") or []


def score_match(osm_name: str, town: str, item: Dict[str, Any]) -> int:
    """Score how likely this search result is the right company."""
    score = 0
    ch_name = item.get("title") or ""
    n_osm = _norm(osm_name)
    n_ch = _norm(ch_name)

    if n_osm and n_osm == n_ch:
        score += 3
    elif n_osm and (n_osm in n_ch or n_ch in n_osm):
        score += 2

    if town:
        n_town = _norm(town)
        snippet = item.get("address_snippet") or ""
        addr_obj = item.get("address") or {}
        if isinstance(addr_obj, dict):
            addr_flat = " ".join(str(v) for v in addr_obj.values() if v)
        else:
            addr_flat = str(addr_obj)
        addr = _norm(str(snippet) + " " + addr_flat)
        if n_town and n_town in addr:
            score += 1

    status = (item.get("company_status") or "").lower()
    if status == "active":
        score += 1
    else:
        score -= 5

    # SIC: a real trading company has at least one SIC code
    sic = item.get("sic_codes") or []
    if sic:
        score += 1

    return score


def enrich_one(name: str, town: str = "") -> Dict[str, Any]:
    """Enrich one business. Returns a dict with match fields and confidence.

    Never raises for 'no match'; returns a record with match_confidence
    'none' and the reason. Raises only on transport errors, which the
    caller may want to know about.
    """
    out: Dict[str, Any] = {
        "osm_name": name,
        "town": town,
        "ch_number": "",
        "ch_name": "",
        "ch_status": "",
        "ch_incorporated": "",
        "ch_sic": "",
        "ch_directors": "",
        "match_confidence": "none",
        "match_score": 0,
    }

    items = search_companies(name, limit=5)
    if not items:
        return out

    scored = [(score_match(name, town, it), it) for it in items]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    if best_score <= 0:
        return out

    number = best.get("company_number") or ""
    if not number:
        return out

    # Fetch the full company record for status, incorporation, SIC
    try:
        company = get_company(number)
    except RuntimeError:
        company = {}

    out["ch_number"] = number
    out["ch_name"] = company.get("company_name") or best.get("title") or ""
    out["ch_status"] = company.get("company_status") or best.get("company_status") or ""
    out["ch_incorporated"] = company.get("date_of_creation") or ""
    # Age in months, for the "too new to be a prospect" filter
    inc = out["ch_incorporated"]
    age_months = ""
    if inc:
        try:
            from datetime import date
            y, m, d = inc.split("-")
            created = date(int(y), int(m), int(d))
            today = date.today()
            age_months = str((today.year - created.year) * 12 + (today.month - created.month))
        except Exception:
            age_months = ""
    out["ch_age_months"] = age_months
    sics = company.get("sic_codes") or best.get("sic_codes") or []
    out["ch_sic"] = "; ".join(sics) if isinstance(sics, list) else str(sics)

    # Directors
    try:
        officers = get_officers(number, limit=5)
        names = [o.get("name", "") for o in officers if o.get("name")]
        out["ch_directors"] = "; ".join(names)
    except RuntimeError:
        pass

    # Confidence: a name match is corroborated by ANY of three signals
    # — the town in the address, a real trading age, a sector SIC.
    # Requiring all three is too strict: OSM rarely carries a town, and
    # the CH search snippet rarely carries a locality.
    town_match = False
    addr_obj = best.get("address") or {}
    if isinstance(addr_obj, dict):
        addr_flat = " ".join(str(v) for v in addr_obj.values() if v)
    else:
        addr_flat = str(addr_obj)
    addr_flat = (best.get("address_snippet") or "") + " " + addr_flat
    if town and _norm(town) in _norm(addr_flat):
        town_match = True

    age_ok = False
    try:
        if out.get("ch_age_months"):
            age_ok = int(out["ch_age_months"]) >= 12
    except Exception:
        age_ok = False

    # SIC 96020 = hairdressing; 96xxx = personal services.
    sic_str = out.get("ch_sic") or ""
    sic_ok = bool(sic_str) and any(s.startswith(("96", "47", "43", "86", "75"))
                                    for s in [x.strip() for x in sic_str.split(";")] if s)

    corroborating = sum([town_match, age_ok, sic_ok])

    if best_score >= 4 and corroborating >= 1:
        out["match_confidence"] = "high"
    elif best_score >= 2 and corroborating >= 1:
        out["match_confidence"] = "medium"
    else:
        out["match_confidence"] = "low"
    out["match_score"] = best_score
    out["match_town"] = "yes" if town_match else "no"
    out["match_age_ok"] = "yes" if age_ok else "no"
    out["match_sic_ok"] = "yes" if sic_ok else "no"
    return out


def enrich_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Enrich a list of lead-scout rows. Adds the CH columns to each."""
    out: List[Dict[str, str]] = []
    for i, row in enumerate(rows):
        name = row.get("name", "")
        town = row.get("city", "") or "Newcastle upon Tyne"
        try:
            ch = enrich_one(name, town)
        except RuntimeError as e:
            ch = {"match_confidence": "error", "match_error": str(e)[:200]}
        merged = dict(row)
        merged.update({k: str(v) for k, v in ch.items() if k not in ("osm_name", "town")})
        out.append(merged)
        if (i + 1) % 10 == 0:
            print(f"  enriched {i+1}/{len(rows)}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN)
    return out


# ---------------------------------------------------------------------------
# Self-test: the scorer, no network needed for the scoring parts
# ---------------------------------------------------------------------------

def _selftest() -> int:
    passed = 0
    failed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}")
            if detail:
                print("      " + detail)

    # _norm
    check("_norm lowercases", _norm("A CUT ABOVE") == "a cut above")
    check("_norm strips punctuation", _norm("A Cut Above (Newcastle) Ltd") == "a cut above newcastle ltd")
    check("_norm collapses spaces", _norm("A  Cut   Above") == "a cut above")

    # score_match — exact
    item_exact = {"title": "A CUT ABOVE", "company_status": "active",
                  "address_snippet": "Newcastle upon Tyne", "sic_codes": ["96020"]}
    check("exact + town + active + sic scores high",
          score_match("A Cut Above", "Newcastle upon Tyne", item_exact) >= 5,
          detail=f"got {score_match('A Cut Above', 'Newcastle upon Tyne', item_exact)}")

    # score_match — not active
    item_dissolved = {"title": "A CUT ABOVE", "company_status": "dissolved",
                      "address_snippet": "Newcastle", "sic_codes": []}
    check("dissolved scores low",
          score_match("A Cut Above", "Newcastle", item_dissolved) < 2,
          detail=f"got {score_match('A Cut Above', 'Newcastle', item_dissolved)}")

    # score_match — wrong business
    item_wrong = {"title": "SOMETHING ELSE ENTIRELY", "company_status": "active",
                  "address_snippet": "London", "sic_codes": ["12345"]}
    check("wrong name + wrong town scores low",
          score_match("A Cut Above", "Newcastle", item_wrong) < 3,
          detail=f"got {score_match('A Cut Above', 'Newcastle', item_wrong)}")

    # no match returns 'none' — mock the search so it's deterministic
    _real_search = globals()["search_companies"]
    globals()["search_companies"] = lambda name, limit=5: []
    try:
        r = enrich_one("A Cut Above", "Newcastle")
    finally:
        globals()["search_companies"] = _real_search
    check("no match returns none", r["match_confidence"] == "none",
          detail=f"got {r.get('match_confidence')!r}")

    # low score is not used: mock a search that returns only a dissolved
    # unrelated company
    def _fake_search(name, limit=5):
        return [{"title": "COMPLETELY DIFFERENT LTD",
                 "company_status": "dissolved",
                 "address_snippet": "London",
                 "address": {"locality": "London"},
                 "sic_codes": [], "company_number": "00000000"}]
    globals()["search_companies"] = _fake_search
    try:
        r = enrich_one("A Cut Above", "Newcastle")
    finally:
        globals()["search_companies"] = _real_search
    check("dissolved unrelated scores none",
          r["match_confidence"] == "none",
          detail=f"got {r.get('match_confidence')!r} score {r.get('match_score')}")

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="a business name to enrich")
    ap.add_argument("--town", default="", help="the town, for matching")
    ap.add_argument("--csv-in", help="a lead-scout CSV to enrich")
    ap.add_argument("--csv-out", help="where to write the enriched CSV")
    ap.add_argument("--limit", type=int, default=10,
                    help="enrich only the first N rows (default 10)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if args.name:
        r = enrich_one(args.name, args.town)
        print(json.dumps(r, indent=2))
        return 0

    if args.csv_in:
        out_path = Path(args.csv_out or args.csv_in.replace(".csv", "-enriched.csv"))
        with open(args.csv_in, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        rows = rows[:args.limit]
        print(f"enriching {len(rows)} rows...", file=sys.stderr)
        enriched = enrich_rows(rows)
        if enriched:
            # Union of all keys across all rows — a row may carry a field
            # (e.g. match_error) that the first row does not.
            fields = []
            seen = set()
            for r in enriched:
                for k in r.keys():
                    if k not in seen:
                        seen.add(k)
                        fields.append(k)
            with out_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for r in enriched:
                    w.writerow(r)
        print(f"written: {out_path}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
