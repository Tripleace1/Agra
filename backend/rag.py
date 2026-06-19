"""SQLite FTS5 retrieval for RAG context."""
from __future__ import annotations

import re
import sqlite3
from typing import List

from config import DB_PATH, RAG_TOP_K


_FTS_SAFE = re.compile(r"[^\w\s]")


def _sanitize(query: str) -> str:
    """Strip punctuation so FTS5 MATCH never trips on stray operators."""
    cleaned = _FTS_SAFE.sub(" ", query).strip()
    tokens = [t for t in cleaned.split() if len(t) > 1]
    if not tokens:
        return ""
    # OR the tokens so partial matches still rank.
    return " OR ".join(tokens[:10])


def retrieve(query: str, lang: str = "en", k: int = RAG_TOP_K) -> List[dict]:
    fts_query = _sanitize(query)
    if not fts_query:
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT a.id, a.title, a.body, a.category, a.lang,
                      bm25(advisories_fts) AS score
               FROM advisories_fts
               JOIN advisories a ON a.id = advisories_fts.rowid
               WHERE advisories_fts MATCH ? AND a.lang = ?
               ORDER BY score
               LIMIT ?""",
            (fts_query, lang, k),
        ).fetchall()
        if not rows:
            rows = conn.execute(
                """SELECT a.id, a.title, a.body, a.category, a.lang,
                          bm25(advisories_fts) AS score
                   FROM advisories_fts
                   JOIN advisories a ON a.id = advisories_fts.rowid
                   WHERE advisories_fts MATCH ?
                   ORDER BY score
                   LIMIT ?""",
                (fts_query, k),
            ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        conn.close()

    return [dict(r) for r in rows]


def format_context(snippets: List[dict]) -> str:
    if not snippets:
        return ""
    parts = []
    for i, s in enumerate(snippets, 1):
        parts.append(f"[{i}] {s['title']} ({s['category']}): {s['body']}")
    return "\n".join(parts)
