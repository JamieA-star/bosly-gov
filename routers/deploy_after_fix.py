#!/usr/bin/env python3
"""
Bosly Gov v4 - Deploy After Fix
Runs syntax check, build, and PM2 restart after a fix is approved.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path("/home/bosly_accord/bosly-1.0")


def run_syntax_check(file_paths: List[str]) -> Dict[str, Any]:
    """Run syntax check on changed files."""
    results = []
    all_ok = True
    for fp in file_paths:
        path = Path(fp)
        if not path.exists():
            results.append({"path": fp, "ok": False, "error": "File not found"})
            all_ok = False
            continue
        try:
            if path.suffix in (".ts", ".tsx", ".js"):
                # Use node -c for JS/TS files (ts files need esbuild or tsc)
                if path.suffix == ".ts" or path.suffix == ".tsx":
                    result = subprocess.run(
                        ["npx", "tsc", "--noEmit", "--skipLibCheck", fp],
                        capture_output=True, text=True, timeout=60,
                        cwd=str(PROJECT_ROOT)
                    )
                else:
                    result = subprocess.run(
                        ["node", "-c", fp],
                        capture_output=True, text=True, timeout=30
                    )
            elif path.suffix == ".py":
                result = subprocess.run(
                    ["python3", "-c", f"import ast; ast.parse(open('{fp}').read())"],
                    capture_output=True, text=True, timeout=30
                )
            else:
                results.append({"path": fp, "ok": True, "skipped": True, "note": "No syntax check for this file type"})
                continue

            if result.returncode == 0:
                results.append({"path": fp, "ok": True})
            else:
                results.append({"path": fp, "ok": False, "error": result.stderr[:500]})
                all_ok = False
        except subprocess.TimeoutExpired:
            results.append({"path": fp, "ok": False, "error": "Syntax check timed out"})
            all_ok = False
        except Exception as e:
            results.append({"path": fp, "ok": False, "error": str(e)})
            all_ok = False

    return {"ok": all_ok, "results": results}


def run_build(project_type: str = "nextjs") -> Dict[str, Any]:
    """Run the appropriate build command."""
    try:
        if project_type == "nextjs":
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True, text=True, timeout=300,
                cwd=str(PROJECT_ROOT),
                env={"PATH": "/home/bosly_accord/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin"}
            )
        else:
            return {"ok": True, "skipped": True, "note": f"No build step for {project_type}"}

        if result.returncode == 0:
            return {"ok": True, "output": result.stdout[-1000:]}
        else:
            return {"ok": False, "error": result.stderr[-2000:] or result.stdout[-2000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Build timed out (300s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def restart_pm2(process_name: str) -> Dict[str, Any]:
    """Restart a PM2 process."""
    try:
        result = subprocess.run(
            ["pm2", "restart", process_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return {"ok": True, "output": result.stdout[-500:]}
        else:
            return {"ok": False, "error": result.stderr or result.stdout}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_pm2_logs(process_name: str, lines: int = 10) -> Dict[str, Any]:
    """Check recent PM2 logs for errors."""
    try:
        result = subprocess.run(
            ["pm2", "logs", process_name, "--lines", str(lines), "--nostream"],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout + result.stderr
        has_error = "ERROR" in output or "Error" in output or "FATAL" in output
        return {"ok": not has_error, "output": output[-1000:], "has_error": has_error}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_smoke_test() -> Dict[str, Any]:
    """Run the Bosly smoke test script."""
    try:
        result = subprocess.run(
            ["/usr/local/bin/bosly-smoke-test"],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout
        # Parse pass/fail counts
        import re
        pass_match = re.search(r"Results: (\d+) pass, (\d+) fail", output)
        if pass_match:
            passes = int(pass_match.group(1))
            fails = int(pass_match.group(2))
            return {"ok": fails == 0, "passes": passes, "fails": fails, "output": output[-500:]}
        return {"ok": result.returncode == 0, "output": output[-500:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Smoke test timed out (60s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def deploy_after_approval(file_paths: List[str], process_name: str = "bosly", project_type: str = "nextjs") -> Dict[str, Any]:
    """Full deploy pipeline: syntax check -> build -> restart -> verify."""
    steps = {}

    # Step 1: Syntax check
    syntax = run_syntax_check(file_paths)
    steps["syntax"] = syntax
    if not syntax["ok"]:
        return {"ok": False, "stage": "syntax", "steps": steps, "error": "Syntax check failed"}

    # Step 2: Build
    build = run_build(project_type)
    steps["build"] = build
    if not build["ok"]:
        return {"ok": False, "stage": "build", "steps": steps, "error": "Build failed"}

    # Step 3: Restart
    restart = restart_pm2(process_name)
    steps["restart"] = restart
    if not restart["ok"]:
        return {"ok": False, "stage": "restart", "steps": steps, "error": "PM2 restart failed"}

    # Step 4: Check logs
    import time
    time.sleep(2)
    logs = check_pm2_logs(process_name)
    steps["logs"] = logs

    if not logs["ok"]:
        return {"ok": False, "stage": "logs", "steps": steps, "error": "Errors found in PM2 logs"}

    # Step 5: Smoke test
    smoke = run_smoke_test()
    steps["smoke"] = smoke

    return {
        "ok": smoke["ok"],
        "stage": "complete" if smoke["ok"] else "smoke",
        "steps": steps,
        "error": None if smoke["ok"] else f"Smoke test failed: {smoke.get('fails', '?')} failures",
    }
