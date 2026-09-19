#!/usr/bin/env python3
"""
Check: secrets are not exposed.

Four assertions across the Bosly server:
  1. .env.production exists and is mode 600
  2. No .env files in web-accessible directories (public/)
  3. No secrets leaked into PM2 logs
  4. No .env files tracked by git (except .env.example)

Replaces the retired /usr/local/bin/bosly-secrets script, which
had stale paths and wasn't scheduled anywhere.

Exit 0 if all assertions hold, 1 otherwise.

Run:
    python3 checks/secrets_audit.py
"""

import subprocess
import sys
from pathlib import Path

ACCORD = Path("/home/bosly_accord/bosly-1.0")
KEEP = Path("/home/bosly_accord/bosly-keep")
GOV = Path("/home/bosly_accord/bosly-gov")
PM2_LOGS = Path("/home/bosly_accord/.pm2/logs")

# Patterns that indicate a leaked secret in a log file
SECRET_PATTERNS = [
    "SMTP_PASS=",
    "ENCRYPTION_KEY=",
    "CLAUDE_API_KEY=",
    "OPENAI_API_KEY=",
    "STRIPE_SECRET_KEY=",
    "DATABASE_URL=postgres",
    "BOSLY_SERVER_KEY=",
    "BOSLY_AUTH_SECRET=",
]

passed = 0
failed = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


def check_env_permissions() -> None:
    env = ACCORD / ".env.production"
    if not env.exists():
        check(".env.production exists", False, str(env))
        return
    mode = oct(env.stat().st_mode)[-3:]
    check(
        ".env.production mode is 600",
        mode == "600",
        f"mode is {mode}, should be 600",
    )


def check_no_public_env() -> None:
    public = ACCORD / "public"
    if not public.exists():
        check("no .env in public/", True)
        return
    found = [p.name for p in public.rglob(".env*") if p.is_file()]
    check(
        "no .env in public/",
        len(found) == 0,
        f"found: {', '.join(found)}",
    )


def check_pm2_logs() -> None:
    if not PM2_LOGS.exists():
        check("PM2 logs scanned", True)
        return
    hits: list[str] = []
    for log in PM2_LOGS.glob("*.log"):
        try:
            text = log.read_text(errors="ignore")
        except Exception:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern in text:
                hits.append(f"{log.name}:{pattern}")
                break
    check(
        "no secrets in PM2 logs",
        len(hits) == 0,
        f"{len(hits)} hits: {', '.join(hits[:3])}",
    )


def check_no_git_secrets() -> None:
    hits: list[str] = []
    for repo in (ACCORD, KEEP, GOV):
        if not (repo / ".git").exists():
            continue
        try:
            out = subprocess.run(
                ["git", "ls-files"],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout
        except Exception:
            continue
        for line in out.split("\n"):
            name = Path(line).name
            if name.startswith(".env") and name != ".env.example":
                hits.append(f"{repo.name}/{line}")
    check(
        "no .env files tracked by git",
        len(hits) == 0,
        f"found: {', '.join(hits)}",
    )


def main() -> int:
    print("")
    print("Invariant: secrets are not exposed")
    print("-" * 52)
    print("")

    check_env_permissions()
    check_no_public_env()
    check_pm2_logs()
    check_no_git_secrets()

    print("")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
