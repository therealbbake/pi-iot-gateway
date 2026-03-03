from datetime import datetime, timezone

import backend.storage as storage


def test_add_and_list(monkeypatch, tmp_path):
    db_path = tmp_path / "telemetry.db"
    monkeypatch.setattr(storage, "DB_PATH", db_path)
    storage.init_db()

    reading = storage.Reading(
        recorded_at=datetime.now(timezone.utc),
        temperature_c=21.5,
        temperature_f=70.7,
        transport_status="success",
        transport_error=None,
    )
    storage.add_reading(reading)
    items = list(storage.list_readings())
    assert len(items) == 1
    assert items[0].temperature_c == reading.temperature_c
    assert items[0].transport_status == "success"
