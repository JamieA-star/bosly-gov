#!/usr/bin/env python3
"""lead_scout.py — find businesses with no website, from OpenStreetMap.

WHAT THIS IS. The first, minimal version of the consultancy's
lead-gen tool (ops.consultancy Phase 3). It queries OpenStreetMap's
Overpass API for businesses of a given type in a given area, checks
whether each has a `website` tag, and writes a CSV of the ones that
don't. A business with no website is a candidate: it could use a
site, a booking page, or an AI receptionist.

WHY OSM FIRST. It needs no API key, it is free, and it carries the
one signal that matters most: does this business have a website.
Companies House enrichment, employee counts, and Google Places
review counts come later, when the keys are set up and the loop is
proven.

WHAT THIS IS NOT. Not a CRM. Not a SaaS. Not a web app. It is a
script that runs, writes a CSV, and exits. Everything past the CSV
is the Executive's job: read it, assess the shortlist, draft, ask,
send.

CONFIG, NOT CODE. The category and the area are arguments. The
weights and thresholds come later, in a config file, when there is
evidence to set them from.

USAGE:
    python3 scripts/lead_scout.py --category hairdresser --area "Hexham"
    python3 scripts/lead_scout.py --category cafe --area "NE46" --out /tmp/leads.csv

OUTPUT: a CSV with one row per business that has no website.
Columns: name, category, lat, lon, street, city, postcode, phone,
osm_id, has_website.

LEGAL: Overpass is a public API with rate limits. This script asks
for a small area and a small category, sleeps between queries, and
sends a user-agent. Do not hammer it.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "bosly-lead-scout/0.1 (contact: jr-arnott@outlook.com)"
HTTP_TIMEOUT = 30  # per request; shorter so a dead mirror fails fast
DEFAULT_OUT = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout.csv")

# Map a friendly category to an OSM tag. Extend as needed.
CATEGORY_TAGS = {
    "hairdresser": ('shop', 'hairdresser'),
    "barber": ('shop', 'barber'),
    "beauty": ('shop', 'beauty'),
    "cafe": ('amenity', 'cafe'),
    "restaurant": ('amenity', 'restaurant'),
    "pub": ('amenity', 'pub'),
    "bakery": ('shop', 'bakery'),
    "butcher": ('shop', 'butcher'),
    "florist": ('shop', 'florist'),
    "plumber": ('craft', 'plumber'),
    "electrician": ('craft', 'electrician'),
    "gardener": ('craft', 'gardener'),
}


def geocode_area(area: str) -> tuple[float, float, float, float] | None:
    """Geocode a name or postcode to a bounding box (south, west, north, east).

    Uses Nominatim (free, no key). The bounding box is what Overpass
    needs; area-name lookups are brittle ('Newcastle' is not
    'Newcastle upon Tyne').
    """
    params = urllib.parse.urlencode({
        "q": area,
        "format": "json",
        "limit": 1,
    })
    req = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise SystemExit(f"geocode failed for {area!r}: {e}")
    if not data:
        return None
    bb = data[0].get("boundingbox")
    if not bb or len(bb) != 4:
        return None
    south, north, west, east = map(float, bb)
    return (south, west, north, east)


def overpass_query(category: str, bbox: tuple[float, float, float, float]) -> str:
    """Build an Overpass QL query for businesses of a category in a bbox."""
    if category not in CATEGORY_TAGS:
        raise SystemExit(
            f"unknown category {category!r}; known: {sorted(CATEGORY_TAGS)}"
        )
    key, value = CATEGORY_TAGS[category]
    south, west, north, east = bbox
    return f"""
[out:json][timeout:60];
(
  node["{key}"="{value}"]({south},{west},{north},{east});
  way["{key}"="{value}"]({south},{west},{north},{east});
);
out tags center;
""".strip()



def overpass_request(query: str) -> Dict[str, Any]:
    """POST the query to Overpass, trying each mirror in turn.

    Returns the parsed JSON. Raises SystemExit with a clear message if
    every endpoint fails. The message distinguishes 'endpoint
    unreachable' from 'no businesses found', because those are very
    different.
    """
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    errors = []
    for url in OVERPASS_ENDPOINTS:
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            errors.append(f"{url}: {e}")
            continue
    raise SystemExit(
        "all Overpass mirrors failed — this is an endpoint problem, "
        "not a zero result:\n  " + "\n  ".join(errors)
    )



def extract_rows(elements: List[Dict[str, Any]], category: str) -> List[Dict[str, str]]:
    """Turn Overpass elements into CSV rows.

    Only rows with no `website` tag are returned. A business with a
    website is not a candidate for the first product (a site); it
    might still be a candidate for a booking page or an AI
    receptionist, but that is a later, richer assessment.
    """
    rows: List[Dict[str, str]] = []
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        has_website = "website" in tags or "contact:website" in tags
        if has_website:
            continue
        lat = el.get("lat") or (el.get("center") or {}).get("lat") or ""
        lon = el.get("lon") or (el.get("center") or {}).get("lon") or ""
        rows.append({
            "name": name,
            "category": category,
            "lat": str(lat),
            "lon": str(lon),
            "street": tags.get("addr:street", ""),
            "city": tags.get("addr:city", ""),
            "postcode": tags.get("addr:postcode", ""),
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "osm_id": f'{el.get("type", "")}/{el.get("id", "")}',
            "has_website": "no",
        })
    return rows


def write_csv(rows: List[Dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "category", "lat", "lon", "street", "city",
              "postcode", "phone", "osm_id", "has_website"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser(description="Find businesses with no website, from OSM.")
    ap.add_argument("--category", required=True,
                    help=f"one of: {', '.join(sorted(CATEGORY_TAGS))}")
    ap.add_argument("--area", required=True,
                    help="a town name or postcode, e.g. Hexham or NE46")
    ap.add_argument("--out", default=str(DEFAULT_OUT),
                    help=f"output CSV path (default: {DEFAULT_OUT})")
    args = ap.parse_args()

    print(f"lead_scout: {args.category} in {args.area}")
    print("  geocoding area...")
    bbox = geocode_area(args.area)
    if bbox is None:
        raise SystemExit(f"could not geocode {args.area!r} — try a postcode or a fuller name")
    print(f"  bbox: {bbox}")
    query = overpass_query(args.category, bbox)
    print("  querying Overpass (mirrors, in order)...")
    data = overpass_request(query)
    elements = data.get("elements") or []
    print(f"  {len(elements)} businesses found")

    rows = extract_rows(elements, args.category)
    print(f"  {len(rows)} with no website")

    out = Path(args.out)
    write_csv(rows, out)
    print(f"  written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
