#!/usr/bin/env python3
"""Rank the sweep for the only list that matters: broken or missing site,
not managed, with a real email address.

Keeps a row only if:
  - managed_platform is no
  - contact_route is email
  - match_verified is yes and ch_status is active
  - it has no working site, or a site with a measured gap
"""
import csv, sys, json
sys.path.insert(0, "/home/bosly_accord/bosly-gov")

SRC = sys.argv[1] if len(sys.argv) > 1 else "/mnt/bosly/bosly-data/.data/governor/lead-east-sussex-v5-verified.csv"
OUT = SRC.replace(".csv", "-unmanaged.csv")

BAD_EMAIL = {"filler", "you", "example", "test", "typesetit", "noreply", "no-reply", "admin"}

def usable_email(r):
    es = [e.strip() for e in (r.get("audit_email") or "").replace(";", ",").split(",") if "@" in e]
    return [e for e in es
            if e.split("@")[0].lower() not in BAD_EMAIL
            and not e.lower().startswith(("example@", "you@"))]

def keep(r):
    if r.get("match_verified") != "yes" or r.get("ch_status") != "active":
        return None
    if (r.get("managed_platform") or "").lower() == "yes":
        return None
    if r.get("contact_route") != "email" or not usable_email(r):
        return None
    no_site = r.get("has_website") == "no"
    dead = r.get("has_website") == "yes" and not (r.get("audit_https") or "").strip()
    gaps = (r.get("audit_booking") == "no") or (r.get("audit_contact_page") == "no")
    if not (no_site or dead or gaps):
        return None
    return {"why": "no_site" if no_site else ("dead" if dead else "gap")}

rows = list(csv.DictReader(open(SRC)))
kept = []
for r in rows:
    why = keep(r)
    if why:
        r.update(why)
        r["email"] = ";".join(usable_email(r))
        kept.append(r)

order = {"no_site": 0, "dead": 1, "gap": 2}
kept.sort(key=lambda r: (order[r["why"]], r.get("name", "")))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ["why", "email"])
    w.writeheader()
    for r in kept:
        w.writerow({k: r.get(k, "") for k in w.fieldnames})
print(f"kept {len(kept)} of {len(rows)} -> {OUT}")
for r in kept[:25]:
    print(f"  [{r['why']:7}] {r['name'][:32]:32} | {r.get('city','?'):12} | {r['email']}")
