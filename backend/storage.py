import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, Iterable, Optional, List

import yaml

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
        # Create sensors table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sensors (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL
            );
            """
        )

        # Check if temperature_readings needs migration for FK
        cursor = conn.execute("PRAGMA table_info(temperature_readings)")
        columns = [row[1] for row in cursor.fetchall()]
        has_fk = any(col == 'sensor_id' for col in columns)  # Simplified check; assume if sensor_id exists, FK is set

        if not has_fk:
            if columns:  # Table exists, migrate
                conn.execute("ALTER TABLE temperature_readings RENAME TO old_temperature_readings")
                conn.execute(
                    """
                    CREATE TABLE temperature_readings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recorded_at TEXT NOT NULL,
                        temperature_c REAL NOT NULL,
                        temperature_f REAL NOT NULL,
                        transport_status TEXT NOT NULL,
                        transport_error TEXT,
                        sensor_id TEXT,
                        FOREIGN KEY(sensor_id) REFERENCES sensors(id) ON DELETE CASCADE
                    );
                    """
                )
                conn.execute(
                    """
                    INSERT INTO temperature_readings 
                    (recorded_at, temperature_c, temperature_f, transport_status, transport_error)
                    SELECT recorded_at, temperature_c, temperature_f, transport_status, transport_error
                    FROM old_temperature_readings
                    """
                )
                conn.execute("DROP TABLE old_temperature_readings")
            else:  # Table doesn't exist, just create
                conn.execute(
                    """
                    CREATE TABLE temperature_readings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recorded_at TEXT NOT NULL,
                        temperature_c REAL NOT NULL,
                        temperature_f REAL NOT NULL,
                        transport_status TEXT NOT NULL,
                        transport_error TEXT,
                        sensor_id TEXT,
                        FOREIGN KEY(sensor_id) REFERENCES sensors(id) ON DELETE CASCADE
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
    sensor_id: Optional[str] = None


def add_reading(reading: Reading) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO temperature_readings (
                recorded_at, temperature_c, temperature_f, transport_status, transport_error, sensor_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reading.recorded_at.isoformat(),
                reading.temperature_c,
                reading.temperature_f,
                reading.transport_status,
                reading.transport_error,
                reading.sensor_id,
            ),
        )
        conn.commit()


def list_sensors() -> List[dict]:
    with db_connection() as conn:
        cursor = conn.execute("SELECT id, provider FROM sensors")
        return [{"id": row["id"], "provider": row["provider"]} for row in cursor.fetchall()]


def add_sensor(sensor_id: str, provider: str) -> None:
    with db_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sensors (id, provider) VALUES (?, ?)",
            (sensor_id, provider)
        )
        conn.commit()


def delete_sensor(sensor_id: str) -> None:
    with db_connection() as conn:
        conn.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
        conn.commit()


def update_sensors(new_sensors: List[dict]) -> None:
    with db_connection() as conn:
        current = list_sensors()
        current_ids = {s["id"] for s in current}
        new_ids = {s["id"] for s in new_sensors}
        to_delete = current_ids - new_ids
        for sid in to_delete:
            conn.execute("DELETE FROM sensors WHERE id = ?", (sid,))
        for sensor in new_sensors:
            conn.execute(
                "INSERT OR REPLACE INTO sensors (id, provider) VALUES (?, ?)",
                (sensor["id"], sensor["provider"])
            )
        conn.commit()


def list_readings(limit: int = 100) -> Iterable[Reading]:
    with db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT recorded_at, temperature_c, temperature_f, transport_status, transport_error, sensor_id
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
                sensor_id=row["sensor_id"],
            )
