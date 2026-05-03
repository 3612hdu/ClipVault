import sqlite3
import time
import os
from config import DB_PATH, FREE_MAX_ITEMS


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                source_app TEXT DEFAULT '',
                is_pinned INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clips_created
            ON clips(created_at DESC)
        """)


def add_clip(content, content_type="text", source_app=""):
    with get_conn() as conn:
        # 去重：如果与最新一条相同，跳过
        cur = conn.execute(
            "SELECT content FROM clips ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row and row[0] == content:
            # 更新时间戳
            conn.execute(
                "UPDATE clips SET created_at = ? WHERE id = (SELECT id FROM clips ORDER BY created_at DESC LIMIT 1)",
                (time.time(),),
            )
            return None

        conn.execute(
            "INSERT INTO clips (content, content_type, source_app, created_at) VALUES (?, ?, ?, ?)",
            (content, content_type, source_app, time.time()),
        )

        # 免费版限制：超过上限后删除最旧的非固定条目
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        import json
        max_items = FREE_MAX_ITEMS
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                s = json.load(f)
                max_items = s.get("max_items", FREE_MAX_ITEMS)

        conn.execute("""
            DELETE FROM clips WHERE id IN (
                SELECT id FROM clips
                WHERE is_pinned = 0
                ORDER BY created_at ASC
                LIMIT max(0, (SELECT COUNT(*) FROM clips) - ?)
            )
        """, (max_items,))
        conn.commit()
        return True


def get_clips(limit=50, offset=0, search=""):
    with get_conn() as conn:
        if search:
            cur = conn.execute(
                "SELECT id, content, content_type, source_app, is_pinned, created_at FROM clips "
                "WHERE content LIKE ? ORDER BY is_pinned DESC, created_at DESC LIMIT ? OFFSET ?",
                (f"%{search}%", limit, offset),
            )
        else:
            cur = conn.execute(
                "SELECT id, content, content_type, source_app, is_pinned, created_at FROM clips "
                "ORDER BY is_pinned DESC, created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        return cur.fetchall()


def toggle_pin(clip_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE clips SET is_pinned = 1 - is_pinned WHERE id = ?", (clip_id,)
        )
        conn.commit()


def delete_clip(clip_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        conn.commit()


def clear_all():
    with get_conn() as conn:
        conn.execute("DELETE FROM clips WHERE is_pinned = 0")
        conn.commit()


def get_count():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
