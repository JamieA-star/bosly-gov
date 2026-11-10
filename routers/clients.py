"""The client department: one profile per verified business.

A profile is a thing of kind 'client'. The body is JSON with four
sections: identity, lawful, gap, timeline. A row becomes a profile only
if it can fill identity, lawful and gap — the scout's acceptance test.
Nothing here sends; it records what is known and what was drafted.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from typing import Any, Dict

sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers.tools import save_thing, read_thing, find_things

SECTIONS = ("identity", "lawful", "gap")

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def profile_from_row(row: Dict[str, Any], source_date: str) -> Dict[str, Any]:
    """Build the body, or raise with what is missing."""
    identity = {
        "name": row.get("name",""), "category": row.get("category",""),
        "city": row.get("city",""), "postcode": row.get("postcode",""),
        "osm_id": row.get("osm_id",""),
    }
    lawful = {
        "ch_name": row.get("ch_name",""), "ch_number": row.get("ch_number",""),
        "ch_status": row.get("ch_status",""), "ch_address": row.get("ch_address",""),
        "match_verified": row.get("match_verified",""),
        "match_reason": row.get("match_reason",""),
        "source_url": row.get("website_url",""), "source_date": source_date,
    }
    gap = {
        "problems": [p for p in (row.get("problems") or "").split(",") if p and p != "none"],
        "evidence": {
            "copyright": row.get("audit_copyright",""),
            "https": row.get("audit_https",""),
            "viewport": row.get("audit_viewport",""),
            "booking": row.get("audit_booking",""),
            "contact_page": row.get("audit_contact_page",""),
            "website_url": row.get("website_url",""),
        },
        "route": row.get("route",""),
        "contact": (row.get("audit_email","") if row.get("route")=="email" else
                    row.get("website_url","") if row.get("route")=="form" else
                    row.get("phone","")),
    }
    missing = []
    if not identity["name"]: missing.append("identity.name")
    if not (lawful["ch_number"] and lawful["match_verified"] == "yes" and lawful["ch_status"] == "active"):
        missing.append("lawful: verified active company")
    if not gap["problems"] or not gap["route"]: missing.append("gap: problems and route")
    if missing:
        raise ValueError("cannot profile: " + "; ".join(missing))
    return {"identity": identity, "lawful": lawful, "gap": gap,
            "state": "new", "timeline": []}

def open_profile(row: Dict[str, Any], source_date: str) -> Dict[str, Any]:
    body = profile_from_row(row, source_date)
    # status is the store's vocabulary (active/done/lost/paused).
    # The pipeline state lives in the body, where it can grow.
    r = save_thing(kind="client", title=body["identity"]["name"],
                   body=json.dumps(body), status="active",
                   tags=body["identity"]["category"])
    return r

def record_event(thing_id: str, event: str, detail: str = "") -> Dict[str, Any]:
    r = read_thing(thing_id)
    if not r.get("ok"):
        return r
    body = json.loads(r["result"].get("body") or "{}")
    body.setdefault("timeline", []).append({"at": _now(), "event": event, "detail": detail})
    body["state"] = event
    store_status = "lost" if event in ("opted_out", "closed") else "active"
    return save_thing(kind="client", title=body["identity"]["name"],
                      body=json.dumps(body), status=store_status,
                      thing_id=thing_id)

# --- The draft: four beats, two sentences, body only (the signature is IONOS) ---
#
# Families, because the cost is different for each:
#   appointment — loses bookings      (hairdresser, beauty, barber, clinic, garage)
#   product     — loses sales         (deli, cheese, butcher, bakery, clothes, books, jewellery, shoes)
#   service     — loses enquiries     (kitchen, flooring, mobile repair, builder, plumber)
#
# The lead is the strongest CHECKABLE fact — dead, stale with a year, not
# mobile, no HTTPS, no site — because a fact they can verify in ten seconds
# is what makes the email not a mail-merge. "No booking" only leads when
# nothing more specific is true, and never for a product shop.

FAMILY = {
    "shop=hairdresser": "appointment", "shop=beauty": "appointment",
    "shop=barber": "appointment", "amenity=clinic": "appointment",
    "shop=car_repair": "appointment",
    "shop=deli": "product", "shop=cheese": "product", "shop=butcher": "product",
    "shop=bakery": "product", "shop=greengrocer": "product",
    "shop=clothes": "product", "shop=shoes": "product", "shop=books": "product",
    "shop=jewelry": "product", "shop=convenience": "product",
    "shop=supermarket": "product", "shop=stationery": "product",
    "shop=kitchen": "service", "shop=flooring": "service",
    "shop=mobile_phone": "service", "shop=hifi": "service",
    # product shops the 30 profiles exposed:
    "shop=bicycle": "product", "shop=farm": "product", "shop=gift": "product",
    "shop=interior_decoration": "product", "shop=florist": "product",
    "shop=pet": "product", "shop=toys": "product", "shop=sports": "product",
    "shop=music": "product", "shop=art": "product", "shop=antiques": "product",
    "shop=electronics": "product", "shop=hardware": "product",
    "shop=garden_centre": "product", "shop=car": "product",
    "shop=car_parts": "product", "shop=optician": "product",
}

COST = {
    "appointment": "so anyone who finds you after hours has to remember to call — most don't",
    "product": "so anyone who'd have bought from you after hours goes somewhere else",
    "service": "so anyone who wanted a quote after hours never asks",
}

VERB = {"appointment": "book", "product": "order", "service": "enquire"}

# checkable facts first; generic gaps last
LEAD_ORDER = ["dead_site", "no_website", "stale_site", "not_mobile",
              "no_https", "no_contact_route", "no_booking"]

def _family(ident: dict) -> str:
    return FAMILY.get(ident.get("category", ""), "service")

# plural and verb per noun, so the sentence is English.
# ("rings", "sell") — a jeweller sells rings. ("repairs", "do") — a bike shop does repairs.
NOUN = {
    "bike": ("bikes", "do"), "bicycle": ("bicycles", "do"),
    "repair": ("repairs", "do"), "service": ("services", "do"),
    "ring": ("rings", "sell"), "necklace": ("necklaces", "sell"),
    "dress": ("dresses", "sell"), "bridal": ("bridal wear", "sell"),
    "suit": ("suits", "sell"), "gift": ("gifts", "sell"),
    "produce": ("produce", "sell"), "farm": ("farm produce", "sell"),
    "vegetable": ("vegetables", "sell"), "cheese": ("cheese", "sell"),
    "fitting": ("fittings", "do"), "alteration": ("alterations", "do"),
}
SERVICE_WORDS = ("repair", "service", "fitting", "alteration", "measure", "consultation")

def _beats(problem: str, ev: dict, ident: dict, fam: str) -> tuple[str, str] | None:
    url = ev.get("website_url") or "your site"
    cost = COST[fam]
    if problem == "dead_site":
        return (f"I tried {url} three times and it didn't load",
                "right now anyone searching for you finds nothing")
    if problem == "no_website":
        return ("you've no website at all",
                f"so when someone searches for what you do in {ident.get('city') or 'the area'}, they find the ones that do")
    if problem == "no_https":
        return ("your site shows 'Not Secure' in the browser",
                "people leave before they read a word")
    if problem == "not_mobile":
        return ("your site doesn't work on a phone",
                "and that's where most people look")
    if problem == "stale_site":
        y = (ev.get("copyright") or "").strip()
        # 0 and "" both mean "no copyright found" — not a year, not a fact.
        if not y.isdigit():
            return None
        yr = int(y)
        if not (1900 <= yr <= 2100) or yr >= 2023:
            return None
        return (f"your site still says {yr}", "which tells a customer nobody's looking after it")
    if problem == "no_contact_route":
        return ("there's no way to contact you except a phone number", cost)
    if problem == "no_booking":
        prods = [p for p in (ev.get("products") or "").split(",") if p]
        action = ev.get("customer_action") or VERB.get(fam, "enquire")
        if prods and action == "book":
            # the thing that gets booked is a service, not a product
            svc = next((w for w in prods if w in SERVICE_WORDS), None)
            if svc:
                noun, verb = NOUN.get(svc, (svc + "s", "do"))
                return (f"you {verb} {noun} but there's no way to book one online", cost)
        if prods and action == "order":
            noun, verb = NOUN.get(prods[0], (prods[0] + "s", "sell"))
            return (f"you {verb} {noun} but there's no way to order from your site", cost)
        if fam == "product":
            return ("there's no way to order from your site", cost)
        return (f"there's no way to {VERB[fam]} online", cost)
    return None

def record_edit(thing_id: str, original: str, edited: str) -> Dict[str, Any]:
    """Store what the founder changed. Ten edits is a voice; one is a note."""
    r = read_thing(thing_id)
    if not r.get("ok"):
        return r
    body = json.loads(r["result"].get("body") or "{}")
    edits = body.setdefault("edits", [])
    edits.append({"at": _now(), "original": original, "edited": edited})
    return save_thing(kind="client", title=body["identity"]["name"],
                      body=json.dumps(body), status="active", thing_id=thing_id)


def draft_email(thing_id: str) -> Dict[str, Any]:
    """Draft from the profile's strongest checkable fact. Records 'drafted' first."""
    r = read_thing(thing_id)
    if not r.get("ok"):
        return r
    body = json.loads(r["result"].get("body") or "{}")
    gap = body.get("gap", {})
    ev = gap.get("evidence") or {}
    ident = body.get("identity", {})
    probs = gap.get("problems") or []
    fam = _family(ident)
    # for a product shop, no_booking is not a lead; anything checkable beats it
    usable = [p for p in LEAD_ORDER if p in probs]
    if fam == "product":
        # no_booking is not the lead for a product shop, but it is the
        # fallback when nothing more specific has a real fact behind it.
        usable = [p for p in usable if p != "no_booking"] + ["no_booking"]
    for lead in usable:
        b = _beats(lead, ev, ident, fam)
        if b:
            pain, cost = b
            text = (f"Hi, {pain} — {cost}. I fix that kind of thing. "
                    f"Want me to show you the full picture, free?")
            record_event(thing_id, "drafted", lead)
            return {"ok": True, "result": {"lead": lead, "family": fam, "text": text}}
    return {"ok": False, "error": f"no usable lead in {probs} for family {fam}"}
