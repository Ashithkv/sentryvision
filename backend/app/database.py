"""
Very small SQLite wrapper for detection history.

No ORM — this project only ever does three things to the database
(insert a detection, list detections, clear detections), so plain
sqlite3 + parameterized queries is simpler to read and explain than
pulling in SQLAlchemy.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    inside_roi INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(_SCHEMA)


def insert_detection(object_class: str, confidence: float, inside_roi: bool,
                      timestamp: Optional[str] = None) -> int:
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO detections (object_class, confidence, inside_roi, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (object_class, confidence, int(inside_roi), ts),
        )
        return cur.lastrowid


def list_detections(limit: int = 200, only_roi: bool = False) -> list[dict]:
    query = "SELECT id, object_class, confidence, inside_roi, timestamp FROM detections"
    if only_roi:
        query += " WHERE inside_roi = 1"
    query += " ORDER BY id DESC LIMIT ?"
    with get_connection() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def clear_detections() -> int:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM detections")
        return cur.rowcount
