"""SQLite persistence. Knows nothing about booking rules."""
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS units (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
    id           INTEGER PRIMARY KEY,
    unit_id      TEXT NOT NULL REFERENCES units(id),
    requester    TEXT NOT NULL,
    start        TEXT NOT NULL,
    end          TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('ACTIVE', 'CANCELLED')),
    created_at   TEXT NOT NULL,
    cancelled_at TEXT
);
"""


@dataclass(frozen=True)
class Unit:
    id: str
    name: str


@dataclass(frozen=True)
class Reservation:
    id: int
    unit_id: str
    requester: str
    start: str
    end: str
    status: str
    created_at: str
    cancelled_at: str | None


class Repository:
    """Queries bound to one open transaction."""

    def __init__(self, conn):
        self._conn = conn

    def add_unit_if_missing(self, unit_id, name):
        self._conn.execute(
            "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)", (unit_id, name)
        )

    def units(self):
        rows = self._conn.execute("SELECT id, name FROM units ORDER BY rowid")
        return [Unit(**dict(row)) for row in rows]

    def unit_exists(self, unit_id):
        row = self._conn.execute("SELECT 1 FROM units WHERE id = ?", (unit_id,))
        return row.fetchone() is not None

    def insert_reservation(self, unit_id, requester, start, end, created_at):
        cursor = self._conn.execute(
            "INSERT INTO reservations (unit_id, requester, start, end, status, created_at) "
            "VALUES (?, ?, ?, ?, 'ACTIVE', ?)",
            (unit_id, requester, start, end, created_at),
        )
        return self.get_reservation(cursor.lastrowid)

    def get_reservation(self, reservation_id):
        row = self._conn.execute(
            "SELECT * FROM reservations WHERE id = ?", (reservation_id,)
        ).fetchone()
        return Reservation(**dict(row)) if row else None

    def reservations(self, unit_id=None, include_cancelled=False):
        query = "SELECT * FROM reservations WHERE 1 = 1"
        params = []
        if unit_id is not None:
            query += " AND unit_id = ?"
            params.append(unit_id)
        if not include_cancelled:
            query += " AND status = 'ACTIVE'"
        query += " ORDER BY start, id"
        return [Reservation(**dict(row)) for row in self._conn.execute(query, params)]

    def mark_cancelled(self, reservation_id, cancelled_at):
        self._conn.execute(
            "UPDATE reservations SET status = 'CANCELLED', cancelled_at = ? WHERE id = ?",
            (cancelled_at, reservation_id),
        )

    def delete_all_reservations(self):
        self._conn.execute("DELETE FROM reservations")


class Database:
    def __init__(self, db_path):
        self._path = Path(db_path)

    @contextmanager
    def transaction(self, write=False):
        """One transaction. `write=True` takes the write lock up front
        (BEGIN IMMEDIATE) so a check followed by an insert cannot interleave
        with another writer."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(SCHEMA)
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            try:
                yield Repository(conn)
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")
        finally:
            conn.close()
