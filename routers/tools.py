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
from datetime import date, timedelta, datetime as _dt
from zoneinfo import ZoneInfo
from typing import Any, Dict

# Make "from routers.things import ..." work when this file is run
# directly (python3 routers/tools.py) — sys.path[0] is routers/ then,
# not the repo root.
import sys as _sys
_sys.path.insert(0, "/home/bosly_accord/bosly-gov")

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

# The founder's own address. send_draft_to_me can only send here — it
# is not a parameter, so the tool cannot be talked into emailing anyone
# else. That is the guard.
FOUNDER_EMAIL = "jr-arnott@outlook.com"


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
# Tools 4a/4b — write_file and patch_file
# ---------------------------------------------------------------------------

def write_file(path: str, content: str) -> Dict[str, Any]:
    """Write a file under one of the three repos.

    Guards: must resolve inside a repo; no .env/.key/.pem; no .git,
    node_modules, .next (the same resolver as read_file). A .bak is
    written before the change.
    """
    resolved = _resolve_safe(path)
    if resolved is None:
        return {"ok": False, "error": f"path {path!r} is outside the repos or forbidden"}
    if resolved.exists() and not resolved.is_file():
        return {"ok": False, "error": f"{resolved} is not a regular file"}
    if resolved.exists():
        try:
            resolved.with_suffix(resolved.suffix + ".bak-write").write_text(
                resolved.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception as e:
            return {"ok": False, "error": f"could not back up {resolved}: {e}"}
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"could not write {resolved}: {e}"}
    return {"ok": True, "result": {"path": str(resolved), "bytes": len(content.encode("utf-8"))}}


def patch_file(path: str, anchor: str, replacement: str) -> Dict[str, Any]:
    """Replace ONE occurrence of anchor with replacement.

    Aborts if the anchor is not found exactly once — never a partial
    edit. A .bak is written before the change. This is the tool the
    butler uses to patch the code.
    """
    resolved = _resolve_safe(path)
    if resolved is None:
        return {"ok": False, "error": f"path {path!r} is outside the repos or forbidden"}
    if not resolved.is_file():
        return {"ok": False, "error": f"{resolved} is not a regular file"}
    try:
        src = resolved.read_text(encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"could not read {resolved}: {e}"}
    n = src.count(anchor)
    if n != 1:
        return {"ok": False, "error": f"anchor found {n} times, expected 1 — aborting, nothing changed"}
    try:
        resolved.with_suffix(resolved.suffix + ".bak-patch").write_text(src, encoding="utf-8")
        resolved.write_text(src.replace(anchor, replacement, 1), encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"could not write {resolved}: {e}"}
    return {"ok": True, "result": {"path": str(resolved), "replaced": True}}


# ---------------------------------------------------------------------------
# Tool 5 — run_check
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

# ---------------------------------------------------------------------------
# The business memory tools (routers/things.py). Same guards as the four
# Custodian tools: the model cannot invent a store, only use the declared
# operations.
# ---------------------------------------------------------------------------
try:
    from routers.things import (
        save_thing as _save_thing_impl,
        read_thing as _read_thing_impl,
        find_things as _find_things_impl,
        link_things as _link_things_impl,
    )
except Exception as _things_import_error:
    _save_thing_impl = None
    _read_thing_impl = None
    _find_things_impl = None
    _link_things_impl = None


# ---------------------------------------------------------------------------
# Tool wrappers for the business memory. Each returns {ok, result|error}
# exactly like the four Custodian tools, so the loop does not care which
# family a tool belongs to.
# ---------------------------------------------------------------------------

def save_thing(kind: str, title: str, body: str = "",
               status: str = "active", tags: str = "",
               thing_id: str = "") -> Dict[str, Any]:
    if _save_thing_impl is None:
        return {"ok": False, "error": "things store unavailable"}
    try:
        return _save_thing_impl(
            kind=kind, title=title, body=body,
            status=status, tags=tags,
            thing_id=thing_id or None,
        )
    except Exception as e:
        return {"ok": False, "error": f"save_thing raised: {e}"}


def read_thing(thing_id: str) -> Dict[str, Any]:
    if _read_thing_impl is None:
        return {"ok": False, "error": "things store unavailable"}
    try:
        return _read_thing_impl(thing_id=thing_id)
    except Exception as e:
        return {"ok": False, "error": f"read_thing raised: {e}"}


def find_things(kind: str = "", status: str = "",
                query: str = "", limit: int = 50) -> Dict[str, Any]:
    if _find_things_impl is None:
        return {"ok": False, "error": "things store unavailable"}
    try:
        return _find_things_impl(
            kind=kind or None, status=status or None,
            query=query or None, limit=int(limit) if limit else 50,
        )
    except Exception as e:
        return {"ok": False, "error": f"find_things raised: {e}"}


