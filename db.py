import os
import sqlite3
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    format TEXT,
    title TEXT,
    status TEXT NOT NULL,
    items INTEGER,
    file TEXT,
    bytes INTEGER,
    created_at TEXT,
    finished_at TEXT,
    error TEXT
);
"""


def _connect(path):
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(path):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with closing(_connect(path)) as conn, conn:
        conn.executescript(SCHEMA)


def insert_download(path, download_id, url, fmt, created_at):
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            "INSERT OR REPLACE INTO downloads (id, url, format, status, created_at)"
            " VALUES (?, ?, ?, 'queued', ?)",
            (download_id, url, fmt, created_at),
        )


def finish_download(path, download_id, status, title, items, file, size, error, finished_at):
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            "UPDATE downloads SET status=?, title=?, items=?, file=?, bytes=?,"
            " error=?, finished_at=? WHERE id=?",
            (status, title, items, file, size, error, finished_at, download_id),
        )


def get_download(path, download_id):
    with closing(_connect(path)) as conn:
        row = conn.execute(
            "SELECT * FROM downloads WHERE id = ?", (download_id,)
        ).fetchone()
        return dict(row) if row else None


def list_downloads(path, query=None, limit=200):
    sql = "SELECT * FROM downloads"
    args = []
    if query:
        sql += " WHERE title LIKE ? OR url LIKE ?"
        like = f"%{query}%"
        args += [like, like]
    sql += " ORDER BY created_at DESC LIMIT ?"
    args.append(limit)
    with closing(_connect(path)) as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def delete_download(path, download_id):
    """Delete one history row. Returns the number of rows removed (0 or 1)."""
    with closing(_connect(path)) as conn, conn:
        return conn.execute("DELETE FROM downloads WHERE id = ?", (download_id,)).rowcount


def delete_all_downloads(path):
    """Delete every history row. Returns the number of rows removed."""
    with closing(_connect(path)) as conn, conn:
        return conn.execute("DELETE FROM downloads").rowcount


def mark_interrupted(path):
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            "UPDATE downloads SET status='interrupted' WHERE status IN ('queued', 'running')"
        )
