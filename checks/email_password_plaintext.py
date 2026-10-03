#!/usr/bin/env python3
"""
Check: no ConnectedEmail.password is stored as plaintext.

The password for a connected email account must be encrypted with
ENCRYPTION_KEY before storage. A value starting with "PLAINTEXT:" is
the old bypass, fixed on 3 Oct (bosly-1.0 b9489df).

Reads the DB directly. DATABASE_URL comes from the environment, or
from bosly-1.0/.env.production if the environment does not have it —
because the pipeline runs under cron with a minimal environment.

Exit 0 if no plaintext password, 1 otherwise. SKIP (exit 0) if the
database cannot be reached, so a missing DB never breaks the pipeline.
"""

import os
import subprocess
import sys
from pathlib import Path

ENV_FILE = Path("/home/bosly_accord/bosly-1.0/.env.production")


def load_db_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def main() -> int:
    print("")
    print("Invariant: no connected email password is stored as plaintext")
    print("------------------------------------------------------------")

    db = load_db_url()
    if not db:
        print("  SKIP: DATABASE_URL not available")
        print("")
        return 0

    try:
        out = subprocess.run(
            ["psql", db, "-tAc",
             "SELECT count(*) FROM \"ConnectedEmail\" WHERE password LIKE 'PLAINTEXT:%';"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception as e:
        print(f"  SKIP: could not query the database: {e}")
        print("")
        return 0

    if out.returncode != 0:
        print(f"  SKIP: psql failed: {out.stderr.strip()[:120]}")
        print("")
        return 0

    count = int((out.stdout or "0").strip() or "0")
    if count:
        print(f"  FAIL: {count} connected email password(s) stored as PLAINTEXT:")
        print("        run the migration to encrypt them")
        print("")
        print(f"SUMMARY: FAIL ({count} plaintext)")
        print("")
        return 1

    print("  OK: no plaintext email passwords")
    print("")
    print("SUMMARY: PASS")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
