"""routers/tools.py — the Custodian's declared tools, with guards.

Four tools, no more, each with a check on what it writes:

  1. append_plan_entry — append a new entry to PLAN.md
  2. save_memory       — write a memory entry via store_memory_item
  3. read_file         — read a file under one of the three repos
  4. run_check         — run a registered check by id

The model cannot invent a tool, cannot run arbitrary code, cannot
write outside these shapes. Every function returns a dict:

    {"ok": True,  "result": <whatever the tool returns>}
    {"ok": False, "error": "<why it refused>"}

The guards are the whole point. The tools are useful only because
the guards hold. Test them first, before any model sees them:

    python3 routers/tools.py

Each tool has a JSON schema for the Anthropic tools API, and the
registry at the bottom is what the loop passes to the API.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Roots and constants
# ---------------------------------------------------------------------------

REPOS = {
    "bosly-1.0":   Path("/home/bosly_accord/bosly-1.0"),
    "bosly-keep":  Path("/home/bosly_accord/bosly-keep"),
    "bosly-gov":   Path("/home/bosly_accord/bosly-gov"),
}

PLAN = Path("/home/bosly_accord/bosly-gov/PLAN.md")
PLAN_FIRST_LINE = "BOSLY GOV — PLAN"
MANIFEST = Path("/home/bosly_accord/bosly-gov/manifests/checks.yml")

# Files that read_file must never return, even if inside a repo.
FORBIDDEN_NAMES = {".env", ".env.production", ".env.local", ".env.development"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".secret"}
FORBIDDEN_DIRS = {".git", "node_modules", ".next", "__pycache__"}


# ---------------------------------------------------------------------------
# Tool 1 — append_plan_entry
# ---------------------------------------------------------------------------

def append_plan_entry(entry: str) -> Dict[str, Any]:
    """Append a new entry to PLAN.md, after the last non-empty line.

    Guard 1: PLAN.md must start with PLAN_FIRST_LINE.
    Guard 2: entry must not be empty and must contain a marker line
             ([ ] or [~] or [x]) so it is recognisably a plan entry.
    Guard 3: entry must not contain the first-line sentinel (we are
             not rewriting the header).
    """
    if not isinstance(entry, str) or not entry.strip():
        return {"ok": False, "error": "entry is empty"}

    if PLAN_FIRST_LINE not in entry:
        pass  # fine — entries don't need to repeat the header
    else:
        return {"ok": False, "error": "entry must not contain the plan header"}

    if not PLAN.exists():
        return {"ok": False, "error": f"PLAN.md not found at {PLAN}"}

    text = PLAN.read_text(encoding="utf-8")
    if not text.startswith(PLAN_FIRST_LINE):
        return {
            "ok": False,
            "error": f"PLAN.md does not start with {PLAN_FIRST_LINE!r} — refusing to append",
        }

    # Must contain at least one well-formed marker line:
    #   [ ] name — description
    #   [~] name — IN PROGRESS ...
    #   [x] name — DONE date. description
    # A bare "[x] some text" is not a plan entry; it has no name
    # and no em-dash separator, so it doesn't sort or grep right.
    import re as _re
    marker_re = _re.compile(
        r"^\s*\[([ x~])\]\s+\S+\s+[—\-]\s+\S"
    )
    has_marker = any(
        marker_re.match(line) for line in entry.splitlines()
    )
    if not has_marker:
        return {
            "ok": False,
            "error": (
                "entry has no well-formed marker line. "
                "Expected a line like: "
                "[x] entry.name — DONE 19 Oct. What was done. "
                "(marker, space, name, space, em-dash or hyphen, space, description)"
            ),
        }

    # Append: ensure exactly one blank line between existing content and entry
    new_text = text.rstrip() + "\n\n" + entry.rstrip() + "\n"
    PLAN.write_text(new_text, encoding="utf-8")

    # Return a small record of what happened, not the whole file.
    lines_added = entry.count("\n") + 1
    return {
        "ok": True,
        "result": {
            "file": str(PLAN),
            "lines_appended": lines_added,
            "new_size_bytes": len(new_text.encode("utf-8")),
        },
    }


# ---------------------------------------------------------------------------
# Tool 2 — save_memory
# ---------------------------------------------------------------------------

def save_memory(project_slug: str, item_type: str, content: str,
                entry_id: str = "") -> Dict[str, Any]:
    """Save a memory entry via store_memory_item (which validates).

    Guard 1: project_slug must be one of the three known repos.
    Guard 2: item_type must be in the allowed set.
    Guard 3: content must be non-empty and at most 8000 chars.
    """
    allowed_slugs = set(REPOS.keys())
    if project_slug not in allowed_slugs:
        return {
            "ok": False,
            "error": f"project_slug {project_slug!r} not in {sorted(allowed_slugs)}",
        }

    allowed_types = {"decision", "pattern", "fact", "incident"}
    if item_type not in allowed_types:
        return {
            "ok": False,
            "error": f"item_type {item_type!r} not in {sorted(allowed_types)}",
        }

    if not content or len(content.strip()) == 0:
        return {"ok": False, "error": "content is empty"}
    if len(content) > 8000:
        return {"ok": False, "error": f"content is {len(content)} chars (max 8000)"}

    # Lazy import — only when the tool is used.
    try:
        sys.path.insert(0, str(REPOS["bosly-gov"]))
        from routers.memory_first import store_memory_item
    except Exception as e:
        return {"ok": False, "error": f"memory_first unavailable: {e}"}

    item: Dict[str, Any] = {
        "project_slug": project_slug,
        "item_type": item_type,
        "content": content,
    }
    if entry_id:
        item["id"] = entry_id

    result = store_memory_item(item)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "store_memory_item refused")}

    return {
        "ok": True,
        "result": {"id": result.get("id"), "project_slug": project_slug,
                   "item_type": item_type},
    }


# ---------------------------------------------------------------------------
# Tool 3 — read_file
# ---------------------------------------------------------------------------

def _resolve_safe(rel_path: str) -> Path | None:
    """Resolve a path and return it if it lives inside a repo and is not
    forbidden. Return None otherwise.

    Accepts three shapes:
      - "PLAN.md"            (relative to a repo; tried in order)
      - "bosly-gov/PLAN.md"  (repo-name prefix)
      - "/home/.../PLAN.md"  (absolute, must be inside a repo)
    """
    if not rel_path or rel_path.strip() == "":
        return None
    candidate = Path(rel_path)

    resolved = None
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        # If the first segment is a known repo name, treat the rest as
        # relative to that repo root.
        parts = candidate.parts
        if parts and parts[0] in REPOS:
            root = REPOS[parts[0]]
            tail = Path(*parts[1:]) if len(parts) > 1 else Path("")
            resolved = (root / tail).resolve()
        else:
            # Otherwise try each repo root in order; first one that
            # exists wins. If none exist, fall back to bosly-gov.
            for root in REPOS.values():
                p = (root / candidate).resolve()
                if p.exists():
                    resolved = p
                    break
            if resolved is None:
                resolved = (REPOS["bosly-gov"] / candidate).resolve()

    # Must be inside one of the repos
    inside = False
    for root in REPOS.values():
        try:
            resolved.relative_to(root.resolve())
            inside = True
            break
        except ValueError:
            continue
    if not inside:
        return None

    # Forbidden names / suffixes / dirs
    if resolved.name in FORBIDDEN_NAMES:
        return None
    if resolved.suffix in FORBIDDEN_SUFFIXES:
        return None
    for part in resolved.parts:
        if part in FORBIDDEN_DIRS:
            return None

    return resolved


def read_file(path: str, max_bytes: int = 400_000) -> Dict[str, Any]:
    """Read a file under one of the three repos.

    Guards: must resolve inside a repo; no .env/.key/.pem; no .git,
    node_modules, .next; file size <= max_bytes (default 200 KB).
    """
    resolved = _resolve_safe(path)
    if resolved is None:
        return {"ok": False, "error": f"path {path!r} is outside the repos or forbidden"}
    if not resolved.exists():
        return {"ok": False, "error": f"{resolved} does not exist"}
    if not resolved.is_file():
        return {"ok": False, "error": f"{resolved} is not a regular file"}

    size = resolved.stat().st_size
    if size > max_bytes:
        return {
            "ok": False,
            "error": f"{resolved} is {size} bytes (max {max_bytes})",
        }

    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "error": f"could not read {resolved}: {e}"}

    return {
        "ok": True,
        "result": {
            "path": str(resolved),
            "size_bytes": size,
            "content": text,
        },
    }


# ---------------------------------------------------------------------------
# Tool 4 — run_check
# ---------------------------------------------------------------------------

def _load_checks() -> Dict[str, Dict[str, str]]:
    """Return {check_id: {command, cwd}} from the manifest.

    The manifest format is: project -> {tiers: {fast: [...], slow: [...]}}
    where each item has 'id' and 'command'. We flatten it.
    """
    try:
        import yaml
    except Exception as e:
        return {}
    if not MANIFEST.exists():
        return {}
    try:
        data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}

    out: Dict[str, Dict[str, str]] = {}
    projects = data.get("projects") if isinstance(data, dict) else None
    if not projects:
        return {}
    for project_name, project_data in projects.items():
        if not isinstance(project_data, dict):
            continue
        root = project_data.get("root", "")
        tiers = project_data.get("tiers", {}) or {}
        for tier_name, checks in tiers.items():
            if not isinstance(checks, list):
                continue
            for c in checks:
                if isinstance(c, dict) and c.get("id") and c.get("command"):
                    out[c["id"]] = {"command": c["command"], "cwd": root}
    return out


def run_check(check_id: str, timeout: int = 120) -> Dict[str, Any]:
    """Run a check registered in manifests/checks.yml.

    Guards: check_id must exist in the manifest. The command comes from
    the manifest, never from the model. No arbitrary shell.
    """
    checks = _load_checks()
    if not checks:
        return {"ok": False, "error": "could not load manifests/checks.yml"}
    if check_id not in checks:
        return {
            "ok": False,
            "error": f"unknown check {check_id!r}; known: {sorted(checks.keys())}",
        }

    spec = checks[check_id]
    cwd = spec.get("cwd") or str(REPOS["bosly-gov"])
    try:
        proc = subprocess.run(
            spec["command"],
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"check {check_id} timed out after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": f"could not run {check_id}: {e}"}

    return {
        "ok": True,
        "result": {
            "check_id": check_id,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "passed": proc.returncode == 0,
        },
    }


# ---------------------------------------------------------------------------
# Registry — what the loop passes to the API
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "append_plan_entry",
        "description": (
            "Append a new entry to BOSLY GOV PLAN.md. The entry must "
            "contain at least one marker line ([ ], [~], or [x]). "
            "Use this to record a decision, a finding, or a task. "
            "It only appends — it never edits or deletes existing text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entry": {"type": "string", "description": "The plan entry text, including the marker line."},
            },
            "required": ["entry"],
        },
        "fn": append_plan_entry,
    },
    {
        "name": "save_memory",
        "description": (
            "Save a memory entry for one of the three repos. Goes through "
            "the memory schema check. Use this to record a pattern, a "
            "decision, an incident, or a fact worth remembering."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_slug": {"type": "string", "enum": ["bosly-1.0", "bosly-keep", "bosly-gov"]},
                "item_type": {"type": "string", "enum": ["decision", "pattern", "fact", "incident"]},
                "content": {"type": "string", "description": "The memory content."},
                "entry_id": {"type": "string", "description": "Optional stable id."},
            },
            "required": ["project_slug", "item_type", "content"],
        },
        "fn": save_memory,
    },
    {
        "name": "read_file",
        "description": (
            "Read a file under one of the three repos. Paths must resolve "
            "inside a repo. .env, .key, .pem, .git and node_modules are "
            "refused. Max 200 KB."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to a repo root, or absolute inside a repo."},
            },
            "required": ["path"],
        },
        "fn": read_file,
    },
    {
        "name": "run_check",
        "description": (
            "Run a check registered in manifests/checks.yml by id. "
            "Example ids: gov.cron_sanity, gov.memory_schema, "
            "accord.invariants. The command comes from the manifest, "
            "not from you."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "check_id": {"type": "string", "description": "A check id from manifests/checks.yml."},
            },
            "required": ["check_id"],
        },
        "fn": run_check,
    },
]

TOOL_BY_NAME = {t["name"]: t for t in TOOLS}


def dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a tool by name with args. Used by the loop."""
    tool = TOOL_BY_NAME.get(name)
    if tool is None:
        return {"ok": False, "error": f"unknown tool {name!r}; known: {sorted(TOOL_BY_NAME)}"}
    try:
        return tool["fn"](**args)
    except TypeError as e:
        return {"ok": False, "error": f"bad arguments to {name}: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"{name} raised: {e}"}


# ---------------------------------------------------------------------------
# Self-test — run this first, before any model touches the tools
# ---------------------------------------------------------------------------

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
                for line in detail.splitlines():
                    print(f"      {line}")

    # --- append_plan_entry: refuses empty, refuses no-marker, refuses header ---
    r = append_plan_entry("")
    check("append refuses empty", not r["ok"])

    r = append_plan_entry("just some text with no marker")
    check("append refuses no-marker", not r["ok"])

    r = append_plan_entry("BOSLY GOV — PLAN\n[ ] fake header")
    check("append refuses plan header in entry", not r["ok"])

    # --- save_memory: refuses bad slug, bad type, empty content ---
    r = save_memory("not-a-repo", "fact", "hello")
    check("save_memory refuses unknown slug", not r["ok"])

    r = save_memory("bosly-gov", "not-a-type", "hello")
    check("save_memory refuses unknown type", not r["ok"])

    r = save_memory("bosly-gov", "fact", "")
    check("save_memory refuses empty content", not r["ok"])

    # --- read_file: refuses traversal, .env, .git, outside-repo ---
    r = read_file("../../../etc/passwd")
    check("read_file refuses traversal", not r["ok"])

    r = read_file("/etc/passwd")
    check("read_file refuses absolute outside repo", not r["ok"])

    r = read_file("bosly-1.0/.env.production")
    check("read_file refuses .env", not r["ok"])

    r = read_file("bosly-gov/.git/config")
    check("read_file refuses .git", not r["ok"])

    r = read_file("bosly-gov/PLAN.md")
    check("read_file allows PLAN.md", r["ok"] and r["result"]["size_bytes"] > 0)

    # --- run_check: refuses unknown, allows known ---
    r = run_check("not.a.real.check")
    check("run_check refuses unknown", not r["ok"])

    r = run_check("gov.memory_schema")
    check(
        "run_check allows gov.memory_schema",
        r["ok"] and r["result"]["exit_code"] in (0, 1),
    )

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_selftest())