def link_things(from_id: str, to_id: str,
                relation: str = "related") -> Dict[str, Any]:
    if _link_things_impl is None:
        return {"ok": False, "error": "things store unavailable"}
    try:
        return _link_things_impl(from_id=from_id, to_id=to_id, relation=relation)
    except Exception as e:
        return {"ok": False, "error": f"link_things raised: {e}"}


# ---------------------------------------------------------------------------
# Draft tools. draft_email structures a draft; send_draft_to_me sends it
# to the founder's own address (hardcoded) so it can be read on a phone.
# Neither sends to a client. send_email to a client is a separate,
# guarded tool that requires explicit approval.
# ---------------------------------------------------------------------------

def draft_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Structure a draft email. Does not send.

    The draft is returned as a record so the loop can show it, and so
    a later tool (send_email) can take it. Guards: to is non-empty,
    subject is non-empty, body is under 50 KB.
    """
    if not to or "@" not in str(to):
        return {"ok": False, "error": "draft_email: 'to' must be an email address"}
    if not subject or not str(subject).strip():
        return {"ok": False, "error": "draft_email: 'subject' is required"}
    if not body or not str(body).strip():
        return {"ok": False, "error": "draft_email: 'body' is empty"}
    if len(body) > 50_000:
        return {"ok": False, "error": f"draft_email: body is {len(body)} chars (max 50000)"}

    to_clean = str(to).strip()
    subject_clean = str(subject).strip()
    body_clean = str(body)

    # Persist the draft as a thing so the next turn can find it.
    # The draft is a thing of kind "draft"; the recipient goes in the
    # tags as "to:<address>". If the save fails, the draft still
    # returns — it is better to have a draft that is not saved than
    # to lose the draft because the store is unhappy.
    thing_id = ""
    try:
        saved = _save_thing_impl(
            kind="draft",
            title=subject_clean,
            body=body_clean,
            status="active",
            tags=f"to:{to_clean},draft-email",
        )
        if saved.get("ok"):
            thing_id = saved["result"]["id"]
    except Exception:
        pass

    return {
        "ok": True,
        "result": {
            "to": to_clean,
            "subject": subject_clean,
            "body": body_clean,
            "char_count": len(body_clean),
            "thing_id": thing_id,
            "saved_as_thing": bool(thing_id),
        },
    }


def send_draft_to_me(subject: str, body: str, note: str = "") -> Dict[str, Any]:
    """Email the draft to the founder so it can be read on a phone.

    The recipient is FOUNDER_EMAIL, hardcoded. The tool cannot send to
    anyone else. The subject gets a [DRAFT] prefix so it is not mistaken
    for a sent email.
    """
    if not subject or not str(subject).strip():
        return {"ok": False, "error": "send_draft_to_me: 'subject' is required"}
    if not body or not str(body).strip():
        return {"ok": False, "error": "send_draft_to_me: 'body' is empty"}
    if len(body) > 100_000:
        return {"ok": False, "error": f"send_draft_to_me: body is {len(body)} chars (max 100000)"}

    try:
        from lib.alert import send_email
    except Exception as e:
        return {"ok": False, "error": f"mailer unavailable: {e}"}

    full_subject = f"[DRAFT] {str(subject).strip()}"
    NL = chr(10)
    note_line = (str(note).strip() + NL) if note else ""
    full_body = (
        "This is a draft. It has NOT been sent to anyone." + NL
        + note_line
        + NL + "---" + NL + NL
        + str(body)
        + NL + NL + "---" + NL
        + "Sent by the Executive so you can read it away from the desk."
    )

    try:
        send_email(to=FOUNDER_EMAIL, subject=full_subject, body=full_body)
    except Exception as e:
        return {"ok": False, "error": f"send failed: {e}"}

    return {
        "ok": True,
        "result": {
            "to": FOUNDER_EMAIL,
            "subject": full_subject,
            "sent": True,
        },
    }


# ---------------------------------------------------------------------------
# The scout tool. Runs scripts/lead_scout.py with a validated category
# and area, reads the CSV it writes, and returns the rows. The model
# names the job; the tool runs the script. No shell, no free-form args.
# ---------------------------------------------------------------------------

SCOUT_SCRIPT = Path("/home/bosly_accord/bosly-gov/scripts/lead_scout.py")
SCOUT_CSV = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout.csv")

# The categories the script knows. Kept in sync with
# scripts/lead_scout.py CATEGORY_TAGS. If the script gains a
# category, add it here too — the tool refuses anything not listed.
SCOUT_CATEGORIES = {
    "hairdresser", "barber", "beauty", "cafe", "restaurant", "pub",
    "bakery", "butcher", "florist", "plumber", "electrician", "gardener",
}


def run_lead_scout(category: str, area: str, timeout: int = 300) -> Dict[str, Any]:
    """Run scripts/lead_scout.py, then read and return the CSV.

    Guards:
      - category must be in SCOUT_CATEGORIES
      - area must be a plain string, max 80 chars, no shell metacharacters
      - the script is invoked with a fixed argv shape — the model cannot
        add flags or change the output path
    The output path is fixed (SCOUT_CSV) so the pickup can find it.
    """
    category = (category or "").strip().lower()
    area = (area or "").strip()

    if category not in SCOUT_CATEGORIES:
        return {
            "ok": False,
            "error": f"category {category!r} not in {sorted(SCOUT_CATEGORIES)}",
        }
    if not area:
        return {"ok": False, "error": "area is required (a town name or postcode)"}
    if len(area) > 80:
        return {"ok": False, "error": f"area is {len(area)} chars (max 80)"}
    # No shell metacharacters: this argument goes into an argv list, but
    # be strict anyway — an area is a name or a postcode.
    import re as _re
    if not _re.match(r"^[A-Za-z0-9][A-Za-z0-9 ,.\-'/]*$", area):
        return {
            "ok": False,
            "error": "area must be a plain place name or postcode (letters, digits, spaces, commas, hyphens, apostrophes)",
        }
    if not SCOUT_SCRIPT.exists():
        return {"ok": False, "error": f"scout script not found at {SCOUT_SCRIPT}"}

    import subprocess as _sp
    import json as _json
    import tempfile as _tempfile

    # The script sweeps a list of areas from a config file; the category
    # is not a config key — the script sweeps its map, and the tool
    # filters the result. Write a one-area config, run --config.
    cfg = {"areas": [area], "output": str(SCOUT_CSV)}
    tmp = _tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(_json.dumps(cfg))
        tmp.close()
        try:
            proc = _sp.run(
                ["python3", str(SCOUT_SCRIPT), "--config", tmp.name],
                capture_output=True, text=True, timeout=timeout,
            )
        except _sp.TimeoutExpired:
            return {"ok": False, "error": f"scout timed out after {timeout}s"}
        except Exception as e:
            return {"ok": False, "error": f"could not run the scout: {e}"}
    finally:
        try:
            Path(tmp.name).unlink()
        except Exception:
            pass

    # The script writes its progress to stdout and its errors (via
    # SystemExit) to stderr. A non-zero exit with 'mirrors failed' in
    # stderr means the endpoint is down — say so honestly.
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": "scout failed — endpoint problem, not a zero result. "
                     + (proc.stderr or proc.stdout or "")[:800],
        }

    # Read the CSV
    import csv as _csv
    if not SCOUT_CSV.exists():
        return {"ok": False, "error": f"scout ran but wrote no CSV at {SCOUT_CSV}"}
    try:
        with SCOUT_CSV.open(encoding="utf-8", newline="") as f:
            rows = [dict(r) for r in _csv.DictReader(f)]
    except Exception as e:
        return {"ok": False, "error": f"could not read the scout CSV: {e}"}

    # The script sweeps every category in its map; the tool's category is
    # a filter on the result. The category argument is honoured, and the
    # script's interface is untouched.
    if category:
        rows = [r for r in rows if (r.get("category") or "").strip().lower() == category]

    return {
        "ok": True,
        "result": {
            "category": category,
            "area": area,
            "csv_path": str(SCOUT_CSV),
            "count": len(rows),
            "rows": rows,
            "stdout": (proc.stdout or "")[-1000:],
        },
    }


# ---------------------------------------------------------------------------
# The guarded client send. This is the tool that emails a real person.
# The guard is `confirmed`: the model must pass True, which means "the
# founder said yes". The prompt tells the model never to set it without
# an explicit yes. Every send is logged.
# ---------------------------------------------------------------------------

EMAIL_LOG = Path("/mnt/bosly/bosly-data/.data/governor/email-sends.jsonl")


def send_email(
    to: str,
    subject: str,
    body: str,
    confirmed: bool = False,
    draft_thing_id: str = "",
) -> Dict[str, Any]:
    """Send an email to a client. Requires confirmed=True.

    Guards:
      - confirmed must be True — the model must not send without an
        explicit yes from the founder
      - to must be a valid email address (has @ and a dot after it)
      - to must NOT be the founder's own address — that is what
        send_draft_to_me is for
      - subject and body are required, body under 50 KB
    Every send is appended to EMAIL_LOG as a JSON line.
    """
    if confirmed is not True:
        return {
            "ok": False,
            "error": (
                "send_email requires confirmed=True. Ask the founder "
                "explicitly ('send it to X?') and only call this tool "
                "with confirmed=True after they say yes."
            ),
        }

    # If the model passes the draft's thing_id, use the saved draft.
    if draft_thing_id and _read_thing_impl is not None:
        try:
            got = _read_thing_impl(thing_id=draft_thing_id)
        except Exception as e:
            return {"ok": False, "error": f"could not read draft {draft_thing_id!r}: {e}"}
        if not got.get("ok"):
            return {"ok": False, "error": f"draft {draft_thing_id!r} not found"}
        thing = got["result"]
        if thing.get("kind") != "draft":
            return {"ok": False, "error": f"thing {draft_thing_id!r} is not a draft"}
        subject = thing.get("title") or subject
        body = thing.get("body") or body
        # The 'to' is stored as a tag 'to:<address>'. If the caller did
        # not pass 'to', extract it from the tags.
        if not (to or "").strip():
            for tag in (thing.get("tags") or "").split(","):
                if tag.startswith("to:"):
                    to = tag[3:]
                    break

    to = (to or "").strip()
    subject = (subject or "").strip()
    body = body or ""

    if not to or "@" not in to or "." not in to.split("@")[-1]:
        return {"ok": False, "error": f"send_email: {to!r} is not a valid email address"}
    if to.lower() == FOUNDER_EMAIL.lower():
        return {
            "ok": False,
            "error": (
                "send_email refuses the founder's own address — use "
                "send_draft_to_me for that. send_email is for clients."
            ),
        }
    if not subject:
        return {"ok": False, "error": "send_email: subject is required"}
    if not body.strip():
        return {"ok": False, "error": "send_email: body is empty"}
    if len(body) > 50_000:
        return {"ok": False, "error": f"send_email: body is {len(body)} chars (max 50000)"}

    try:
        from lib.alert import send_email as _send
    except Exception as e:
        return {"ok": False, "error": f"mailer unavailable: {e}"}

    import json as _json, time as _time

    def _log(status: str, detail: str) -> None:
        try:
            EMAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
            with EMAIL_LOG.open("a", encoding="utf-8") as f:
                f.write(_json.dumps({
                    "ts": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
                    "to": to,
                    "subject": subject,
                    "body_chars": len(body),
                    "body": body,
                    "status": status,
                    "detail": detail,
                }) + "\n")
        except Exception:
            pass  # logging is best-effort

    try:
        _send(to=to, subject=subject, body=body)
    except Exception as e:
        _log("failed", str(e)[:500])
        return {"ok": False, "error": f"send failed: {e}"}

    _log("sent", "")
    return {
        "ok": True,
        "result": {"to": to, "subject": subject, "sent": True},
    }


# ---------------------------------------------------------------------------
# read_leads — this week's ranked shortlist, as structured rows.
# The path is fixed. The model asks for "this week's leads" and gets
# the rows; it does not pass a path, so it cannot read the log or the
# state or anything else in the governor directory.
# ---------------------------------------------------------------------------

LEADS_CSV = Path("/mnt/bosly/bosly-data/.data/governor/lead-scout-ranked.csv")


def read_leads(only_call_list: bool = False, limit: int = 15) -> Dict[str, Any]:
    """Read the ranked lead shortlist.

    Guards: fixed path; only_call_list is a bool; limit is 1-50.
    Returns the rows as dicts, in ranked order.
    """
    if not LEADS_CSV.exists():
        return {
            "ok": False,
            "error": (
                "no ranked lead file yet — the Saturday sweep may not "
                "have run, or the ranker has not written it"
            ),
        }
    if limit < 1 or limit > 50:
        return {"ok": False, "error": "limit must be 1-50"}
    try:
        import csv as _csv
        with LEADS_CSV.open(newline="", encoding="utf-8") as f:
            rows = [dict(r) for r in _csv.DictReader(f)]
    except Exception as e:
        return {"ok": False, "error": f"could not read leads: {e}"}

    if only_call_list:
        rows = [r for r in rows if (r.get("call_list") or "") == "yes"]
    rows = rows[:limit]

    return {
        "ok": True,
        "result": {
            "count": len(rows),
            "total_in_file": len(rows),
            "rows": rows,
        },
    }


# ---------------------------------------------------------------------------
# ecosystem_state — one reader for the whole ecosystem.
# ---------------------------------------------------------------------------
try:
    import sys as _sys_eco
    _sys_eco.path.insert(0, "/home/bosly_accord/bosly-gov")
    from routers.ecosystem import ecosystem_state as _ecosystem_state_impl  # type: ignore
except Exception:
    _ecosystem_state_impl = None


def ecosystem_state(section: str = "all") -> Dict[str, Any]:
    if _ecosystem_state_impl is None:
        return {"ok": False, "error": "ecosystem reader unavailable"}
    try:
        return _ecosystem_state_impl(section=section)
    except Exception as e:
        return {"ok": False, "error": f"ecosystem_state raised: {e}"}


_LONDON = ZoneInfo("Europe/London")

_PERIOD_FORMS = (
    "today, tomorrow, yesterday, this week, next week, last week, "
    "this month, next month, last month, next 7 days, "
    "YYYY-MM-DD (single day), YYYY-MM-DD..YYYY-MM-DD"
)


def _resolve_period(period, today=None):
    """Resolve a period to inclusive ISO dates (start, end, label).

    Raises ValueError naming the accepted forms. today is injectable so
    a check can pin a date. Weeks are Monday-Sunday, Europe/London.
    """
    if today is None:
        today = _dt.now(_LONDON).date()
    p = (period or "").strip().lower()
    if not p:
        p = "this week"

    def week_bounds(d):
        monday = d - timedelta(days=d.weekday())
        return monday, monday + timedelta(days=6)

    def month_bounds(y, m):
        start = date(y, m, 1)
        end = date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
        return start, end

    if p == "today":
        return today.isoformat(), today.isoformat(), "today"
    if p == "tomorrow":
        d = today + timedelta(days=1)
        return d.isoformat(), d.isoformat(), "tomorrow"
    if p == "yesterday":
        d = today - timedelta(days=1)
        return d.isoformat(), d.isoformat(), "yesterday"
    if p == "this week":
        s, e = week_bounds(today)
        return s.isoformat(), e.isoformat(), "this week"
    if p == "week":
        raise ValueError("ambiguous period 'week'; try 'this week' or 'next week'")
    if p == "next week":
        s, e = week_bounds(today + timedelta(days=7))
        return s.isoformat(), e.isoformat(), "next week"
    if p == "last week":
        s, e = week_bounds(today - timedelta(days=7))
        return s.isoformat(), e.isoformat(), "last week"
    if p == "this month":
        s, e = month_bounds(today.year, today.month)
        return s.isoformat(), e.isoformat(), "this month"
    if p == "next month":
        y, m = (today.year + (today.month == 12), (today.month % 12) + 1)
        s, e = month_bounds(y, m)
        return s.isoformat(), e.isoformat(), "next month"
    if p == "last month":
        y, m = (today.year - (today.month == 1), (today.month - 2) % 12 + 1)
        s, e = month_bounds(y, m)
        return s.isoformat(), e.isoformat(), "last month"
    if p == "next 7 days":
        return today.isoformat(), (today + timedelta(days=6)).isoformat(), "next 7 days"

    if ".." in p:
        a, b = p.split("..", 1)
        try:
            s = date.fromisoformat(a.strip())
            e = date.fromisoformat(b.strip())
        except ValueError:
            raise ValueError(f"unrecognised date in range {period!r}; use YYYY-MM-DD..YYYY-MM-DD")
        if e < s:
            raise ValueError(f"reversed range: end {e} is before start {s}")
        return s.isoformat(), e.isoformat(), f"{s.isoformat()}..{e.isoformat()}"
    try:
        d = date.fromisoformat(p)
    except ValueError:
        raise ValueError(f"unrecognised period {period!r}; accepted: {_PERIOD_FORMS}")
    return d.isoformat(), d.isoformat(), p


# read_accord: the founder's read tool
def _parse_period(period: str) -> tuple[str, str]:
    """Parse a period into (from, to) ISO dates.

    today, tomorrow, this week, next week, this month, a date
    (YYYY-MM-DD), or a range (YYYY-MM-DD..YYYY-MM-DD).
    """
    from datetime import date, timedelta
    p = (period or "").strip().lower()
    today = date.today()
    if p in ("", "today"):
        return today.isoformat(), today.isoformat()
    if p == "tomorrow":
        t = today + timedelta(days=1)
        return t.isoformat(), t.isoformat()
    if p == "this week":
        start = today - timedelta(days=today.weekday())
        return start.isoformat(), (start + timedelta(days=6)).isoformat()
    if p == "next week":
        start = today - timedelta(days=today.weekday()) + timedelta(days=7)
        return start.isoformat(), (start + timedelta(days=6)).isoformat()
    if p == "this month":
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return start.isoformat(), end.isoformat()
    if ".." in p:
        a, b = p.split("..", 1)
        return a.strip(), b.strip()
    return p, p


def read_accord(section: str = "calendar", period: str = "") -> Dict[str, Any]:
    """Read the founder's Accord.founder through the app's own routes.

    The Executive's key is FOUNDER_SERVICE_TOKEN; the userId is
    FOUNDER_USER_ID. The Copilot never sees the token; this tool sends
    it. A client's Accord is never read — the token is the founder's.
    Sections: calendar, invoices, mode.
    """
    import json as _json
    import urllib.request as _urllib

    token = (os.environ.get("FOUNDER_SERVICE_TOKEN") or "").strip()
    if not token:
        return {"ok": False, "error": "FOUNDER_SERVICE_TOKEN not set"}
    base = "http://localhost:3100"
    paths = {
        "calendar": "/api/calendar/list",
        "invoices": "/api/invoices",
        "mode": "/api/account/mode",
    }
    path = paths.get(section)
    if not path:
        return {"ok": False, "error": f"unknown section {section!r}; known: {sorted(paths)}"}
    # The period, for the calendar: "next week" narrows the window.
    if section == "calendar" and period:
        try:
            f, t = _parse_period(period)
            path = f"{path}?from={f}&to={t}"
        except Exception as e:
            return {"ok": False, "error": f"could not parse period {period!r}: {e}"}
    req = _urllib.Request(base + path, headers={"Authorization": f"Bearer {token}"})
    try:
        with _urllib.urlopen(req, timeout=30) as r:
            status = r.status
            ctype = r.headers.get("content-type", "")
            body = r.read().decode("utf-8", "replace")
        # A failure is not a zero. If the route answered with HTML (a
        # redirect to signin, a middleware page) or an error, say so —
        # never parse it as data and never report it as empty.
        if "application/json" not in ctype:
            return {
                "ok": False,
                "error": f"Accord returned {status} {ctype or '(no content-type)'}",
                "body_preview": body[:160],
            }
        try:
            data = _json.loads(body)
        except ValueError:
            return {
                "ok": False,
                "error": f"Accord returned {status} but the body was not JSON",
                "body_preview": body[:160],
            }
        # The calendar route returns every event in a wide window and
        # does not filter deleted rows. Resolve the period here, and
        # filter on the route's own local `date` string (YYYY-MM-DD).
        if section == "calendar":
            if not isinstance(data, dict) or not isinstance(data.get("events"), list):
                return {"ok": False, "error": "calendar response had no events list"}
            try:
                start, end, label = _resolve_period(period)
            except ValueError as e:
                return {"ok": False, "error": str(e)}
            kept = []
            dropped_deleted = 0
            for ev in data["events"]:
                if ev.get("isDeleted"):
                    dropped_deleted += 1
                    continue
                d = ev.get("date")
                if isinstance(d, str) and start <= d <= end:
                    kept.append(ev)
            data = dict(data)
            data["events"] = kept
            data["period"] = {
                "start": start, "end": end, "label": label,
                "dropped_deleted": dropped_deleted,
            }
        return {"ok": True, "result": data}
    except _urllib.HTTPError as e:
        return {"ok": False, "error": f"Accord returned HTTP {e.code} for {path}"}
    except Exception as e:
        return {"ok": False, "error": f"read_accord failed: {type(e).__name__}: {e}"}


# test proof
def read_chat(room: str = "all", limit: int = 40, week: str = "") -> Dict[str, Any]:
    """Read the shared transcript — both rooms, one log.

    Every message from the app and the UI butler is appended to
    chat-transcript.jsonl with ts, room, role, text. This tool reads
    the last N, optionally filtered by room. Use it to answer "what did
    we say about X" — read, never guess.
    """
    import json as _json
    from pathlib import Path as _Path
    import glob as _glob

    # The transcript is one file per ISO week. Read the current week's
    # file by default; a "week" argument reads a specific one; no
    # argument reads the current week. The old weeks stay, dated.
    base = _Path("/mnt/bosly/bosly-data/.data/governor")
    files = sorted(base.glob("chat-transcript-*.jsonl"))
    if week:
        files = [f for f in files if f"W{week}" in f.name or week in f.name]
    elif files:
        files = [files[-1]]   # the current week
    if not files:
        return {"ok": True, "result": {"messages": []}}
    lines = []
    for f in files:
        try:
            lines.extend(f.read_text(encoding="utf-8").splitlines())
        except Exception:
            continue
    lines = lines[-limit:]
    msgs = []
    for line in lines:
        try:
            e = _json.loads(line)
        except Exception:
            continue
        if room != "all" and e.get("room") != room:
            continue
        msgs.append(e)
    return {"ok": True, "result": {"messages": msgs}}


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
    {
        "name": "save_thing",
        "description": (
            "Save a thing in the business memory: a client, a project, "
            "a lead, an idea, anything the founder needs held. `kind` "
            "is a free string (client, lead, project, idea, ...). "
            "`title` is one line. `body` is markdown detail. If you "
            "pass an existing `thing_id`, it updates; otherwise it "
            "creates. Only the declared fields are stored."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "description": "e.g. client, lead, project, idea"},
                "title": {"type": "string", "description": "one-line label"},
                "body": {"type": "string", "description": "markdown detail"},
                "status": {"type": "string", "enum": ["active", "paused", "done", "lost"]},
                "tags": {"type": "string", "description": "comma-separated tags, optional"},
                "thing_id": {"type": "string", "description": "pass to update an existing thing"},
            },
            "required": ["kind", "title"],
        },
        "fn": save_thing,
    },
    {
        "name": "read_thing",
        "description": (
            "Read one thing from the business memory by id. Returns "
            "the full record: kind, title, status, body, tags, "
            "timestamps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thing_id": {"type": "string", "description": "the thing's id"},
            },
            "required": ["thing_id"],
        },
        "fn": read_thing,
    },
    {
        "name": "find_things",
        "description": (
            "Search the business memory. Filter by kind, status, and/or "
            "a text query (matches title, body, and tags). Returns up "
            "to 50 things by default, newest-updated first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string"},
                "status": {"type": "string", "enum": ["active", "paused", "done", "lost"]},
                "query": {"type": "string"},
                "limit": {"type": "integer", "description": "1-500, default 50"},
            },
        },
        "fn": find_things,
    },
    {
        "name": "link_things",
        "description": (
            "Record a relationship between two things, e.g. a lead "
            "becoming a client, or a project belonging to a client. "
            "Stored as a tag line on the from-thing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "from_id": {"type": "string"},
                "to_id": {"type": "string"},
                "relation": {"type": "string", "description": "e.g. became, belongs_to, related_to"},
            },
            "required": ["from_id", "to_id"],
        },
        "fn": link_things,
    },
    {
        "name": "draft_email",
        "description": (
            "Structure a draft email to a client. Does not send. "
            "Returns the draft as a record: to, subject, body. Use "
            "this when the founder asks you to draft outreach, then "
            "show them the draft and wait for approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "the client's email address"},
                "subject": {"type": "string"},
                "body": {"type": "string", "description": "the draft text"},
            },
            "required": ["to", "subject", "body"],
        },
        "fn": draft_email,
    },
    {
        "name": "send_draft_to_me",
        "description": (
            "Email a draft to the FOUNDER so it can be read on a phone "
            "while away from the desk. The recipient is hardcoded to "
            "the founder's own address — this tool cannot email a "
            "client. Use it after drafting when the founder wants to "
            "review the draft away from the UI. It does not send the "
            "draft to the client; that is a separate step."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "note": {"type": "string", "description": "optional note above the draft"},
            },
            "required": ["subject", "body"],
        },
        "fn": send_draft_to_me,
    },
    {
        "name": "run_lead_scout",
        "description": (
            "Find businesses with no website, from OpenStreetMap, by "
            "running the lead-scout script. Give a category (hairdresser, "
            "cafe, pub, plumber, ...) and an area (a POSTCODE or a "
            "small area, e.g. 'NE46' or 'Kemptown' — a whole town is a "
            "huge bounding box and Overpass times out). Returns the "
            "candidates as rows: name, city, "
            "phone, and whether they have a website. If the Overpass "
            "endpoint is down, it says so — a failure is never reported "
            "as zero results. After running, you can save chosen "
            "candidates with save_thing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "one of: hairdresser, barber, beauty, cafe, restaurant, pub, bakery, butcher, florist, plumber, electrician, gardener",
                },
                "area": {
                    "type": "string",
                    "description": "a POSTCODE or small area, e.g. 'NE46' or 'Kemptown' — not a whole town",
                },
            },
            "required": ["category", "area"],
        },
        "fn": run_lead_scout,
    },
    {
        "name": "send_email",
        "description": (
            "Send a real email to a client. This is the final step of "
            "the lead workflow. It requires confirmed=True, which you "
            "must ONLY set after the founder has explicitly said yes "
            "in this conversation. Never set confirmed=True on your "
            "own initiative. Ask: 'Send this to <address>?' and wait. "
            "For sending a draft to the founder's own address, use "
            "send_draft_to_me instead — this tool refuses the founder's "
            "address."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "the client's email address"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "confirmed": {
                    "type": "boolean",
                    "description": "must be true, and only after the founder has said yes",
                },
                "draft_thing_id": {
                    "type": "string",
                    "description": "optional: the id of a saved draft thing. If given, its subject and body are used instead of the ones passed.",
                },
            },
            "required": ["to", "subject", "body", "confirmed"],
        },
        "fn": send_email,
    },
    {
        "name": "read_leads",
        "description": (
            "Read this week's ranked lead shortlist: the top businesses "
            "the scout found, ranked by fit, with Companies House and "
            "Google data attached. Use this when the founder says 'work "
            "this week's list' or 'what's in this week's sweep?'. Set "
            "only_call_list=true to get just the top 10 marked for a "
            "call. Each row has name, phone, city, category, fit_score, "
            "fit_breakdown, call_list, ch_name, ch_status, ch_age_months, "
            "match_confidence, and google_rating/reviews if available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "only_call_list": {
                    "type": "boolean",
                    "description": "true to return only the call-list rows",
                },
                "limit": {
                    "type": "integer",
                    "description": "max rows, 1-50 (default 15)",
                },
            },
        },
        "fn": read_leads,
    },
    {
        "name": "ecosystem_state",
        "description": (
            "Read the state of the whole ecosystem in one call. Use it "
            "when the founder asks 'what's going on?' or before acting "
            "on something that depends on the current state. Sections: "
            "plan (in-progress plan items), things (active clients, "
            "leads, drafts, projects), scout (this week's ranked list "
            "with contact routes), capsules (the latest reasoning "
            "trail), accord (not yet — needs the session token). Pass "
            "section='all' for everything, or one section name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["all", "plan", "things", "scout", "capsules", "accord"],
                },
            },
        },
        "fn": ecosystem_state,
    },
    {
        "name": "read_accord",
        "description": (
            "Read the founder's Accord.founder. Sections: "
            "'calendar' — events for a period (default this week; "
            "pass period='next week' or '2026-11-02..2026-11-08'). "
            "Titles and details are encrypted client-side: you get the "
            "times and structure, not the content. To read what an event "
            "is, tell the founder to open Accord. "
            "'invoices' — the invoice list, what is issued and outstanding; "
            "'mode' — the account mode. "
            "Finance is NOT readable here: income, expenses and profit are "
            "encrypted client-side. For 'how much did I make' or tax, tell "
            "the founder to ask in Accord, where the session has the key."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": ["calendar", "invoices", "mode"]},
                "period": {
                    "type": "string",
                    "description": (
                        "For 'calendar' only. today, tomorrow, yesterday, "
                        "this week, next week, last week, this month, next "
                        "month, last month, next 7 days, YYYY-MM-DD, or "
                        "YYYY-MM-DD..YYYY-MM-DD. Omit for this week."
                    ),
                },
            },
            "required": ["section"],
        },
        "fn": read_accord,
    },
    {
        "name": "write_file",
        "description": (
            "Write a file under one of the three repos. The same guards as "
            "read_file: inside a repo, no .env/.key/.pem, no .git/"
            "node_modules/.next. A .bak is written before the change. Use "
            "this for a new file or a full rewrite; use patch_file for a "
            "small anchored change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        "fn": write_file,
    },
    {
        "name": "patch_file",
        "description": (
            "Replace ONE occurrence of anchor with replacement in a file. "
            "Aborts if the anchor is not found exactly once — never a "
            "partial edit. A .bak is written before the change. This is the "
            "tool for a small, anchored code change: read the file first, "
            "pick a unique anchor, then patch. This includes the tools "
            "themselves — routers/tools.py, and this tool's own schema and "
            "read_accord's sections, are files like any other and can be "
            "patched here. After patching, PROVE it: ask the question the "
            "patch was meant to answer — the one the task was about — and "
            "report the answer, not the diff. A patch that compiles is not a "
            "patch that works."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "anchor": {"type": "string", "description": "the exact text to replace; must appear exactly once"},
                "replacement": {"type": "string", "description": "the text to put in its place"},
            },
            "required": ["path", "anchor", "replacement"],
        },
        "fn": patch_file,
    },
    {
        "name": "read_chat",
        "description": (
            "Read the shared transcript — both rooms (app and ui), one "
            "log, with timestamps. Use this to answer 'what did we say "
            "about X' or to remember the conversation. Read, never guess."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "room": {"type": "string", "enum": ["all", "app", "ui"]},
                "limit": {"type": "integer"},
                "week": {"type": "string", "description": "an ISO week, e.g. '2026-W44'; empty reads the current week"},
            },
            "required": [],
        },
        "fn": read_chat,
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

    # --- business memory wrappers (use a temp DB) ---
    import os as _os, tempfile as _tmp
    _tmpdir = _tmp.mkdtemp()
    _os.environ["BOSLY_THINGS_DB"] = str(Path(_tmpdir) / "things.db")
    try:
        r = save_thing(kind="lead", title="Test lead",
                       body="Testing the wrapper")
        check("save_thing wrapper creates",
              r["ok"] and "id" in r["result"], detail=str(r))
        tid = r["result"]["id"] if r["ok"] else ""
        r = read_thing(tid)
        check("read_thing wrapper reads",
              r["ok"] and r["result"]["title"] == "Test lead", detail=str(r))
        r = find_things(kind="lead")
        check("find_things wrapper finds",
              r["ok"] and r["result"]["count"] >= 1, detail=str(r))
        r = save_thing(kind="", title="x")
        check("save_thing wrapper refuses empty kind", not r["ok"])
    finally:
        import shutil as _sh
        _sh.rmtree(_tmpdir, ignore_errors=True)
        _os.environ.pop("BOSLY_THINGS_DB", None)

    # --- run_lead_scout guards (no network) ---
    r = run_lead_scout(category="notacategory", area="Hexham")
    check("run_lead_scout refuses unknown category", not r["ok"])

    r = run_lead_scout(category="hairdresser", area="")
    check("run_lead_scout refuses empty area", not r["ok"])

    r = run_lead_scout(category="hairdresser", area="X" * 200)
    check("run_lead_scout refuses oversized area", not r["ok"])

    r = run_lead_scout(category="hairdresser", area="Hexham; rm -rf /")
    check("run_lead_scout refuses shell metacharacters", not r["ok"])

    # --- send_email guards (no real send) ---
    r = send_email(to="client@example.com", subject="x", body="y", confirmed=False)
    check("send_email refuses without confirmed=True", not r["ok"])

    r = send_email(to="notanemail", subject="x", body="y", confirmed=True)
    check("send_email refuses invalid address", not r["ok"])

    r = send_email(to="jr-arnott@outlook.com", subject="x", body="y", confirmed=True)
    check("send_email refuses the founder's own address", not r["ok"])

    r = send_email(to="client@example.com", subject="", body="y", confirmed=True)
    check("send_email refuses empty subject", not r["ok"])

    r = send_email(to="client@example.com", subject="x", body="", confirmed=True)
    check("send_email refuses empty body", not r["ok"])

    # read_leads guards (no file dependency for the refusal cases)
    r = read_leads(limit=0)
    check("read_leads refuses limit 0", not r["ok"])
    r = read_leads(limit=999)
    check("read_leads refuses limit 999", not r["ok"])

    r = ecosystem_state(section="nope")
    check("ecosystem_state refuses unknown section", not r["ok"])

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_selftest())
