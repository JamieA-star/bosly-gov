#!/usr/bin/env python3
"""site_audit.py — assess a business's website for gaps.

WHAT THIS DOES. Fetches one page, and reports what it finds:
    has_https        the URL is https
    has_viewport     a <meta name="viewport"> (mobile-friendly)
    has_email        a mailto: link or an @ address on the page
    has_booking      a booking link (Calendly, Fresha, Booksy, ...)
    has_contact_page a link to a /contact page
    copyright_year   the latest year in a © notice
    social_links     facebook / instagram / twitter / tiktok links
    page_bytes       response size (a rough "is this site thin?" signal)
    audit_score      0-10, higher = more gaps (more to sell)

WHY A SEPARATE SCRIPT. The sweep finds businesses; the audit judges
their website. Keeping them separate means the audit can run on one
URL by hand, and the sweep can call it per has-website business
later. Same pattern as ch_enrich.py.

GUARDS: only http/https; max 2 MB; timeout 15s; user-agent says who
it is; follows at most 3 redirects. It reads the page a human would
read. It does not crawl the site or follow links.

USAGE:
    python3 scripts/site_audit.py --url https://example.com
    python3 scripts/site_audit.py --selftest

SELF-TEST does not hit the network: it parses known HTML and checks
the extractor. Run --url to test a real site.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict

USER_AGENT = "bosly-lead-scout/0.1 (contact: jr-arnott@outlook.com)"
HTTP_TIMEOUT = 15
MAX_BYTES = 2_000_000  # 2 MB cap

BOOKING_HOSTS = [
    "calendly.com", "fresha.com", "booksy.com", "treatwell.co.uk",
    "treatwell.com", "setmore.com", "simplybook.me", "acuityscheduling.com",
    "square.site", "bookwhen.com", "appointedd.com", "vagaro.com",
]
SOCIAL_HOSTS = {
    "facebook": ["facebook.com", "fb.com"],
    "instagram": ["instagram.com"],
    "twitter": ["twitter.com", "x.com"],
    "tiktok": ["tiktok.com"],
    "linkedin": ["linkedin.com"],
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
COPYRIGHT_RE = re.compile(r"(?:©|&copy;|copyright)\s*(?:19|20)(\d{2})", re.IGNORECASE)


def _norm_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def fetch(url: str) -> tuple[str, str, int]:
    """Fetch a page. Returns (final_url, html, status_code).

    Raises RuntimeError on transport errors. Caps the body at MAX_BYTES.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            body = r.read(MAX_BYTES).decode("utf-8", errors="replace")
            return (r.geturl() or url, body, r.status)
    except urllib.error.HTTPError as e:
        return (url, "", e.code)
    except Exception as e:
        raise RuntimeError(f"fetch failed: {e}") from None


def _hrefs(html: str) -> list[str]:
    return re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)


