"""
SQLite persistence for inspection history (assignment section 15).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.models.inspection_result import InspectionResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id TEXT PRIMARY KEY,
    timestamp     TEXT NOT NULL,
    component     TEXT NOT NULL,
    condition     TEXT NOT NULL,
    defect        TEXT,
    severity      TEXT,
    location      TEXT,
    confidence    REAL NOT NULL,
    reason        TEXT,
    image_path    TEXT
);
"""


class InspectionRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def save(self, result: InspectionResult) -> None:
        row = result.to_row()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO inspections
                    (inspection_id, timestamp, component, condition, defect,
                     severity, location, confidence, reason, image_path)
                VALUES
                    (:inspection_id, :timestamp, :component, :condition, :defect,
                     :severity, :location, :confidence, :reason, :image_path)
                """,
                row,
            )

    def list_recent(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM inspections ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in cur.fetchall()]

    def get(self, inspection_id: str) -> dict | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
