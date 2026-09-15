#!/usr/bin/env python3
"""
Bosly Gov check runner.

Reads the manifest, runs the matching checks for the requested tier,
writes per-check JSON reports, prints a short summary, exits non-zero
if any check failed.

Usage:
    python3 runners/run_checks.py --tier fast
    python3 runners/run_checks.py --tier fast --manifest manifests/checks.yml
    python3 runners/run_checks.py --tier all

Reports are written to:
    /mnt/bosly/bosly-data/reports/YYYY-MM-DD/<check_id>.json

This is Phase 1 of the Gov plan. See PLAN.md.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.alert import send_failure_alert

REPORTS_ROOT = Path("/mnt/bosly/bosly-data/reports")
DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "manifests" / "checks.yml"


def load_manifest(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def run_check(project_name: str, project: dict, check: dict) -> dict:
    check_id = check["id"]
    severity = check.get("severity", "medium")
    command = check["command"]
    cwd = project["root"]

    started = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        exit_code = 124
        stdout = ""
        stderr = "check timed out after 600 seconds"
    elapsed_ms = int((time.time() - started) * 1000)

    status = "pass" if exit_code == 0 else "fail"

    return {
        "check_id": check_id,
        "project": project_name,
        "status": status,
        "severity": severity,
        "exit_code": exit_code,
        "duration_ms": elapsed_ms,
        "stdout_tail": stdout[-2000:] if stdout else "",
        "stderr_tail": stderr[-2000:] if stderr else "",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_report(report: dict) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = REPORTS_ROOT / day
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / (report["check_id"] + ".json")
    with path.open("w") as f:
        json.dump(report, f, indent=2)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="fast", choices=["fast", "slow", "all"])
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"FAIL: manifest not found at {manifest_path}", file=sys.stderr)
        return 2

    manifest = load_manifest(manifest_path)
    projects = manifest.get("projects", {})

    tiers = ["fast", "slow"] if args.tier == "all" else [args.tier]

    all_reports = []
    for project_name, project in projects.items():
        for tier in tiers:
            checks = project.get("tiers", {}).get(tier, []) or []
            for check in checks:
                report = run_check(project_name, project, check)
                report["tier"] = tier
                path = write_report(report)
                report["report_path"] = str(path)
                all_reports.append(report)

    if not args.quiet:
        print("")
        print("=" * 60)
        print(f"  BOSLY GOV CHECK RUN — tier: {args.tier}")
        print(f"  {len(all_reports)} check(s)")
        print("=" * 60)
        for r in all_reports:
            marker = "PASS" if r["status"] == "pass" else "FAIL"
            print(f"  [{marker}] {r['check_id']} ({r['duration_ms']}ms)")
        print("")

    passed = sum(1 for r in all_reports if r["status"] == "pass")
    failed = sum(1 for r in all_reports if r["status"] != "pass")

    if not args.quiet:
        print("=" * 60)
        print(f"  SUMMARY: {passed} passed, {failed} failed")
        print("=" * 60)
        print("")

    # Send one alert email if anything failed. Silently skip if there
    # was nothing to report. Failures in the alert path itself are
    # logged but do not change the exit code — the checks already ran.
    if failed > 0:
        try:
            failed_reports = [r for r in all_reports if r["status"] != "pass"]
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            reports_dir = str(REPORTS_ROOT / day)
            send_failure_alert(failed_reports, args.tier, reports_dir)
            if not args.quiet:
                print(f"  alert sent to configured recipient")
                print("")
        except Exception as e:
            print(f"  WARNING: could not send alert email: {e}", file=sys.stderr)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
