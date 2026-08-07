import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_PATH, DEFAULT_SETTINGS


def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL DEFAULT 'User',
                email TEXT,
                avatar TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                title TEXT NOT NULL DEFAULT 'New Chat',
                pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                attachments TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chat_history(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                UNIQUE(user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS pdf_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                filename TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chat_history(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
            CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_chat_history_updated ON chat_history(updated_at);
        """)

        user = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
        if not user:
            now = datetime.utcnow().isoformat()
            conn.execute(
                "INSERT INTO users (username, email, created_at) VALUES (?, ?, ?)",
                ("User", "user@gemini-ai.local", now),
            )
            for key, value in DEFAULT_SETTINGS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings (user_id, key, value) VALUES (1, ?, ?)",
                    (key, value),
                )
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def get_settings(user_id=1):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT key, value FROM settings WHERE user_id = ?", (user_id,)
        ).fetchall()
    settings = dict(DEFAULT_SETTINGS)
    settings.update({row["key"]: row["value"] for row in rows})
    return settings


def update_setting(key, value, user_id=1):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value""",
            (user_id, key, str(value)),
        )
        conn.commit()


def create_chat(title="New Chat", user_id=1):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO chat_history (user_id, title, created_at, updated_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, title, now, now),
        )
        conn.commit()
        return cursor.lastrowid


def get_chat(chat_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM chat_history WHERE id = ?", (chat_id,)
        ).fetchone()


def get_all_chats(user_id=1, search=""):
    with get_connection() as conn:
        if search:
            query = """
                SELECT DISTINCT c.* FROM chat_history c
                LEFT JOIN messages m ON m.chat_id = c.id
                WHERE c.user_id = ? AND (c.title LIKE ? OR m.content LIKE ?)
                ORDER BY c.pinned DESC, c.updated_at DESC
            """
            pattern = f"%{search}%"
            return conn.execute(query, (user_id, pattern, pattern)).fetchall()
        return conn.execute(
            """SELECT * FROM chat_history WHERE user_id = ?
               ORDER BY pinned DESC, updated_at DESC""",
            (user_id,),
        ).fetchall()


def update_chat(chat_id, title=None, pinned=None):
    with get_connection() as conn:
        if title is not None:
            conn.execute(
                "UPDATE chat_history SET title = ?, updated_at = ? WHERE id = ?",
                (title, datetime.utcnow().isoformat(), chat_id),
            )
        if pinned is not None:
            conn.execute(
                "UPDATE chat_history SET pinned = ? WHERE id = ?",
                (1 if pinned else 0, chat_id),
            )
        conn.commit()


def delete_chat(chat_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM pdf_documents WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM chat_history WHERE id = ?", (chat_id,))
        conn.commit()


def clear_all_chats(user_id=1):
    with get_connection() as conn:
        chat_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM chat_history WHERE user_id = ?", (user_id,)
            ).fetchall()
        ]
        for chat_id in chat_ids:
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.execute("DELETE FROM pdf_documents WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.commit()


def add_message(chat_id, role, content, attachments=None):
    now = datetime.utcnow().isoformat()
    attachments_json = json.dumps(attachments or [])
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO messages (chat_id, role, content, attachments, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (chat_id, role, content, attachments_json, now),
        )
        conn.execute(
            "UPDATE chat_history SET updated_at = ? WHERE id = ?",
            (now, chat_id),
        )
        conn.commit()
        return cursor.lastrowid


def get_messages(chat_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,),
        ).fetchall()

    messages = []
    for row in rows:
        msg = dict(row)
        try:
            msg["attachments"] = json.loads(msg.get("attachments") or "[]")
        except (ValueError, TypeError):
            msg["attachments"] = []
        messages.append(msg)

    return messages


def delete_last_assistant_message(chat_id):
    with get_connection() as conn:
        last = conn.execute(
            """SELECT id FROM messages WHERE chat_id = ? AND role = 'assistant'
               ORDER BY created_at DESC LIMIT 1""",
            (chat_id,),
        ).fetchone()
        if last:
            conn.execute("DELETE FROM messages WHERE id = ?", (last["id"],))
            conn.commit()
            return True
    return False


def save_pdf_document(chat_id, filename, extracted_text):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO pdf_documents (chat_id, filename, extracted_text, created_at)
               VALUES (?, ?, ?, ?)""",
            (chat_id, filename, extracted_text, now),
        )
        conn.commit()
        return cursor.lastrowid


def get_pdf_documents(chat_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM pdf_documents WHERE chat_id = ? ORDER BY created_at DESC",
            (chat_id,),
        ).fetchall()
    return [dict(row) for row in rows]
