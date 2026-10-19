"""routers/things.py — the business memory.

WHAT THIS HOLDS: the business's state. Clients, projects, leads,
ideas, notes — anything the founder needs the Executive to hold.
Not lessons (that is memory.json), not the plan (that is
PLAN.md). The things that are going on.

WHY A GENERAL STORE, NOT A FIXED SCHEMA. The founder's words:
"I need the chief to hold everything I need." A fixed schema can
only hold what was anticipated. This holds a thing with a kind,
a title, a body, and tags. New kinds appear without a migration.

THE SHAPE OF A THING:
  id         — a stable id, "thing-<timestamp>-<short>"
  kind       — free string: "client", "lead", "project", "idea", ...
  title      — one line: "The hairdresser", "Café in town"
  status     — "active" | "paused" | "done" | "lost"
  body       — markdown. The detail. The Executive reads prose well.
  tags       — comma-separated string, optional
  created_at — ISO timestamp
  updated_at — ISO timestamp

WHERE IT LIVES: /mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/things.db

WHY SQLITE. The memory store (memory.json) is JSON and it was
malformed for five weeks without anyone noticing. SQLite gives us
queries, indexes, and a schema we can check.

THE SELF-TEST: python3 routers/things.py

It creates a temp database, exercises every operation, and
refuses to touch the real one. Safe to run any time.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unicodedata
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# The real database. Overridable for tests via BOSLY_THINGS_DB.
DEFAULT_DB = Path(
    "/mnt/bosly/bosly-data/copilot-knowledge/bosly-gov/things.db"
)

ALLOWED_STATUSES = {"active", "paused", "done", "lost"}


def _db_path() -> Path:
    return Path(os.environ.get("BOSLY_THINGS_DB", str(DEFAULT_DB)))


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS things (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            body TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            title_norm TEXT NOT NULL DEFAULT '',
            body_norm TEXT NOT NULL DEFAULT ''
        )
    """)
    # Migration: add the columns if this is an old db
    cols = {r[1] for r in conn.execute("PRAGMA table_info(things)").fetchall()}
    if "title_norm" not in cols:
        conn.execute("ALTER TABLE things ADD COLUMN title_norm TEXT NOT NULL DEFAULT ''")
    if "body_norm" not in cols:
        conn.execute("ALTER TABLE things ADD COLUMN body_norm TEXT NOT NULL DEFAULT ''")
    # Backfill existing rows whose norm columns are empty
    for row in conn.execute("SELECT id, title, body FROM things WHERE title_norm = ''").fetchall():
        conn.execute(
            "UPDATE things SET title_norm = ?, body_norm = ? WHERE id = ?",
            (_norm(row["title"]), _norm(row["body"] or ""), row["id"]),
        )
    conn.commit()
    conn.execute("CREATE INDEX IF NOT EXISTS idx_things_kind ON things(kind)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_things_status ON things(status)")
    conn.commit()
    return conn


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _norm(s: str) -> str:
    """Strip accents and lowercase — 'Café' -> 'cafe'."""
    if not s:
        return ""
    n = unicodedata.normalize("NFD", s)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return n.lower()


def _new_id() -> str:
    return f"thing-{int(time.time() * 1000)}-{os.urandom(2).hex()}"


def save_thing(
    kind: str,
    title: str,
    body: str = "",
    status: str = "active",
    tags: str = "",
    thing_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update a thing. Returns {ok, result|error}."""
    if not kind or not kind.strip():
        return {"ok": False, "error": "kind is required"}
    if not title or not title.strip():
        return {"ok": False, "error": "title is required"}
    if status not in ALLOWED_STATUSES:
        return {
            "ok": False,
            "error": f"status {status!r} not in {sorted(ALLOWED_STATUSES)}",
        }
    if len(body) > 100_000:
        return {"ok": False, "error": f"body is {len(body)} chars (max 100000)"}

    kind = kind.strip().lower()
    title = title.strip()
    now = _now()

    conn = _connect()
    try:
        if thing_id:
            row = conn.execute(
                "SELECT id FROM things WHERE id = ?", (thing_id,)
            ).fetchone()
            if row is None:
                return {"ok": False, "error": f"no thing with id {thing_id!r}"}
            conn.execute(
                """UPDATE things
                   SET kind=?, title=?, status=?, body=?, tags=?, updated_at=?,
                       title_norm=?, body_norm=?
                   WHERE id=?""",
                (kind, title, status, body, tags, now,
                 _norm(title), _norm(body), thing_id),
            )
            saved_id = thing_id
        else:
            saved_id = _new_id()
            conn.execute(
                """INSERT INTO things
                   (id, kind, title, status, body, tags, created_at, updated_at,
                    title_norm, body_norm)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (saved_id, kind, title, status, body, tags, now, now,
                 _norm(title), _norm(body)),
            )
        conn.commit()
    finally:
        conn.close()

    return {
        "ok": True,
        "result": {
            "id": saved_id,
            "kind": kind,
            "title": title,
            "status": status,
            "updated_at": now,
        },
    }


def read_thing(thing_id: str) -> Dict[str, Any]:
    """Read one thing by id."""
    if not thing_id:
        return {"ok": False, "error": "id is required"}
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM things WHERE id = ?", (thing_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"ok": False, "error": f"no thing with id {thing_id!r}"}
    return {"ok": True, "result": dict(row)}


