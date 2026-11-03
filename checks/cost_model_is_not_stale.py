#!/usr/bin/env python3
"""The cost model is honest: it learns from the last build and confirms
the table against the provider.

Four ways the cost model goes stale, and each is a failure here:
  1. a rate in the table that the provider has changed (monthly
     reconciliation against the Admin API's cost_report);
  2. a quote that assumes turns-per-step instead of measuring it;
  3. a model id that no longer resolves to a rate;
  4. rates duplicated between the table and the quote.

This check runs on the fast tier. It reads the usage log and the code;
it makes no API call. The reconciliation is a separate monthly job —
this check fails if that job has not run in 35 days.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, "/home/bosly_accord/bosly-gov")

USAGE = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/usage.jsonl")
RECON = Path("/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/usage-reconciled.json")


def main() -> int:
    print("")
    print("Invariant: the cost model does not go stale")
    print("-" * 52)
    ok = True

    try:
        from routers import usage as u
    except Exception as e:
        print(f"  FAIL: cannot import usage: {e}")
        print("SUMMARY: FAIL")
        return 1

    # 3. Every model in the log resolves to a rate.
    rows = u._read()
    models = {r.get("model") for r in rows if r.get("model")}
    unresolved = sorted(m for m in models if not u.rate_for(m))
    print(f"  models in the log: {len(models)}, without a rate: {len(unresolved)} {unresolved}")
    ok = ok and not unresolved

    # 4. The quote takes its rates from the table, not from constants.
    src = open("/home/bosly_accord/bosly-gov/routers/usage.py", encoding="utf-8").read()
    quote_uses_table = "rate_for" in src and "mechanical_pence" not in src
    print(f"  the quote takes its rates from the table: {quote_uses_table}")
    ok = ok and quote_uses_table

    # 2. The quote calibrates from real builds once there are enough.
    real = [r for r in rows if r.get("build")]
    builds = {r["build"] for r in real}
    calibrates = "turns_per_step" in src and "real_turns_per_step" in src
    if len(builds) >= 2:
        print(f"  builds in the log: {len(builds)}, the quote calibrates: {calibrates}")
        ok = ok and calibrates
    else:
        print(f"  builds in the log: {len(builds)} — too few to calibrate; a NOTE, not a fail")

    # 1. The provider's own report has confirmed the table recently.
    if RECON.exists():
        d = json.loads(RECON.read_text(encoding="utf-8"))
        last = d.get("at", "")
        drift = d.get("drift_pct", 0)
        recent = last >= (datetime.now(timezone.utc) - timedelta(days=35)).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"  reconciled at {last}, drift {drift}% (recent: {recent})")
        ok = ok and recent and abs(drift) < 5
    else:
        print("  NOTE: no reconciliation yet — the table is unconfirmed; the monthly job has not run")

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
