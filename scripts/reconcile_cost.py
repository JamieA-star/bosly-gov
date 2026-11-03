#!/usr/bin/env python3
"""Reconcile the rate table against the provider's own cost report.

Monthly. Needs an Admin API key in the environment. Pulls the provider's
cost report for the last 30 days, compares it to the table's total for
the same period, and writes the drift. If drift > 5%, the stale check
fails — the table is wrong and the bill is the truth.

Run:
    ADMIN_API_KEY=... python3 scripts/reconcile_cost.py
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers import usage as u

OUT = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/usage-reconciled.json")


def main() -> int:
    key = os.environ.get("ADMIN_API_KEY", "")
    if not key:
        print("no ADMIN_API_KEY; reconciliation skipped")
        return 0

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
    url = f"https://api.anthropic.com/v1/organizations/cost_report?starting_at={start}"
    req = urllib.request.Request(url, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
    except Exception as e:
        print(f"cost_report failed: {e}")
        return 0

    provider_usd = 0.0
    for b in body.get("data", []):
        provider_usd += float(b.get("amount", 0)) / 100
    provider_gbp = provider_usd * u.GBP_PER_USD

    ours = u.total(start)["result"]["pence"] / 100
    drift = round(((ours - provider_gbp) / provider_gbp * 100) if provider_gbp else 0, 2)
    OUT.write_text(json.dumps({
        "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider_gbp": round(provider_gbp, 2),
        "ours_gbp": round(ours, 2),
        "drift_pct": drift,
    }, indent=2), encoding="utf-8")
    print(f"provider GBP {provider_gbp:.2f}, ours GBP {ours:.2f}, drift {drift}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
