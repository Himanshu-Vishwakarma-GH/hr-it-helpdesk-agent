"""Support-ticket store backed by SQLite (local file, no server needed).

Ticket IDs look like TKT-1001, TKT-1002, ... and keep counting across runs.
Statuses: Open -> In Progress -> Resolved, or Open -> Escalated.

The connection is opened with check_same_thread=False and guarded by a
lock, because FastAPI serves requests from a thread pool while the store
is created once at startup.
"""
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "tickets.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'IT',
    priority TEXT NOT NULL DEFAULT 'Normal',
    status TEXT NOT NULL DEFAULT 'Open',
    requester TEXT NOT NULL DEFAULT 'employee',
    created_at TEXT NOT NULL
);
"""


class TicketStore:
    def __init__(self, db_path: Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def _next_ticket_id(self) -> str:
        with self._lock:
            row = self._conn.execute("SELECT MAX(id) AS m FROM tickets").fetchone()
        number = (row["m"] or 0) + 1001
        return f"TKT-{number}"

    def create(self, title: str, description: str, category: str = "IT",
               priority: str = "Normal", requester: str = "employee") -> dict:
        ticket_id = self._next_ticket_id()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock:
            self._conn.execute(
                "INSERT INTO tickets (ticket_id, title, description, category, "
                "priority, status, requester, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'Open', ?, ?)",
                (ticket_id, title, description, category, priority, requester, now),
            )
            self._conn.commit()
        return self.get(ticket_id)

    def get(self, ticket_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id.upper(),)
            ).fetchone()
        return dict(row) if row else None

    def list_all(self, status: str | None = None) -> list[dict]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM tickets WHERE status = ? ORDER BY id", (status,)
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def escalate(self, ticket_id: str) -> dict | None:
        ticket = self.get(ticket_id)
        if ticket is None:
            return None
        if ticket["status"] in ("Resolved", "Escalated"):
            return ticket
        with self._lock:
            self._conn.execute(
                "UPDATE tickets SET status = 'Escalated' WHERE ticket_id = ?",
                (ticket["ticket_id"],),
            )
            self._conn.commit()
        return self.get(ticket["ticket_id"])

    def close(self) -> None:
        self._conn.close()
