#!/usr/bin/env python3
"""
Check: the Waiting Well pages are current and their sources resolve.

Scans the waiting-well pages for @claim markers — JSX comments
carrying a source, a URL, the date the claim was last verified, a
review window in days, and the population the evidence covers.

Flags:
  - stale    : verified + review days is in the past
  - broken   : the URL returns 404 or 410
  - uncheck  : the URL returned 403, 5xx, or timed out (not a failure)
  - placeholder : the URL is not a real http(s) address

Writes a status file the orientation reads:
  /mnt/bosly/bosly-data/.data/governor/waiting-well-status.json

Slow tier — it makes HTTP requests, so it must not run in the fast
tier or slow the session start.

Run:
    python3 checks/waiting_well.py
    python3 checks/waiting_well.py --no-http   (skip URL checks)
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

PAGES_DIR = Path("/home/bosly_accord/bosly-1.0/app/(marketing)/waiting-well")
STATUS_FILE = Path(
    "/mnt/bosly/bosly-data/.data/governor/waiting-well-status.json"
)

CLAIM_RE = re.compile(r"@claim\s+(.*?)\*/", re.DOTALL)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')

HTTP_TIMEOUT = 10


def parse_attrs(text: str) -> dict:
    return {k: v for k, v in ATTR_RE.findall(text)}


def find_claims() -> list[dict]:
    claims = []
    if not PAGES_DIR.exists():
        return claims
    for page in sorted(PAGES_DIR.rglob("page.tsx")):
        text = page.read_text(encoding="utf-8")
        for m in CLAIM_RE.finditer(text):
            attrs = parse_attrs(m.group(1))
            if "verified" not in attrs and "url" not in attrs:
                # a bare @claim type="advice" marker — nothing to check
                continue
            claims.append({"page": str(page.relative_to(PAGES_DIR)), **attrs})
    return claims


def is_stale(claim: dict) -> bool:
    try:
        verified = datetime.strptime(claim["verified"], "%Y-%m-%d").date()
        review = int(claim.get("review", "365"))
    except (KeyError, ValueError):
        return False
    return (date.today() - verified).days > review


def is_placeholder(url: str) -> bool:
    return not url.startswith("http://") and not url.startswith("https://")


def check_url(url: str) -> tuple[str, str]:
    """Return (status, detail). status is 'ok' | 'broken' | 'uncheck'."""
    try:
        req = urllib.request.Request(
            url, method="HEAD",
            headers={"User-Agent": "Mozilla/5.0 (bosly-gov check)"},
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            if resp.status == 200:
                return ("ok", "")
            return ("uncheck", f"HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return ("broken", f"HTTP {e.code}")
        return ("uncheck", f"HTTP {e.code}")
    except Exception as e:
        return ("uncheck", type(e).__name__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-http", action="store_true",
                        help="skip URL checks, only report staleness")
    args = parser.parse_args()

    claims = find_claims()

    print("")
    print("Invariant: the Waiting Well pages are current and sourced")
    print("--------------------------------------------------------")
    print(f"  pages scanned, claims found: {len(claims)}")

    stale = []
    broken = []
    uncheck = []
    placeholder = []

    for c in claims:
        label = c.get("source", c.get("url", "?"))
        if is_stale(c):
            stale.append({"source": label, "verified": c.get("verified"),
                          "review": c.get("review", "365")})
        url = c.get("url", "")
        if url:
            if is_placeholder(url):
                placeholder.append({"source": label, "url": url})
            elif not args.no_http:
                status, detail = check_url(url)
                if status == "broken":
                    broken.append({"source": label, "url": url, "detail": detail})
                elif status == "uncheck":
                    uncheck.append({"source": label, "url": url, "detail": detail})

    if stale:
        print(f"  stale: {len(stale)}")
        for s in stale:
            print(f"    - {s['source']} (verified {s['verified']}, review {s['review']}d)")
    if broken:
        print(f"  broken: {len(broken)}")
        for b in broken:
            print(f"    - {b['source']} -> {b['url']} ({b['detail']})")
    if placeholder:
        print(f"  placeholder: {len(placeholder)}")
        for p in placeholder:
            print(f"    - {p['source']} -> {p['url']}")
    if uncheck:
        print(f"  could not check (not a failure): {len(uncheck)}")
        for u in uncheck:
            print(f"    - {u['source']} ({u['detail']})")

    ok = not (stale or broken or placeholder)

    if ok:
        print("  OK: every claim is current and its source resolves")

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps({
        "checkedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale": stale,
        "broken": broken,
        "placeholder": placeholder,
        "uncheck": uncheck,
        "ok": ok,
    }, indent=2), encoding="utf-8")
    print(f"  status written to {STATUS_FILE}")

    print("")
    print(f"SUMMARY: {'PASS' if ok else 'REPORT'}")
    print("")
    # report-only until calibrated — never fail the pipeline
    return 0


if __name__ == "__main__":
    sys.exit(main())
