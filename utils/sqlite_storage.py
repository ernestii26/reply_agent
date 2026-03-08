"""
SQLite-backed storage backend implementing the same public API as PostStorage.

提供方法：load, save, contains, count, get_recent, clear, export_to_list, save_reply
"""
import sqlite3
import threading
import time
import hashlib
import json
from pathlib import Path
from typing import Set, List
from config.settings import FILES


class SQLitePostStorage:
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else Path(FILES.get("db_path"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Connection per instance; check_same_thread=False allows access from other threads
        self._conn = sqlite3.connect(str(self.db_path), timeout=30, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute("PRAGMA temp_store=MEMORY;")
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._ensure_tables()

    def _ensure_tables(self):
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS replied_posts (
                    post_id TEXT PRIMARY KEY,
                    inserted_at INTEGER NOT NULL,
                    source TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS replies_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    title TEXT,
                    reply TEXT,
                    timestamp INTEGER NOT NULL,
                    reply_hash TEXT
                )
                """
            )
            # Unique index to avoid exact duplicate replies (optional)
            self._conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_replies_post_hash ON replies_log(post_id, reply_hash)"
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_replies_ts ON replies_log(timestamp)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_replied_ts ON replied_posts(inserted_at)")

    def load(self) -> Set[str]:
        cur = self._conn.execute("SELECT post_id FROM replied_posts")
        return set(row[0] for row in cur.fetchall())

    def save(self, post_id: str) -> bool:
        ts = int(time.time())
        try:
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO replied_posts(post_id, inserted_at, source) VALUES (?, ?, ?)",
                        (post_id, ts, "app"),
                    )
            return True
        except Exception:
            return False

    def contains(self, post_id: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM replied_posts WHERE post_id = ? LIMIT 1", (post_id,))
        return cur.fetchone() is not None

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(1) FROM replied_posts")
        return cur.fetchone()[0]

    def get_recent(self, n: int = 5) -> List[str]:
        cur = self._conn.execute(
            "SELECT post_id FROM replied_posts ORDER BY inserted_at DESC LIMIT ?",
            (n,),
        )
        rows = [r[0] for r in cur.fetchall()]
        # original file-based impl returns in chronological order (oldest->newest for the last N)
        return list(reversed(rows))

    def clear(self) -> bool:
        try:
            with self._lock:
                with self._conn:
                    self._conn.execute("DELETE FROM replies_log")
                    self._conn.execute("DELETE FROM replied_posts")
            return True
        except Exception:
            return False

    def export_to_list(self) -> List[str]:
        cur = self._conn.execute("SELECT post_id FROM replied_posts ORDER BY inserted_at")
        return [r[0] for r in cur.fetchall()]

    def save_reply(self, post_id: str, title: str, reply_content: str) -> bool:
        try:
            ts = int(time.time())
            reply_hash = hashlib.sha256(reply_content.encode("utf-8")).hexdigest()
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO replies_log(post_id, title, reply, timestamp, reply_hash) VALUES (?, ?, ?, ?, ?)",
                        (post_id, title, reply_content, ts, reply_hash),
                    )
            return True
        except Exception:
            return False

    # Compatibility exports
    def export_to_text(self, filepath_out: str):
        p = Path(filepath_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for pid in self.export_to_list():
                f.write(f"{pid}\n")

    def export_replies_jsonl(self, filepath_out: str):
        p = Path(filepath_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        cur = self._conn.execute("SELECT timestamp, post_id, title, reply FROM replies_log ORDER BY timestamp")
        with open(p, "w", encoding="utf-8") as f:
            for row in cur.fetchall():
                entry = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[0])),
                    "post_id": row[1],
                    "title": row[2],
                    "reply": row[3],
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
