from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ppe_decision.state_machine import PPEEvent


SCHEMA = """
CREATE TABLE IF NOT EXISTS ppe_events (
    event_id TEXT PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    track_id TEXT NOT NULL,
    violation_type TEXT NOT NULL,
    person_confidence REAL NOT NULL,
    helmet_confidence REAL NOT NULL,
    vest_confidence REAL NOT NULL,
    source TEXT NOT NULL,
    image_path TEXT,
    alert_message TEXT NOT NULL,
    alert_status TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL
)
"""


class EventRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def insert(
        self,
        event: PPEEvent,
        image_path: str | None = None,
        alert_status: str = "queued",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        values = (
            event.event_id,
            datetime.now(timezone.utc).isoformat(),
            event.track_id,
            event.violation_type,
            event.person_confidence,
            event.helmet_confidence,
            event.vest_confidence,
            event.source,
            image_path,
            event.alert_message,
            alert_status,
            0,
            json.dumps(metadata or {}, sort_keys=True),
        )
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO ppe_events (
                    event_id, timestamp_utc, track_id, violation_type,
                    person_confidence, helmet_confidence, vest_confidence,
                    source, image_path, alert_message, alert_status,
                    acknowledged, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values,
            )

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM ppe_events").fetchone()[0])

    def list_events(self) -> list[sqlite3.Row]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            return list(connection.execute(
                "SELECT * FROM ppe_events ORDER BY timestamp_utc"
            ))