def find_things(
    kind: Optional[str] = None,
    status: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search things by kind, status, and/or body/title text."""
    if status and status not in ALLOWED_STATUSES:
        return {
            "ok": False,
            "error": f"status {status!r} not in {sorted(ALLOWED_STATUSES)}",
        }
    if limit < 1 or limit > 500:
        return {"ok": False, "error": "limit must be 1-500"}

    clauses = []
    params: List[Any] = []
    if kind:
        clauses.append("kind = ?")
        params.append(kind.strip().lower())
    if status:
        clauses.append("status = ?")
        params.append(status)
    if query:
        # Search the normalised columns so "Cafe" finds "Café".
        clauses.append("(title_norm LIKE ? OR body_norm LIKE ? OR tags LIKE ?)")
        qn = f"%{_norm(query)}%"
        qr = f"%{query}%"
        params.extend([qn, qn, qr])

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM things{where} ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    conn = _connect()
    try:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

    return {"ok": True, "result": {"count": len(rows), "things": rows}}


def link_things(
    from_id: str, to_id: str, relation: str = "related"
) -> Dict[str, Any]:
    """Record a relationship between two things.

    v1: stored as a tag line on the from-thing. A proper links
    table can wait until there is a query that needs it.
    """
    if not from_id or not to_id:
        return {"ok": False, "error": "from_id and to_id are required"}
    if from_id == to_id:
        return {"ok": False, "error": "cannot link a thing to itself"}
    if not relation or len(relation) > 60:
        return {"ok": False, "error": "relation must be 1-60 chars"}

    conn = _connect()
    try:
        a = conn.execute("SELECT id, tags FROM things WHERE id = ?", (from_id,)).fetchone()
        b = conn.execute("SELECT id FROM things WHERE id = ?", (to_id,)).fetchone()
        if a is None:
            return {"ok": False, "error": f"no thing with id {from_id!r}"}
        if b is None:
            return {"ok": False, "error": f"no thing with id {to_id!r}"}
        link = f"{relation}:{to_id}"
        tags = a["tags"] or ""
        if link in tags.split(","):
            return {"ok": True, "result": {"already_linked": True, "from": from_id, "to": to_id}}
        new_tags = (tags + "," + link).lstrip(",")
        conn.execute(
            "UPDATE things SET tags = ?, updated_at = ? WHERE id = ?",
            (new_tags, _now(), from_id),
        )
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "result": {"from": from_id, "to": to_id, "relation": relation}}


# ---------------------------------------------------------------------------
# Self-test — uses a temp DB, never touches the real one
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

    # Point at a temp DB for the whole test
    tmpdir = tempfile.mkdtemp()
    os.environ["BOSLY_THINGS_DB"] = str(Path(tmpdir) / "things.db")

    try:
        # save
        r = save_thing(kind="client", title="The hairdresser",
                       body="Needs an AI receptionist. Calls only in the morning.")
        check("save_thing creates", r["ok"], detail=str(r))
        hairdresser_id = r["result"]["id"]

        # save another of a different kind
        r2 = save_thing(kind="lead", title="Café in town",
                        body="No website. Good reviews. Could use a booking page.")
        check("save_thing second kind", r2["ok"], detail=str(r2))
        cafe_id = r2["result"]["id"]

        # read
        r = read_thing(hairdresser_id)
        check("read_thing returns the thing",
              r["ok"] and r["result"]["title"] == "The hairdresser",
              detail=str(r))

        # find by kind
        r = find_things(kind="client")
        check("find_things by kind",
              r["ok"] and r["result"]["count"] == 1,
              detail=str(r))

        # find by query
        r = find_things(query="receptionist")
        check("find_things by query",
              r["ok"] and r["result"]["count"] == 1,
              detail=str(r))

        # find by status
        r = find_things(status="active")
        check("find_things by status",
              r["ok"] and r["result"]["count"] == 2,
              detail=str(r))

        # update
        r = save_thing(kind="client", title="The hairdresser",
                       body="Needs an AI receptionist and a booking page.",
                       status="active", thing_id=hairdresser_id)
        check("save_thing updates", r["ok"], detail=str(r))
        r = read_thing(hairdresser_id)
        check("update took effect",
              "booking page" in r["result"]["body"],
              detail=r["result"]["body"])

        # link
        r = link_things(from_id=cafe_id, to_id=hairdresser_id, relation="similar_to")
        check("link_things", r["ok"], detail=str(r))
        r = read_thing(cafe_id)
        check("link recorded in tags",
              "similar_to:" + hairdresser_id in r["result"]["tags"],
              detail=r["result"]["tags"])

        # guards
        r = save_thing(kind="", title="x")
        check("save_thing refuses empty kind", not r["ok"])
        r = save_thing(kind="client", title="")
        check("save_thing refuses empty title", not r["ok"])
        r = save_thing(kind="client", title="x", status="bogus")
        check("save_thing refuses unknown status", not r["ok"])
        r = read_thing("thing-does-not-exist")
        check("read_thing refuses unknown id", not r["ok"])
        r = find_things(status="bogus")
        check("find_things refuses unknown status", not r["ok"])
        r = link_things(from_id=cafe_id, to_id="thing-nope")
        check("link_things refuses unknown target", not r["ok"])
    finally:
        # Clean up temp db
        import shutil as _sh
        _sh.rmtree(tmpdir, ignore_errors=True)
        os.environ.pop("BOSLY_THINGS_DB", None)

    print()
    print(f"SUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
