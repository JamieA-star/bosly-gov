"""A build's deploy restarts Accord, never Gov, and is gated by the smoke test.

Reads deploy_after_fix for the two things that must be true, and hits the
live liveness endpoint. It does not restart anything: a check that restarts
a process on every tier run is a check that makes the server flaky.
"""
import pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "routers" / "deploy_after_fix.py"
SMOKE_URL = "http://localhost:3100/api/health/smoke"

def main() -> int:
    ok = True
    s = SRC.read_text()

    # 1. The deploy defaults to Accord, never Gov.
    m = re.search(r'def deploy_after_approval\([^)]*process_name:\s*str\s*=\s*"([^"]+)"', s)
    target = m.group(1) if m else None
    good = target == "bosly"
    print(f"  deploy defaults to Accord (bosly), not Gov: {good}  (default={target!r})")
    ok = ok and good

    # 2. 'bosly-gov' does not appear as a process name anywhere in the file.
    bad = "bosly-gov" in s
    print(f"  'bosly-gov' absent from deploy code: {not bad}")
    ok = ok and (not bad)

    # 3. The pipeline runs the smoke and gates on it.
    good = "run_smoke_test" in s and '"smoke"' in s
    print(f"  deploy pipeline is smoke-gated: {good}")
    ok = ok and good

    # 4. The live smoke endpoint says pass.
    try:
        body = urllib.request.urlopen(SMOKE_URL, timeout=5).read().decode()
        good = '"status":"pass"' in body
        detail = body[:80]
    except Exception as e:
        good, detail = False, str(e)
    print(f"  live /api/health/smoke passes: {good}  ({detail})")
    ok = ok and good

    print("")
    print("SUMMARY: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
