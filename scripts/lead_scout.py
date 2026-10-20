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
HTTP_TIMEOUT = 60  # per request; a county query can be slow, and 30s is too eager to give up
# The site audit is optional: if it is missing, the sweep still runs and
# every has-website row gets contact_route 'contact_page' (safer than
# 'email', which needs a real address).
try:
    import sys as _sys
    _sys.path.insert(0, "/home/bosly_accord/bosly-gov")
    from scripts.site_audit import audit_url as _audit_url  # type: ignore
except Exception:
    _audit_url = None

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


def overpass_query(bbox: tuple[float, float, float, float], family: str) -> str:
    """Build an Overpass QL query for ONE tag family in a bbox.

    A whole county with every family in one request times out the
    mirrors. So the sweep asks for one family at a time: shop, then
    amenity, then craft, then office, then healthcare. Each is a
    fraction of the load, and a slow family does not block the rest.
    """
    s, w, n, e = bbox
    return f"""
[out:json][timeout:90];
(
  node["{family}"]({s},{w},{n},{e});
  way["{family}"]({s},{w},{n},{e});
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



def _category_of(tags: dict) -> str:
    """Which business tag family this element has."""
    for key in ("shop", "amenity", "craft", "office", "healthcare"):
        if key in tags:
            return f"{key}={tags[key]}"
    return ""


def extract_rows(elements, gap: dict) -> list:
    """Turn Overpass elements into CSV rows, filtered to the gap.

    gap = {"has_phone": True, "no_website": True}
    A row survives if it has a phone (when required) and no website
    (when required), and has a name.
    """
    want_phone = bool(gap.get("has_phone", False))
    want_no_website = bool(gap.get("no_website", False))

    rows = []
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name:
            continue

        website = tags.get("website") or tags.get("contact:website") or ""
        phone = tags.get("phone") or tags.get("contact:phone") or ""

        if want_no_website and website:
            continue
        if want_phone and not phone:
            continue

        lat = el.get("lat") or (el.get("center") or {}).get("lat") or ""
        lon = el.get("lon") or (el.get("center") or {}).get("lon") or ""
        rows.append({
            "name": name,
            "category": _category_of(tags),
            "lat": str(lat),
            "lon": str(lon),
            "street": tags.get("addr:street", ""),
            "city": tags.get("addr:city", ""),
            "postcode": tags.get("addr:postcode", ""),
            "phone": phone,
            "osm_id": f'{el.get("type", "")}/{el.get("id", "")}',
            "has_website": "yes" if website else "no",
            "website_url": website,
        })
    return rows




def add_contact_route(rows: list, do_audit: bool = True) -> list:
    """For each row, decide how to contact the business.

    no website            -> contact_route = 'call'
    website, email found  -> 'email'
    website, contact page -> 'contact_page'
    website, neither      -> 'call'

    If the audit module is unavailable, every has-website row gets
    'contact_page' — the safe default, because we cannot confirm an
    email.
    """
    out = []
    for i, row in enumerate(rows):
        website = (row.get("has_website") or "").lower() == "yes"
        route = "call"
        audit_fields = {}
        if website and do_audit and _audit_url is not None:
            url = row.get("website_url") or ""
            # The OSM extractor does not put the URL in the CSV; we need
            # it. If it is absent, skip the audit and default to
            # contact_page.
            if url:
                try:
                    a = _audit_url(url)
                except Exception:
                    a = {}
                if a and not a.get("error"):
                    audit_fields = {
                        "audit_score": str(a.get("audit_score", "")),
                        "audit_email": ";".join(a.get("email_found") or []),
                        "audit_booking": "yes" if a.get("has_booking") else "no",
                        "audit_contact_page": "yes" if a.get("has_contact_page") else "no",
                        "audit_viewport": "yes" if a.get("has_viewport") else "no",
                        "audit_https": "yes" if a.get("has_https") else "no",
                        "audit_copyright": str(a.get("copyright_year", "")),
                    }
                    if a.get("email_found"):
                        route = "email"
                    elif a.get("has_contact_page"):
                        route = "contact_page"
                    else:
                        route = "call"
            else:
                # Website flagged but no URL captured — be honest, ask a
                # human to look.
                route = "contact_page"
        elif website:
            route = "contact_page"
        merged = dict(row)
        merged.update(audit_fields)
        merged["contact_route"] = route
        out.append(merged)
        if (i + 1) % 25 == 0:
            print(f"  audited {i+1}/{len(rows)}", file=sys.stderr)
    return out


def write_csv(rows: list, out: Path, area: str = "") -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "category", "lat", "lon", "street", "city",
              "postcode", "phone", "osm_id", "has_website", "website_url",
              "contact_route", "audit_score", "audit_email", "audit_booking",
              "audit_contact_page", "audit_viewport", "audit_https",
              "audit_copyright", "area"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r2 = {k: r.get(k, "") for k in fields}
            r2["area"] = area
            w.writerow(r2)


def _retry_path(state_path: Path) -> Path:
    return state_path.with_name("lead-scout.retry.json")


def _write_retry(state_path: Path, area: str, area_index: int) -> None:
    p = _retry_path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "area": area,
        "area_index": area_index,
        "first_failed": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "attempts": 1,
    }, indent=2) + "\n", encoding="utf-8")


def _read_retry(state_path: Path) -> dict:
    p = _retry_path(state_path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _clear_retry(state_path: Path) -> None:
    p = _retry_path(state_path)
    try:
        p.unlink()
    except FileNotFoundError:
        pass


def _read_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")




def main() -> int:
    ap = argparse.ArgumentParser(description="Lead scout sweep — one area per run.")
    ap.add_argument("--config", default="/home/bosly_accord/bosly-gov/lead-scout.config.json",
                    help="path to lead-scout.config.json")
    ap.add_argument("--retry", action="store_true",
                    help="retry the area that failed last run, if a marker exists")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    areas = cfg.get("areas") or []
    if not areas:
        raise SystemExit("config has no areas")

    gap = cfg.get("gap") or {}
    out = Path(cfg.get("output") or DEFAULT_OUT)
    state_path = Path(cfg.get("state") or "/mnt/bosly/bosly-data/.data/governor/lead-scout.sweep.json")
    cap = int(cfg.get("max_rows_per_area") or 250)

    state = _read_state(state_path)
    retry = _read_retry(state_path)

    if args.retry and retry.get("area"):
        # A previous run failed. Try that area again.
        area = retry["area"]
        idx = int(retry.get("area_index", 0)) % len(areas)
        retry["attempts"] = int(retry.get("attempts", 1)) + 1
        print(f"lead_scout RETRY (attempt {retry['attempts']}): {area}")
    else:
        idx = int(state.get("next_index", 0)) % len(areas)
        area = areas[idx]
        print(f"lead_scout sweep: area {idx+1}/{len(areas)} — {area}")

    print(f"lead_scout sweep: area {idx+1}/{len(areas)} — {area}")
    print("  geocoding area...")
    bbox = geocode_area(area)
    if bbox is None:
        raise SystemExit(f"could not geocode {area!r}")
    print(f"  bbox: {bbox}")
    # shop and craft are the trades the gap is for. amenity returns
    # every bench and bus stop, office returns every estate agent,
    # healthcare is sparse. Dropping them makes the sweep gentler on
    # Overpass and the shortlist more relevant. Add them back if the
    # shortlist needs cafés or clinics.
    families = ["shop", "craft"]
    elements = []
    for fam in families:
        print(f"  querying Overpass: {fam}...")
        try:
            data = overpass_request(overpass_query(bbox, fam))
            got = data.get("elements") or []
            elements.extend(got)
            print(f"    {fam}: {len(got)} elements")
        except SystemExit as e:
            print(f"    {fam}: FAILED ({str(e)[:120]})")
            # A failed family does not stop the sweep; the others
            # still return. The row count will be lower, honestly.
            continue
        # Sleep between families: a burst of requests gets throttled,
        # a trickle does not. 4 seconds is enough to stay polite.
        time.sleep(4)
    print(f"  {len(elements)} elements found in total")
    if not elements:
        print("  NO ELEMENTS — all families failed or returned nothing.")
        print("  Not writing the CSV. Not advancing the sweep.")
        if retry.get("area") == area:
            _write_retry(state_path, area, idx)
        else:
            _write_retry(state_path, area, idx)
        print(f"  retry marker written for {area}; a 12-hour cron will try again.")
        raise SystemExit(1)

    rows = extract_rows(elements, gap)
    print(f"  {len(rows)} match the gap")
    if len(rows) > cap:
        rows = rows[:cap]
        print(f"  capped at {cap}")
    print("  deciding contact route (auditing websites)...")
    rows = add_contact_route(rows, do_audit=True)
    n_email = sum(1 for r in rows if r.get("contact_route") == "email")
    n_page = sum(1 for r in rows if r.get("contact_route") == "contact_page")
    n_call = sum(1 for r in rows if r.get("contact_route") == "call")
    print(f"  routes: email={n_email} contact_page={n_page} call={n_call}")

    write_csv(rows, out, area=area)
    print(f"  written: {out}")

    _clear_retry(state_path)
    next_idx = (idx + 1) % len(areas)
    _write_state(state_path, {
        "next_index": next_idx,
        "last_area": area,
        "last_run": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "last_count": len(rows),
    })
    print(f"  next area: {areas[next_idx]}")
    return 0




if __name__ == "__main__":
    sys.exit(main())
