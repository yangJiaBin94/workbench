import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from models.session import Session, Message


class SessionStore:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "workbench.db"
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), isolation_level=None)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
            self._migrate()
        return self._conn

    def _migrate(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                working_dir TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                event_type TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
        """)
        try:
            self.conn.execute("ALTER TABLE sessions ADD COLUMN total_tokens INTEGER DEFAULT 0")
        except Exception:
            pass

    def _row_to_session(self, row) -> Session:
        d = dict(row)
        d.pop("total_tokens", None)
        return Session(**d)

    # ---- sessions ----

    def create_session(self, name: str = "", working_dir: str = "") -> Session:
        if not name:
            name = "新会话"
        session = Session(name=name, working_dir=working_dir)
        cur = self.conn.execute(
            "INSERT INTO sessions (name, working_dir, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session.name, session.working_dir, session.created_at, session.updated_at),
        )
        session.id = cur.lastrowid
        return session

    def list_sessions(self) -> list[Session]:
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY id ASC"
        ).fetchall()
        return [self._row_to_session(r) for r in rows]

    def get_session(self, session_id: int) -> Optional[Session]:
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return self._row_to_session(row) if row else None

    def update_session(self, session: Session):
        self.conn.execute(
            "UPDATE sessions SET name=?, working_dir=?, updated_at=? WHERE id=?",
            (session.name, session.working_dir, session.updated_at, session.id),
        )

    def update_session_name(self, session_id: int, name: str):
        self.conn.execute(
            "UPDATE sessions SET name=?, updated_at=? WHERE id=?",
            (name, datetime.now().isoformat(), session_id),
        )

    def get_recent_sessions(self, limit: int = 10) -> list[Session]:
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_session(r) for r in rows]

    def delete_session(self, session_id: int):
        self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    # ---- messages ----

    def save_message(self, message: Message) -> int:
        cur = self.conn.execute(
            "INSERT INTO messages (session_id, role, content, event_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (message.session_id, message.role, message.content, message.event_type, message.created_at),
        )
        message.id = cur.lastrowid
        self.conn.execute(
            "UPDATE sessions SET updated_at=? WHERE id=?",
            (message.created_at, message.session_id),
        )
        return message.id

    def update_message(self, message: Message):
        self.conn.execute(
            "UPDATE messages SET content=?, event_type=? WHERE id=?",
            (message.content, message.event_type, message.id),
        )

    def get_messages(self, session_id: int) -> list[Message]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return [Message(**dict(r)) for r in rows]

    def get_recent_messages(self, session_id: int, limit: int = 6) -> list[Message]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE session_id=? AND role IN ('user','assistant') ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        rows.reverse()
        return [Message(**dict(r)) for r in rows]

    def get_last_message(self, session_id: int, role: str) -> Optional[Message]:
        row = self.conn.execute(
            "SELECT * FROM messages WHERE session_id=? AND role=? ORDER BY id DESC LIMIT 1",
            (session_id, role),
        ).fetchone()
        return Message(**dict(row)) if row else None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
