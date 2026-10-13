"""Tiny SQLite store for posts and sync state (stdlib only, no ORM)."""

import json
import os
import sqlite3
import threading

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    channel TEXT NOT NULL,
    date TEXT NOT NULL,
    text_html TEXT NOT NULL DEFAULT '',
    media_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

_lock = threading.Lock()


class Store:
    def __init__(self, path):
        self.path = path
        self._init()

    def _connect(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init(self):
        with _lock:
            conn = self._connect()
            try:
                conn.executescript(_SCHEMA)
                conn.commit()
            finally:
                conn.close()

    def upsert_post(self, post):
        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO posts"
                    " (id, channel, date, text_html, media_json)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (
                        post["id"],
                        post["channel"],
                        post["date"],
                        post["text_html"],
                        json.dumps(post["attachments"], ensure_ascii=False),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def has_post(self, post_id):
        with _lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT 1 FROM posts WHERE id = ?", (post_id,)
                ).fetchone()
                return row is not None
            finally:
                conn.close()

    def posts_after(self, post_id, limit):
        with _lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT id, channel, date, text_html, media_json"
                    " FROM posts WHERE id > ? ORDER BY id ASC LIMIT ?",
                    (post_id, limit),
                ).fetchall()
            finally:
                conn.close()
        out = []
        for row in rows:
            out.append(
                {
                    "id": row[0],
                    "channel": row[1],
                    "date": row[2],
                    "text_html": row[3],
                    "attachments": json.loads(row[4] or "[]"),
                }
            )
        return out

    def get_state(self, key, default=""):
        with _lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT value FROM state WHERE key = ?", (key,)
                ).fetchone()
                return row[0] if row else default
            finally:
                conn.close()

    def set_state(self, key, value):
        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                    (key, str(value)),
                )
                conn.commit()
            finally:
                conn.close()
