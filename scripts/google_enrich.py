#!/usr/bin/env python3
"""scripts/google_enrich.py — fill Google rating and reviews for the top N.

Runs AFTER the scout and the ranker. The gap ranking is free; Google is
paid, so this touches only the top N — the number is the cost. It reads
the ranked CSV, looks up each business by name and postcode, writes the
rating, the review count, and the place id, and the ranker is re-run on
the enriched file.

Usage:
    python3 scripts/google_enrich.py --top 30
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

IN = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout-ranked.csv")
OUT = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout-enriched.csv")
API = "https://maps.googleapis.com/maps/api/place"


def _key() -> str:
    k = (os.environ.get("GOOGLE_PLACES_API_KEY") or "").strip()
    if k:
        return k
    try:
        for line in open("/home/bosly_accord/bosly-1.0/.env.production", encoding="utf-8"):
            if line.startswith("GOOGLE_PLACES_API_KEY=") or line.startswith("GOOGLE_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def lookup(name: str, postcode: str, key: str) -> dict:
    """Find the place, then read its rating and review count. Two calls."""
    q = f"{name} {postcode}".strip()
    find_url = API + "/findplacefromtext/json?" + urllib.parse.urlencode({
        "input": q, "inputtype": "textquery",
        "fields": "place_id,name,rating,user_ratings_total,formatted_address",
        "key": key,
    })
    try:
        with urllib.request.urlopen(find_url, timeout=15) as r:
            body = json.loads(r.read().decode())
    except Exception:
        return {}
    cands = body.get("candidates") or []
    if not cands:
        return {}
    c = cands[0]
    return {
        "google_place_id": c.get("place_id", ""),
        "google_rating": str(c.get("rating", "") or ""),
        "google_reviews": str(c.get("user_ratings_total", "") or ""),
        "google_address": c.get("formatted_address", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30, help="how many rows to enrich (the cost)")
    ap.add_argument("--in", dest="inp", default=str(IN))
    ap.add_argument("--out", dest="out", default=str(OUT))
    args = ap.parse_args()

    key = _key()
    if not key:
        print("no GOOGLE_PLACES_API_KEY; nothing enriched")
        return 0

    rows = list(csv.DictReader(open(args.inp, encoding="utf-8")))
    print(f"rows: {len(rows)}, enriching the top {args.top}")
    enriched = 0
    for i, r in enumerate(rows):
        if i >= args.top:
            break
        g = lookup(r.get("name") or "", r.get("postcode") or "", key)
        if g:
            r.update(g)
            enriched += 1
    fields = list(rows[0].keys()) if rows else []
    for extra in ("google_place_id", "google_rating", "google_reviews", "google_address"):
        if extra not in fields:
            fields.append(extra)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"enriched {enriched}/{min(args.top, len(rows))}; written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
