#!/usr/bin/env python3
"""
Bosly Gov v4 — Workspace File Watcher (stdlib only, no watchdog needed)
Polls the workspace every 2 seconds for file changes.
"""

import json
import logging
import os
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone

WORKSPACE_ROOT = "/home/bosly_accord/bosly-1.0"
CONTEXT_PATH = "/tmp/bosly-context.json"
LOG_PATH = "/tmp/bosly-watcher.log"
WATCH_EXTENSIONS = {".tsx", ".ts", ".py", ".prisma", ".css", ".js", ".jsx"}
IGNORE_PARTS = ("node_modules", ".next", ".git", "prisma/migrations", "__pycache__", ".turbo", "dist", "build")
MAX_RECENT_FILES = 10
POLL_INTERVAL = 2  # seconds

def setup_logging():
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info("Bosly watcher starting (stdlib poll mode)...")

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def is_ignored(path):
    return any(part in path for part in IGNORE_PARTS)

def is_watched_file(path):
    if is_ignored(path): return False
    _, ext = os.path.splitext(path)
    return ext.lower() in WATCH_EXTENSIONS

def relpath(path):
    return os.path.relpath(path, WORKSPACE_ROOT).replace("\\", "/")

def safe_git(cmd):
    try:
        result = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else ""
    except: return ""

def get_git_branch():
    return safe_git(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"

def get_git_diff_summary():
    out = safe_git(["git", "diff", "--stat", "HEAD"])
    if not out: return "No local changes"
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return lines[-1] if lines else "No local changes"

def scan_workspace():
    """Walk the workspace and return {relpath: mtime} for all watched files."""
    files = {}
    try:
        for root, dirs, filenames in os.walk(WORKSPACE_ROOT):
            # Filter out ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORE_PARTS]
            for fname in filenames:
                fpath = os.path.join(root, fname)
                if is_watched_file(fpath):
                    try:
                        mtime = os.path.getmtime(fpath)
                        files[relpath(fpath)] = mtime
                    except OSError:
                        pass
    except Exception:
        pass
    return files

def write_context(current_file, recent_files):
    state = {
        "current_file": current_file,
        "recent_files": recent_files,
        "last_save": utc_now_iso(),
        "git_branch": get_git_branch(),
        "git_diff_summary": get_git_diff_summary(),
    }
    tmp = f"{CONTEXT_PATH}.tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, CONTEXT_PATH)

def main():
    setup_logging()
    os.makedirs(os.path.dirname(CONTEXT_PATH), exist_ok=True)

    # Initial scan
    previous = scan_workspace()
    recent_files = []
    logging.info("Initial scan: %d files watched", len(previous))

    stop_event = threading.Event()

    def _stop(signum=None, frame=None):
        logging.info("Stopping watcher...")
        stop_event.set()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    while not stop_event.is_set():
        time.sleep(POLL_INTERVAL)
        try:
            current = scan_workspace()
            # Find changed files (new or modified)
            changed = []
            for path, mtime in current.items():
                prev_mtime = previous.get(path)
                if prev_mtime is None or mtime > prev_mtime:
                    changed.append(path)

            if changed:
                # Sort by mtime, most recent first
                changed.sort(key=lambda p: current.get(p, 0), reverse=True)
                current_file = changed[0]

                # Update recent files list
                recent = [p for p in recent_files if p != current_file]
                recent.insert(0, current_file)
                recent_files = recent[:MAX_RECENT_FILES]

                write_context(current_file, recent_files)
                logging.info("Changed: %s -> %s", changed, current_file)

            previous = current
        except Exception as e:
            logging.exception("Error during scan: %s", e)

    logging.info("Bosly watcher stopped.")

if __name__ == "__main__":
    main()
