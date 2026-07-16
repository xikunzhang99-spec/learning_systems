import os
import sqlite3
from datetime import datetime
from config import settings

DB_PATH = os.path.join(os.path.dirname(settings.DATABASE_PATH), "terms.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL UNIQUE,
            domain TEXT DEFAULT '',
            source_urls TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.commit()
    conn.close()


def term_exists(term: str) -> bool:
    conn = _get_conn()
    row = conn.execute("SELECT 1 FROM terms WHERE term = ?", (term,)).fetchone()
    conn.close()
    return row is not None


def insert_term(term: str, domain: str = "", source_urls: list = None):
    conn = _get_conn()
    urls = ",".join(source_urls) if source_urls else ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT OR REPLACE INTO terms (term, domain, source_urls, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (term, domain, urls, now),
    )
    conn.commit()
    conn.close()


def list_terms(limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM terms ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_term(term: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM terms WHERE term = ?", (term,)).fetchone()
    conn.close()
    return dict(row) if row else None


init_db()