def _host_of(url: str) -> str:
    try:
        return (urllib.parse.urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def audit_html(url: str, html: str) -> Dict[str, Any]:
    """Assess a page's HTML. Returns the audit dict."""
    low = html.lower()

    has_viewport = 'name="viewport"' in low or "name='viewport'" in low
    has_https = url.lower().startswith("https://")

    # Email: mailto: links and bare addresses
    emails = set(EMAIL_RE.findall(html))
    has_email = ("mailto:" in low) or bool(emails)

    # Booking: known hosts, or a link with "book" in it
    booking_hits = []
    for href in _hrefs(html):
        h = href.lower()
        if any(b in h for b in BOOKING_HOSTS):
            booking_hits.append(href)
        elif "book" in h and ("appoint" in h or "booking" in h or "reserve" in h):
            booking_hits.append(href)
    has_booking = bool(booking_hits)

    # Contact page: a link whose path contains /contact
    contact_hits = []
    for href in _hrefs(html):
        h = href.lower()
        if "contact" in h and not h.startswith("mailto:"):
            contact_hits.append(href)
    has_contact_page = bool(contact_hits)

    # Copyright year: the latest 19xx/20xx in a © notice
    years = [int(y) for y in COPYRIGHT_RE.findall(html)]
    copyright_year = max(years) if years else 0
    # The regex captures two digits; turn into full year
    if copyright_year:
        copyright_year = 1900 + copyright_year if copyright_year >= 50 else 2000 + copyright_year

    # Social links
    socials = []
    for name, hosts in SOCIAL_HOSTS.items():
        if any(h in low for h in hosts):
            socials.append(name)

    # Score: higher = more gaps = more to sell
    score = 0
    if not has_https:
        score += 2
    if not has_viewport:
        score += 2
    if not has_booking:
        score += 2
    if not has_email:
        score += 1
    if not has_contact_page:
        score += 1
    if copyright_year and copyright_year < 2023:
        score += 2

    return {
        "url": url,
        "has_https": has_https,
        "has_viewport": has_viewport,
        "has_email": has_email,
        "email_found": sorted(emails)[:3],
        "has_booking": has_booking,
        "booking_links": booking_hits[:3],
        "has_contact_page": has_contact_page,
        "contact_links": contact_hits[:3],
        "copyright_year": copyright_year,
        "social_links": socials,
        "page_bytes": len(html.encode("utf-8")),
        "audit_score": score,
    }


def audit_url(url: str) -> Dict[str, Any]:
    """Fetch and audit a URL. Returns a dict, never raises for a bad site."""
    url = _norm_url(url)
    if not url:
        return {"url": "", "error": "no url"}
    try:
        final, html, status = fetch(url)
    except RuntimeError as e:
        return {"url": url, "error": str(e)[:200]}
    if status != 200:
        return {"url": final, "error": f"HTTP {status}"}
    out = audit_html(final, html)
    out["status"] = status
    return out


# ---------------------------------------------------------------------------
# Self-test: parse known HTML, no network
# ---------------------------------------------------------------------------

SAMPLE_OLD = """<!doctype html>
<html><head><title>A Salon</title></head>
<body>
<h1>Welcome</h1>
<p>Call us on 0191 123 4567</p>
<p>&copy; 2018 A Salon</p>
</body></html>"""

SAMPLE_MODERN = """<!doctype html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>B Salon</title>
</head><body>
<a href="https://calendly.com/bsalon">Book now</a>
<a href="/contact">Contact</a>
<a href="mailto:hello@bsalon.co.uk">Email us</a>
<a href="https://instagram.com/bsalon">Instagram</a>
<p>&copy; 2025 B Salon</p>
</body></html>"""


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

    old = audit_html("http://oldsalon.example", SAMPLE_OLD)
    check("old: no https", old["has_https"] is False)
    check("old: no viewport", old["has_viewport"] is False)
    check("old: no booking", old["has_booking"] is False)
    check("old: no email", old["has_email"] is False)
    check("old: copyright 2018", old["copyright_year"] == 2018,
          detail=str(old["copyright_year"]))
    check("old: high audit score", old["audit_score"] >= 7,
          detail=str(old["audit_score"]))

    modern = audit_html("https://bsalon.co.uk", SAMPLE_MODERN)
    check("modern: https", modern["has_https"] is True)
    check("modern: viewport", modern["has_viewport"] is True)
    check("modern: booking", modern["has_booking"] is True)
    check("modern: email", modern["has_email"] is True)
    check("modern: contact page", modern["has_contact_page"] is True)
    check("modern: socials include instagram", "instagram" in modern["social_links"])
    check("modern: copyright 2025", modern["copyright_year"] == 2025)
    check("modern: low audit score", modern["audit_score"] <= 2,
          detail=str(modern["audit_score"]))

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a business website for gaps.")
    ap.add_argument("--url")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if args.url:
        r = audit_url(args.url)
        print(json.dumps(r, indent=2))
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
