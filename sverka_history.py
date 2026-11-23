"""Локальное хранилище результатов и отметок ACT SVERKA."""

from contextlib import closing, contextmanager
from datetime import date, datetime, timezone
import json
import sqlite3


REVIEW_STATES = {
    "pending": "Нужно проверить",
    "checked": "Проверено",
    "request": "Запросить документ",
}


def encode_date(value):
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Значение типа {type(value).__name__} нельзя сохранить")


class ReconciliationHistory:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connection(self):
        with closing(sqlite3.connect(self.path, timeout=5)) as conn, conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sverka_stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total INTEGER NOT NULL CHECK (total >= 0)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reconciliations (
                    id INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    first_file TEXT NOT NULL,
                    second_file TEXT NOT NULL,
                    period TEXT NOT NULL,
                    snapshot TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_marks (
                    reconciliation_id INTEGER NOT NULL REFERENCES reconciliations(id),
                    case_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'checked', 'request')),
                    PRIMARY KEY (reconciliation_id, case_id)
                )
            """)
            yield conn

    def total(self):
        with self.connection() as conn:
            row = conn.execute("SELECT total FROM sverka_stats WHERE id = 1").fetchone()
            return row["total"] if row else 0

    def save(self, result):
        snapshot = json.dumps(result, default=encode_date, ensure_ascii=False, separators=(",", ":"))
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO reconciliations (created_at, first_file, second_file, period, snapshot)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(timezone.utc).isoformat(), *result["files"], result["period"], snapshot))
            record_id = cursor.lastrowid
            marks = [
                (record_id, f"{act}:{source}")
                for act, indices in enumerate(result["only"], start=1)
                for source in indices
            ]
            conn.executemany("""
                INSERT INTO reconciliation_marks (reconciliation_id, case_id, status) VALUES (?, ?, 'pending')
            """, marks)
            conn.execute("""
                INSERT INTO sverka_stats (id, total) VALUES (1, 1)
                ON CONFLICT (id) DO UPDATE SET total = total + 1
            """)
            return record_id

    def list(self):
        with self.connection() as conn:
            return conn.execute("""
                SELECT r.id, r.created_at, r.closed_at, r.first_file, r.second_file, r.period,
                       COUNT(CASE WHEN m.status = 'pending' THEN 1 END) AS pending,
                       COUNT(CASE WHEN m.status = 'checked' THEN 1 END) AS checked,
                       COUNT(CASE WHEN m.status = 'request' THEN 1 END) AS requested
                FROM reconciliations AS r
                LEFT JOIN reconciliation_marks AS m ON m.reconciliation_id = r.id
                GROUP BY r.id
                ORDER BY r.id DESC
            """).fetchall()

    def load(self, record_id):
        with self.connection() as conn:
            conn.execute("BEGIN")
            row = conn.execute("SELECT * FROM reconciliations WHERE id = ?", (record_id,)).fetchone()
            if row is None:
                return None
            marks = conn.execute("""
                SELECT case_id, status FROM reconciliation_marks WHERE reconciliation_id = ?
            """, (record_id,)).fetchall()
        record = dict(row)
        record["marks"] = {mark["case_id"]: mark["status"] for mark in marks}
        record["result"] = json.loads(record.pop("snapshot"))
        for operations in record["result"]["ops"]:
            for operation in operations:
                operation["date"] = date.fromisoformat(operation["date"])
        return record

    def mark(self, record_id, case_id, status):
        if status not in REVIEW_STATES:
            raise ValueError("Неизвестная отметка проверки")
        with self.connection() as conn:
            cursor = conn.execute("""
                UPDATE reconciliation_marks SET status = ?
                WHERE reconciliation_id = ? AND case_id = ?
                  AND EXISTS (SELECT 1 FROM reconciliations WHERE id = ? AND closed_at IS NULL)
            """, (status, record_id, case_id, record_id))
            return cursor.rowcount == 1

    def finish(self, record_id):
        with self.connection() as conn:
            cursor = conn.execute("""
                UPDATE reconciliations SET closed_at = ?
                WHERE id = ? AND closed_at IS NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM reconciliation_marks
                    WHERE reconciliation_id = ? AND status <> 'checked'
                  )
            """, (datetime.now(timezone.utc).isoformat(), record_id, record_id))
            return cursor.rowcount == 1
