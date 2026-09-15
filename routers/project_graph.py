#!/usr/bin/env python3
"""
Bosly Gov v4 - Project Intelligence Graph
Python 3.12+

SQLite-backed property graph:
- nodes(project_slug, node_type, node_id, properties_json, created_at, updated_at)
- edges(project_slug, from_node, to_node, relation, weight, created_at, updated_at)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path("/mnt/bosly/bosly-data/.data/governor/project-graph.sqlite3")
PROJECTS_BASE = Path("/mnt/bosly/bosly-data/copilot-knowledge")

ALLOWED_NODE_TYPES = {"decision", "component", "incident", "person", "event"}
ALLOWED_RELATIONS = {"causes", "fixes", "depends_on", "supersedes", "similar_to"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_slug(slug: str) -> bool:
    if not slug or len(slug) > 50:
        return False
    return all(c.isalnum() or c == "-" for c in slug) and slug == slug.lower()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            project_slug TEXT NOT NULL,
            node_type TEXT NOT NULL,
            node_id TEXT NOT NULL,
            properties_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (project_slug, node_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS edges (
            project_slug TEXT NOT NULL,
            from_node TEXT NOT NULL,
            to_node TEXT NOT NULL,
            relation TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (project_slug, from_node, to_node, relation)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_project_type ON nodes(project_slug, node_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_project_from ON edges(project_slug, from_node)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_project_to ON edges(project_slug, to_node)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_project_relation ON edges(project_slug, relation)")
    conn.commit()


def _node_key(project_slug: str, node_type: str, node_id: str) -> str:
    return f"{project_slug}:{node_type}:{node_id}"


def _parse_node_ref(node_ref: str) -> tuple[str, str, str] | None:
    parts = (node_ref or "").split(":", 2)
    if len(parts) != 3:
        return None
    slug, ntype, nid = parts[0].strip(), parts[1].strip(), parts[2].strip()
    if not slug or not ntype or not nid:
        return None
    return slug, ntype, nid


def add_node(node_type: str, node_id: str, properties: dict) -> dict:
    slug = str((properties or {}).get("project_slug", "")).strip()
    if not _validate_slug(slug):
        return {"ok": False, "error": "Invalid project_slug"}
    ntype = str(node_type or "").strip().lower()
    nid = str(node_id or "").strip()
    if ntype not in ALLOWED_NODE_TYPES:
        return {"ok": False, "error": f"Invalid node_type: {ntype}"}
    if not nid:
        return {"ok": False, "error": "node_id is required"}
    props = dict(properties or {})
    props.pop("project_slug", None)

    now = _now_iso()
    conn = _connect()
    try:
        _init_db(conn)
        conn.execute(
            """
            INSERT INTO nodes(project_slug, node_type, node_id, properties_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_slug, node_id) DO UPDATE SET
              node_type = excluded.node_type,
              properties_json = excluded.properties_json,
              updated_at = excluded.updated_at
            """,
            (slug, ntype, nid, json.dumps(props, ensure_ascii=False), now, now),
        )
        conn.commit()
        return {
            "ok": True,
            "node": {
                "project_slug": slug,
                "node_type": ntype,
                "node_id": nid,
                "node_ref": _node_key(slug, ntype, nid),
                "properties": props,
                "updated_at": now,
            },
        }
    finally:
        conn.close()


def add_edge(from_node: str, to_node: str, relation: str, weight: float = 1.0) -> dict:
    rel = str(relation or "").strip().lower()
    if rel not in ALLOWED_RELATIONS:
        return {"ok": False, "error": f"Invalid relation: {rel}"}

    f = _parse_node_ref(from_node)
    t = _parse_node_ref(to_node)
    if not f or not t:
        return {"ok": False, "error": "Invalid node reference format"}
    f_slug, _, f_id = f
    t_slug, _, t_id = t
    if f_slug != t_slug:
        return {"ok": False, "error": "Cross-project edges are not allowed"}
    if not _validate_slug(f_slug):
        return {"ok": False, "error": "Invalid project_slug"}

    w = float(weight or 1.0)
    if w <= 0:
        w = 0.1

    conn = _connect()
    now = _now_iso()
    try:
        _init_db(conn)
        exists = conn.execute(
            "SELECT node_id FROM nodes WHERE project_slug=? AND node_id IN (?, ?)",
            (f_slug, f_id, t_id),
        ).fetchall()
        if len(exists) < 2:
            return {"ok": False, "error": "from_node or to_node does not exist"}

        conn.execute(
            """
            INSERT INTO edges(project_slug, from_node, to_node, relation, weight, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_slug, from_node, to_node, relation) DO UPDATE SET
              weight = excluded.weight,
              updated_at = excluded.updated_at
            """,
            (f_slug, f_id, t_id, rel, w, now, now),
        )
        conn.commit()
        return {
            "ok": True,
            "edge": {
                "project_slug": f_slug,
                "from_node": f_id,
                "to_node": t_id,
                "relation": rel,
                "weight": w,
                "updated_at": now,
            },
        }
    finally:
        conn.close()


def build_graph(project_slug: str) -> dict:
    slug = str(project_slug or "").strip()
    if not _validate_slug(slug):
        return {"ok": False, "error": "Invalid project_slug"}

    code_root = Path("/home/bosly_accord/bosly-1.0")
    if not code_root.exists():
        return {"ok": False, "error": "Code root not found"}

    conn = _connect()
    try:
        _init_db(conn)
        now = _now_iso()

        file_nodes_added = 0
        dep_edges_added = 0

        exts = {".ts", ".tsx", ".js", ".jsx", ".py"}
        skip_dirs = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".turbo"}

        file_index: dict[str, str] = {}
        for root, dirs, files in os_walk(code_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            rp = Path(root)
            for fn in files:
                p = rp / fn
                if p.suffix.lower() not in exts:
                    continue
                try:
                    rel = str(p.resolve().relative_to(code_root)).replace("\\", "/")
                except Exception:
                    continue
                node_id = f"component:{rel}"
                props = {"path": rel, "ext": p.suffix.lower(), "project_slug": slug}
                add_node("component", node_id, props)
                file_index[rel] = node_id
                file_nodes_added += 1

        import_re = re_compile_imports()
        for rel, node_id in file_index.items():
            p = code_root / rel
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for imp in import_re(txt):
                tgt = resolve_import_to_rel(rel, imp)
                if not tgt:
                    continue
                if tgt in file_index:
                    from_ref = _node_key(slug, "component", node_id)
                    to_ref = _node_key(slug, "component", file_index[tgt])
                    res = add_edge(from_ref, to_ref, "depends_on", 1.0)
                    if res.get("ok"):
                        dep_edges_added += 1

        event_node_id = f"event:graph-build:{int(datetime.now(timezone.utc).timestamp())}"
        add_node("event", event_node_id, {"project_slug": slug, "kind": "graph_build", "summary": "Graph rebuilt"})
        conn.commit()

        return {
            "ok": True,
            "project_slug": slug,
            "stats": {
                "component_nodes": file_nodes_added,
                "depends_on_edges": dep_edges_added,
            },
        }
    finally:
        conn.close()


def query_graph(query: str, project_slug: str) -> list[dict]:
    slug = str(project_slug or "").strip()
    q = str(query or "").strip().lower()
    if not _validate_slug(slug) or not q:
        return []

    conn = _connect()
    try:
        _init_db(conn)
        rows = conn.execute(
            """
            SELECT node_type, node_id, properties_json, updated_at
            FROM nodes
            WHERE project_slug = ?
              AND (
                lower(node_id) LIKE ?
                OR lower(properties_json) LIKE ?
              )
            ORDER BY updated_at DESC
            LIMIT 50
            """,
            (slug, f"%{q}%", f"%{q}%"),
        ).fetchall()

        out = []
        for r in rows:
            try:
                props = json.loads(r["properties_json"] or "{}")
            except Exception:
                props = {}
            out.append(
                {
                    "node_type": r["node_type"],
                    "node_id": r["node_id"],
                    "properties": props,
                    "updated_at": r["updated_at"],
                }
            )
        return out
    finally:
        conn.close()


def get_related_entities(entity_id: str, project_slug: str) -> list[dict]:
    slug = str(project_slug or "").strip()
    eid = str(entity_id or "").strip()
    if not _validate_slug(slug) or not eid:
        return []

    conn = _connect()
    try:
        _init_db(conn)
        rows = conn.execute(
            """
            SELECT e.from_node, e.to_node, e.relation, e.weight, e.updated_at,
                   nf.node_type AS from_type, nt.node_type AS to_type
            FROM edges e
            LEFT JOIN nodes nf ON nf.project_slug=e.project_slug AND nf.node_id=e.from_node
            LEFT JOIN nodes nt ON nt.project_slug=e.project_slug AND nt.node_id=e.to_node
            WHERE e.project_slug = ?
              AND (e.from_node = ? OR e.to_node = ?)
            ORDER BY e.weight DESC, e.updated_at DESC
            LIMIT 100
            """,
            (slug, eid, eid),
        ).fetchall()

        return [
            {
                "from_node": r["from_node"],
                "to_node": r["to_node"],
                "from_type": r["from_type"],
                "to_type": r["to_type"],
                "relation": r["relation"],
                "weight": float(r["weight"] or 1.0),
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_project_summary(project_slug: str) -> dict:
    slug = str(project_slug or "").strip()
    if not _validate_slug(slug):
        return {"ok": False, "error": "Invalid project_slug"}

    conn = _connect()
    try:
        _init_db(conn)

        node_counts = conn.execute(
            """
            SELECT node_type, COUNT(*) AS c
            FROM nodes
            WHERE project_slug=?
            GROUP BY node_type
            """,
            (slug,),
        ).fetchall()

        edge_counts = conn.execute(
            """
            SELECT relation, COUNT(*) AS c
            FROM edges
            WHERE project_slug=?
            GROUP BY relation
            """,
            (slug,),
        ).fetchall()

        recent = conn.execute(
            """
            SELECT node_type, node_id, updated_at
            FROM nodes
            WHERE project_slug=?
            ORDER BY updated_at DESC
            LIMIT 10
            """,
            (slug,),
        ).fetchall()

        return {
            "ok": True,
            "project_slug": slug,
            "nodes": {r["node_type"]: int(r["c"]) for r in node_counts},
            "edges": {r["relation"]: int(r["c"]) for r in edge_counts},
            "recent_nodes": [
                {"node_type": r["node_type"], "node_id": r["node_id"], "updated_at": r["updated_at"]}
                for r in recent
            ],
        }
    finally:
        conn.close()


def os_walk(root: Path):
    import os
    return os.walk(root)


def re_compile_imports():
    import re
    pats = [
        re.compile(r'(?m)^\s*import\s+[^"\']*from\s+["\']([^"\']+)["\']'),
        re.compile(r'(?m)^\s*import\s+["\']([^"\']+)["\']'),
        re.compile(r'(?m)^\s*const\s+.+?=\s*require\(["\']([^"\']+)["\']\)'),
        re.compile(r'(?m)^\s*from\s+["\']([^"\']+)["\']\s+import\s+'),
    ]

    def extract(text: str) -> list[str]:
        out: list[str] = []
        for rx in pats:
            out.extend([m.group(1).strip() for m in rx.finditer(text or "") if m.group(1).strip()])
        return out

    return extract


def resolve_import_to_rel(src_rel: str, imp: str) -> str | None:
    if not imp or not imp.startswith("."):
        return None
    src = Path(src_rel)
    base = src.parent
    target = (base / imp).as_posix()

    candidates = [
        target,
        f"{target}.ts",
        f"{target}.tsx",
        f"{target}.js",
        f"{target}.jsx",
        f"{target}.py",
        f"{target}/index.ts",
        f"{target}/index.tsx",
        f"{target}/index.js",
        f"{target}/index.py",
    ]
    for c in candidates:
        p = Path(c)
        norm = str(p).replace("\\", "/")
        norm = str(Path(norm)).replace("\\", "/")
        if ".." in norm.split("/"):
            continue
        return norm
    return None
