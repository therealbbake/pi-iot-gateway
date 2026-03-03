import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, Iterable, Optional

DB_PATH = Path("data/telemetry.db")


@contextmanager
def db_connection() -> Generator[sqlite3.Connection, None, None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS temperature_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                temperature_f REAL NOT NULL,
                transport_status TEXT NOT NULL,
                transport_error TEXT
            );
            """
        )
        conn.commit()


@dataclass
class Reading:
    recorded_at: datetime
    temperature_c: float
    temperature_f: float
    transport_status: str
    transport_error: Optional[str]


def add_reading(reading: Reading) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO temperature_readings (
                recorded_at, temperature_c, temperature_f, transport_status, transport_error
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                reading.recorded_at.isoformat(),
                reading.temperature_c,
                reading.temperature_f,
                reading.transport_status,
                reading.transport_error,
            ),
        )
        conn.commit()


def list_readings(limit: int = 100) -> Iterable[Reading]:
    with db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT recorded_at, temperature_c, temperature_f, transport_status, transport_error
            FROM temperature_readings
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        for row in cursor:
            yield Reading(
                recorded_at=datetime.fromisoformat(row["recorded_at"]),
                temperature_c=row["temperature_c"],
                temperature_f=row["temperature_f"],
                transport_status=row["transport_status"],
                transport_error=row["transport_error"],
            )

