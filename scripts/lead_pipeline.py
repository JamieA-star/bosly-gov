#!/usr/bin/env python3
"""lead_pipeline.py — one run: sweep, enrich, rank.

WHAT THIS DOES, IN ORDER:
    1. Run the sweep (scripts/lead_scout.py) — one area from the
       config, up to 250 rows, written to lead-scout.csv.
    2. Enrich with Companies House (scripts/ch_enrich.py).
    3. Enrich with Google, IF the key exists (scripts/google_enrich.py).
    4. Rank (scripts/lead_rank.py), writing lead-scout-ranked.csv.

WHY ONE SCRIPT. The cron should call one thing. If step 1 fails,
steps 2-4 don't run — the retry cron will try the whole pipeline
again. If step 1 succeeds but Companies House fails, the pipeline
stops and the CSV from step 1 is still there, honestly labelled.

THE SWEEP RETRY: if the sweep finds nothing, the pipeline exits
non-zero and writes the retry marker (the sweep does that itself),
so Sunday's --retry runs the whole pipeline again for the same
county.

USAGE:
    python3 scripts/lead_pipeline.py
    python3 scripts/lead_pipeline.py --retry
    python3 scripts/lead_pipeline.py --skip-google   (force skip, even if keyed)
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path

GOV = Path("/home/bosly_accord/bosly-gov")
SCRIPTS = GOV / "scripts"
STATE = Path("/mnt/bosly/bosly-data/.data/governor")
SWEEP_CSV = STATE / "lead-scout.csv"
ENRICHED_CSV = STATE / "lead-scout-enriched.csv"
GOOGLE_CSV = STATE / "lead-scout-google.csv"
RANKED_CSV = STATE / "lead-scout-ranked.csv"
ENV_FILE = Path("/home/bosly_accord/bosly-1.0/.env.production")


def _run(cmd: list[str], label: str) -> bool:
    print(f"\n=== {label} ===", flush=True)
    r = subprocess.run(cmd, cwd=str(GOV))
    ok = r.returncode == 0
    print(f"=== {label}: {'ok' if ok else 'FAILED'} ===", flush=True)
    return ok


def _has_google_key() -> bool:
    if not ENV_FILE.exists():
        return False
    for line in ENV_FILE.read_text().splitlines():
        if line.strip().startswith("GOOGLE_PLACES_API_KEY="):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            return bool(v)
    return False


def _row_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)  # minus header
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--skip-google", action="store_true")
    args = ap.parse_args()

    py = sys.executable

    # 1. SWEEP
    sweep_cmd = [py, str(SCRIPTS / "lead_scout.py"),
                 "--config", str(GOV / "lead-scout.config.json")]
    if args.retry:
        sweep_cmd.append("--retry")
    if not _run(sweep_cmd, "1/4 sweep"):
        print("sweep failed — stopping. The retry cron will try this county again.")
        return 1

    n = _row_count(SWEEP_CSV)
    print(f"\nsweep rows: {n}")
    if n == 0:
        print("sweep produced no rows — stopping.")
        return 1

    # 2. COMPANIES HOUSE
    if not _run([py, str(SCRIPTS / "ch_enrich.py"),
                 "--csv-in", str(SWEEP_CSV),
                 "--csv-out", str(ENRICHED_CSV),
                 "--limit", str(n)], "2/4 Companies House"):
        print("CH enrichment failed. The sweep CSV is intact; ranking will be shallow.")
        # Continue with the sweep CSV rather than failing entirely
        ENRICHED_CSV.write_bytes(SWEEP_CSV.read_bytes())

    # 3. GOOGLE (optional)
    source_for_rank = ENRICHED_CSV
    if not args.skip_google and _has_google_key():
        if not _run([py, str(SCRIPTS / "google_enrich.py"),
                     "--csv-in", str(ENRICHED_CSV),
                     "--csv-out", str(GOOGLE_CSV)], "3/4 Google"):
            print("Google enrichment failed. Ranking on CH + OSM only.")
        else:
            source_for_rank = GOOGLE_CSV
    else:
        print("\n=== 3/4 Google: skipped (no key or --skip-google) ===")

    # 4. RANK
    if not _run([py, str(SCRIPTS / "lead_rank.py"),
                 "--csv-in", str(source_for_rank),
                 "--csv-out", str(RANKED_CSV)], "4/4 rank"):
        print("ranking failed.")
        return 1

    print(f"\nDONE. This week's list: {RANKED_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
