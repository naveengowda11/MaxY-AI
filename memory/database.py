"""SQLite persistence for conversations and messages."""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


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
                CREATE TABLE IF NOT EXISTS user_memories (
                    id TEXT PRIMARY KEY, content TEXT NOT NULL, category TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS personal_tasks (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, due_at TEXT,
                    status TEXT NOT NULL CHECK(status IN ('open', 'completed')),
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tool_proposals (
                    id TEXT PRIMARY KEY, tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL, expires_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                        ('pending', 'executing', 'completed', 'expired', 'failed'))
                );
                CREATE TABLE IF NOT EXISTS tool_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL,
                    tool_name TEXT NOT NULL, proposal_id TEXT NOT NULL,
                    detail TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tool_audit_created ON tool_audit(created_at);
                """
            )


    def save_memory(self, content: str, category: str = "general") -> dict[str, str]:
        cleaned = " ".join(content.strip().split())
        if not cleaned or len(cleaned) > 1000:
            raise ValueError("Memory must contain 1 to 1000 characters.")
        category = category.strip().lower()[:40] or "general"
        memory_id = str(uuid4())
        now = utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO user_memories(id, content, category, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (memory_id, cleaned, category, now, now),
            )
        return {"id": memory_id, "content": cleaned, "category": category,
                "created_at": now, "updated_at": now}

    def list_memories(self, limit: int = 100) -> list[dict[str, str]]:
        safe_limit = max(1, min(int(limit), 250))
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, content, category, created_at, updated_at "
                "FROM user_memories ORDER BY created_at DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_memory(self, memory_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM user_memories WHERE id = ?", (memory_id,)
            )
        return cursor.rowcount == 1

    def clear_memories(self) -> int:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM user_memories")
        return cursor.rowcount

    def create_task(self, title: str, due_at: str | None = None) -> dict[str, str]:
        cleaned = " ".join(title.strip().split())
        if not cleaned or len(cleaned) > 300:
            raise ValueError("Task must contain 1 to 300 characters.")
        task_id = str(uuid4())[:8]
        now = utc_now()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO personal_tasks(id, title, due_at, status, created_at, updated_at) "
                "VALUES (?, ?, ?, 'open', ?, ?)",
                (task_id, cleaned, due_at, now, now),
            )
        return {"id": task_id, "title": cleaned, "due_at": due_at or "",
                "status": "open", "created_at": now, "updated_at": now}

    def list_tasks(self, include_completed: bool = True, limit: int = 100) -> list[dict[str, str]]:
        safe_limit = max(1, min(int(limit), 250))
        query = ("SELECT id, title, due_at, status, created_at, updated_at "
                 "FROM personal_tasks ")
        if not include_completed:
            query += "WHERE status = 'open' "
        query += "ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END, created_at DESC LIMIT ?"
        with self._connection() as connection:
            rows = connection.execute(query, (safe_limit,)).fetchall()
        return [dict(row) for row in rows]

    def set_task_status(self, task_id: str, status: str) -> bool:
        if status not in {"open", "completed"}:
            raise ValueError("Task status must be open or completed.")
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE personal_tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, utc_now(), task_id),
            )
        return cursor.rowcount == 1

    def delete_task(self, task_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM personal_tasks WHERE id = ?", (task_id,))
        return cursor.rowcount == 1

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

    def create_tool_proposal(self, proposal_id: str, tool_name: str,
                             arguments_json: str, expires_at: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO tool_proposals(id, tool_name, arguments_json, expires_at, status) "
                "VALUES (?, ?, ?, ?, 'pending')",
                (proposal_id, tool_name, arguments_json, expires_at),
            )

    def get_tool_proposal(self, proposal_id: str) -> dict[str, str] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id, tool_name, arguments_json, expires_at, status "
                "FROM tool_proposals WHERE id = ? AND status = 'pending'",
                (proposal_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_tool_proposal(self, proposal_id: str, status: str,
                             expected_status: str | None = None) -> bool:
        valid = {"pending", "executing", "completed", "expired", "failed"}
        if status not in valid:
            raise ValueError("Invalid tool proposal status.")
        with self._connection() as connection:
            if expected_status:
                cursor = connection.execute(
                    "UPDATE tool_proposals SET status = ? WHERE id = ? AND status = ?",
                    (status, proposal_id, expected_status),
                )
            else:
                cursor = connection.execute(
                    "UPDATE tool_proposals SET status = ? WHERE id = ?",
                    (status, proposal_id),
                )
        return cursor.rowcount == 1

    def add_audit_event(self, event: str, tool_name: str, proposal_id: str,
                         detail: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO tool_audit(event, tool_name, proposal_id, detail, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event, tool_name, proposal_id, detail[:500], utc_now()),
            )

    def get_audit_events(self, limit: int = 100) -> list[dict[str, str]]:
        safe_limit = max(1, min(int(limit), 500))
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT event, tool_name, proposal_id, detail, created_at "
                "FROM tool_audit ORDER BY id DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [dict(row) for row in rows]
