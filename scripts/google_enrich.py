#!/usr/bin/env python3
"""google_enrich.py — add Google rating and review count to scout rows.

WHAT THIS DOES. For each business in a CSV, calls Google Places Text
Search once (name + county), takes the best match, and writes:
    google_rating    (e.g. 4.6)
    google_reviews   (e.g. 214)
    google_status    (OPERATIONAL / CLOSED_PERMANENTLY / ...)
    google_place_id  (for later Place Details, if ever needed)
    google_match     (high / medium / low / none)

WHY TEXT SEARCH ONLY. Text Search returns rating, review count, and
business status in one call at $32/1,000. Place Details is a second
call for fields OSM already has (phone, address). One call per
business keeps the cost at a fraction of the free tier.

COST. 250 rows a week = ~13,000 calls a year = ~$416/year, all inside
the $200/month free tier.

THE KEY. Read from GOOGLE_PLACES_API_KEY in
/home/bosly_accord/bosly-1.0/.env.production. If the key is missing,
this module SKIPS and returns the rows unchanged, with a clear note.
The scout still works without Google.

USAGE:
    python3 scripts/google_enrich.py --csv-in lead-scout.csv --csv-out enriched.csv
    python3 scripts/google_enrich.py --name "A Cut Above" --area "Newcastle upon Tyne"
    python3 scripts/google_enrich.py --selftest

SELF-TEST does not call Google: it tests the match scorer and the
skip-if-no-key path.
"""
from __future__ import annotations

import argparse
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
API_URL = "https://places.googleapis.com/v1/places:searchText"
HTTP_TIMEOUT = 20
SLEEP_BETWEEN = 0.15  # ~6 req/s; polite and well under Google's limits

# Only the fields we need. Requesting fewer fields is cheaper.
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
])


def _load_key() -> Optional[str]:
    """Return the Google key, or None if absent."""
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("GOOGLE_PLACES_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            return key or None
    return None


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def text_search(name: str, area: str, key: str) -> List[Dict[str, Any]]:
    """One Text Search call. Returns the list of places."""
    body = json.dumps({
        "textQuery": f"{name} {area}",
        "maxResultCount": 5,
        "languageCode": "en-GB",
        "regionCode": "GB",
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:300]
        except Exception:
            pass
        raise RuntimeError(f"Google HTTP {e.code}: {body}") from None
    except Exception as e:
        raise RuntimeError(f"Google request failed: {e}") from None
    return d.get("places") or []


def score_match(business_name: str, area: str, place: Dict[str, Any]) -> int:
    """Score how likely this Google place is the right business."""
    score = 0
    name = (place.get("displayName") or {}).get("text") or ""
    n_biz = _norm(business_name)
    n_g = _norm(name)

    if n_biz and n_biz == n_g:
        score += 3
    elif n_biz and (n_biz in n_g or n_g in n_biz):
        score += 2

    if area and _norm(area) in _norm(place.get("formattedAddress") or ""):
        score += 1

    if place.get("rating"):
        score += 1
    if (place.get("userRatingCount") or 0) >= 5:
        score += 1
    return score


def enrich_one(name: str, area: str, key: str) -> Dict[str, Any]:
    """Enrich one business. Returns Google fields (or 'none' if no match)."""
    out = {
        "google_rating": "",
        "google_reviews": "",
        "google_status": "",
        "google_place_id": "",
        "google_match": "none",
    }
    try:
        places = text_search(name, area, key)
    except RuntimeError as e:
        out["google_match"] = "error"
        out["google_error"] = str(e)[:200]
        return out

    if not places:
        return out

    scored = [(score_match(name, area, p), p) for p in places]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    if best_score <= 0:
        return out

    rating = best.get("rating")
    reviews = best.get("userRatingCount")
    status = best.get("businessStatus") or ""
    pid = best.get("id") or ""

    out["google_rating"] = str(rating) if rating is not None else ""
    out["google_reviews"] = str(reviews) if reviews is not None else ""
    out["google_status"] = str(status)
    out["google_place_id"] = str(pid)

    if best_score >= 5:
        out["google_match"] = "high"
    elif best_score >= 3:
        out["google_match"] = "medium"
    else:
        out["google_match"] = "low"
    return out


def enrich_rows(rows: List[Dict[str, str]], area: str, key: str) -> List[Dict[str, str]]:
    """Enrich every row. Adds the google_* columns."""
    out: List[Dict[str, str]] = []
    for i, row in enumerate(rows):
        name = row.get("name", "")
        g = enrich_one(name, area, key)
        merged = dict(row)
        merged.update({k: str(v) for k, v in g.items()})
        out.append(merged)
        if (i + 1) % 25 == 0:
            print(f"  google: {i+1}/{len(rows)}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN)
    return out


# ---------------------------------------------------------------------------
# Self-test — no network, no key
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
    check("_norm lowercase", _norm("A CUT ABOVE") == "a cut above")
    check("_norm punctuation", _norm("Jayne's Hair & Beauty") == "jayne s hair beauty")

    # score_match
    exact = {"displayName": {"text": "A Cut Above"},
             "formattedAddress": "Newcastle upon Tyne",
             "rating": 4.6, "userRatingCount": 214}
    check("exact + town + reviews scores high",
          score_match("A Cut Above", "Newcastle upon Tyne", exact) >= 5,
          detail=f"got {score_match('A Cut Above', 'Newcastle', exact)}")

    wrong = {"displayName": {"text": "Totally Different Ltd"},
             "formattedAddress": "London",
             "rating": 4.0, "userRatingCount": 10}
    check("wrong name + wrong town scores low",
          score_match("A Cut Above", "Newcastle", wrong) < 3,
          detail=f"got {score_match('A Cut Above', 'Newcastle', wrong)}")

    # skip-if-no-key path: _load_key with a temp env that has none
    global ENV_FILE
    real = ENV_FILE
    try:
        import tempfile
        tmp = Path(tempfile.mkdtemp()) / ".env"
        tmp.write_text("SMTP_HOST=x\n")
        ENV_FILE = tmp
        check("no key returns None", _load_key() is None)
    finally:
        ENV_FILE = real

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Add Google rating/reviews to scout rows.")
    ap.add_argument("--csv-in")
    ap.add_argument("--csv-out")
    ap.add_argument("--name")
    ap.add_argument("--area", default="")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    key = _load_key()
    if not key:
        print("No GOOGLE_PLACES_API_KEY in .env.production — skipping Google enrichment.")
        if args.csv_in:
            # Copy through unchanged, so the pipeline never breaks
            with open(args.csv_in, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            out_path = Path(args.csv_out or args.csv_in)
            if rows:
                with out_path.open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    w.writeheader()
                    w.writerows(rows)
                print(f"  copied unchanged: {out_path}")
        return 0

    if args.name:
        r = enrich_one(args.name, args.area, key)
        print(json.dumps(r, indent=2))
        return 0

    if args.csv_in:
        with open(args.csv_in, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        area = rows[0].get("area", "") if rows else ""
        print(f"enriching {len(rows)} rows with Google (area: {area})...", file=sys.stderr)
        enriched = enrich_rows(rows, area, key)
        out_path = Path(args.csv_out or args.csv_in.replace(".csv", "-google.csv"))
        if enriched:
            with out_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(enriched[0].keys()))
                w.writeheader()
                w.writerows(enriched)
        print(f"written: {out_path}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
