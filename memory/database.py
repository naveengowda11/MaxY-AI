"""SQLite persistence for conversations and messages."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, id);
                """
            )

    def create_conversation(self, title: str = "New conversation") -> str:
        conversation_id = str(uuid4())
        now = utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO conversations(id, title, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (conversation_id, title, now, now),
            )
        return conversation_id

    def conversation_exists(self, conversation_id: str) -> bool:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return row is not None

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        now = utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO messages(conversation_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, now),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )

    def get_recent_messages(
        self, conversation_id: str, limit: int = 12
    ) -> list[dict[str, str]]:
        safe_limit = max(1, min(int(limit), 100))
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (conversation_id, safe_limit),
            ).fetchall()
        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    def get_messages(self, conversation_id: str) -> list[dict[str, str]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT role, content, created_at FROM messages "
                "WHERE conversation_id = ? ORDER BY id ASC",
                (conversation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_conversations(self, limit: int = 30) -> list[dict[str, str]]:
        safe_limit = max(1, min(int(limit), 100))
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, title, created_at, updated_at FROM conversations "
                "ORDER BY updated_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [dict(row) for row in rows]
