#!/usr/bin/env python3
"""lead_rank.py — rank a scout CSV and write the week's shortlist.

WHAT THIS DOES. Reads lead-scout.csv, scores every row on the signals
available (the gap, Companies House, and Google if present), sorts,
and writes lead-scout-ranked.csv with:
    rank            1..N
    fit_score       the score
    fit_breakdown   which signals contributed
    call_list       yes for the top N (default 10)
The top `pick` (default 15) are written; the rest are dropped.

WHY A SEPARATE SCRIPT. The sweep finds; the ranker judges. Keeping
them separate means the Executive can re-rank an existing CSV without
re-running the sweep, and the ranking weights can be tuned without
touching the discovery code.

WEIGHTS come from lead-scout.config.json -> fit.weights.
Missing signals score 0, not an error — a row without Google data
still ranks on Companies House and the gap.

USAGE:
    python3 scripts/lead_rank.py --csv-in lead-scout.csv --csv-out lead-scout-ranked.csv
    python3 scripts/lead_rank.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CONFIG = Path("/home/bosly_accord/bosly-gov/lead-scout.config.json")
DEFAULT_IN = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout.csv")
DEFAULT_OUT = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout-ranked.csv")

DEFAULT_WEIGHTS = {
    "has_phone": 1,
    "ch_active": 1,
    "ch_age_over_12m": 1,
    "bookable_trade": 1,
    "has_address": 1,
    "google_good_reviews": 2,
    "google_few_reviews": -1,
}
DEFAULT_BOOKABLE = [
    "hairdresser", "barber", "beauty", "therapist", "dentist",
    "garage", "plumber", "electrician", "physio", "tutor",
    "veterinary", "cafe", "restaurant",
]
DEFAULT_THRESHOLDS = {"good_reviews_min": 20, "good_rating_min": 4.0, "few_reviews_max": 5}


def _to_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(str(v)))
    except Exception:
        return default


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(str(v))
    except Exception:
        return default


def score_row(row: Dict[str, str], weights: Dict[str, int],
              bookable: List[str], thresholds: Dict[str, float]) -> tuple[int, str]:
    """Score one row. Returns (score, breakdown)."""
    score = 0
    bits = []

    if row.get("phone"):
        score += weights.get("has_phone", 0)
        bits.append("phone")

    # A Companies House match only counts if it is medium or high
    # confidence. A low-confidence name match is a guess, and a guess
    # should not score the same as a verified company.
    ch_conf = (row.get("match_confidence") or "").lower()
    ch_trusted = ch_conf in ("medium", "high")

    status = (row.get("ch_status") or "").lower()
    if status == "active" and ch_trusted:
        score += weights.get("ch_active", 0)
        bits.append("active")

    age = _to_int(row.get("ch_age_months"), 0)
    if age >= 12 and ch_trusted:
        score += weights.get("ch_age_over_12m", 0)
        bits.append(f"age{age}m")

    # bookable trade: the OSM category is "shop=hairdresser" etc.
    cat = (row.get("category") or "").lower()
    if any(b in cat for b in bookable):
        score += weights.get("bookable_trade", 0)
        bits.append("bookable")

    if row.get("street") or row.get("city") or row.get("postcode"):
        score += weights.get("has_address", 0)
        bits.append("address")

    # Google, if present
    gr = _to_float(row.get("google_rating"), 0.0)
    grc = _to_int(row.get("google_reviews"), 0)
    if grc >= thresholds.get("good_reviews_min", 20) and gr >= thresholds.get("good_rating_min", 4.0):
        score += weights.get("google_good_reviews", 0)
        bits.append(f"google{gr}★/{grc}")
    elif grc and grc <= thresholds.get("few_reviews_max", 5):
        score += weights.get("google_few_reviews", 0)
        bits.append("google-few")

    return score, "; ".join(bits)


def rank_rows(rows: List[Dict[str, str]], cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    fit = cfg.get("fit") or {}
    weights = fit.get("weights") or DEFAULT_WEIGHTS
    bookable = fit.get("bookable_trades") or DEFAULT_BOOKABLE
    thresholds = fit.get("google_thresholds") or DEFAULT_THRESHOLDS
    pick = int(fit.get("pick", 15))
    call_n = int(fit.get("call_list", 10))

    scored = []
    for r in rows:
        s, bits = score_row(r, weights, bookable, thresholds)
        scored.append((s, bits, r))

    # Sort by score desc, then by google reviews desc (so within a tie,
    # a business with more reviews comes first), then by name for stability.
    def _sort_key(t):
        s, bits, r = t
        return (-s, -_to_int(r.get("google_reviews"), 0), (r.get("name") or "").lower())

    scored.sort(key=_sort_key)
    top = scored[:pick]

    out = []
    for i, (s, bits, r) in enumerate(top, start=1):
        r2 = dict(r)
        r2["rank"] = str(i)
        r2["fit_score"] = str(s)
        r2["fit_breakdown"] = bits
        r2["call_list"] = "yes" if i <= call_n else "no"
        out.append(r2)
    return out


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

    cfg = {"fit": {"pick": 3, "call_list": 2}}
    rows = [
        # strong: phone, active, old, bookable, address
        {"name": "Alpha", "phone": "1", "ch_status": "active", "ch_age_months": "50",
         "category": "shop=hairdresser", "street": "X", "google_rating": "4.6", "google_reviews": "200"},
        # medium: phone, active, no age
        {"name": "Beta", "phone": "1", "ch_status": "active", "ch_age_months": "3",
         "category": "shop=cafe", "google_rating": "", "google_reviews": ""},
        # weak: no phone
        {"name": "Gamma", "phone": "", "ch_status": "active", "ch_age_months": "50",
         "category": "shop=plumber", "street": "X"},
        # strong-ish: phone, old, bookable
        {"name": "Delta", "phone": "1", "ch_status": "active", "ch_age_months": "30",
         "category": "craft=electrician", "google_rating": "4.0", "google_reviews": "2"},
    ]
    ranked = rank_rows(rows, cfg)
    check("returns at most pick", len(ranked) <= 3, detail=f"{len(ranked)}")
    check("top is Alpha", ranked[0]["name"] == "Alpha", detail=ranked[0]["name"])
    check("rank starts at 1", ranked[0]["rank"] == "1")
    check("call_list top 2", ranked[0]["call_list"] == "yes" and ranked[1]["call_list"] == "yes")
    if len(ranked) >= 3:
        check("third is not call_list", ranked[2]["call_list"] == "no")

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Rank a scout CSV into this week's shortlist.")
    ap.add_argument("--csv-in", default=str(DEFAULT_IN))
    ap.add_argument("--csv-out", default=str(DEFAULT_OUT))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    cfg = {}
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}

    inp = Path(args.csv_in)
    if not inp.exists():
        raise SystemExit(f"input not found: {inp}")
    with inp.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"no rows in {inp}")

    ranked = rank_rows(rows, cfg)
    out = Path(args.csv_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if ranked:
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(ranked[0].keys()))
            w.writeheader()
            w.writerows(ranked)
    print(f"ranked {len(rows)} -> {len(ranked)}; written: {out}")
    for r in ranked[:5]:
        print(f"  {r['rank']:>2}. {r['name'][:30]:30} score={r['fit_score']:>2} "
              f"call={r['call_list']:3} ({r['fit_breakdown']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
