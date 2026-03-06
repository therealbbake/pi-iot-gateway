import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

from backend.config import ConfigRepository, TransportSettings, config_repository
from backend.sensor.base import BaseSensorProvider, get_provider
from backend.storage import Reading, add_reading, list_sensors
from backend.transports.base import BaseTransport, get_transport

logger = logging.getLogger("pi_iot_gateway.scheduler")


class SensorScheduler:
    def __init__(self, repository: ConfigRepository = config_repository) -> None:
        self._repo = repository
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._providers: Dict[str, BaseSensorProvider] = {}
        self._transport: Optional[BaseTransport] = None
        self._protocol: Optional[str] = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            await self._task
        await self._close_transport()

    async def _close_transport(self) -> None:
        if self._transport:
            close_fn = getattr(self._transport, "close", None)
            if close_fn:
                result = close_fn()
                if asyncio.iscoroutine(result):
                    await result
            self._transport = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            settings = self._repo.settings.transport
            # Update providers based on configured sensors from DB
            sensors = list_sensors()
            current_sensor_ids = set(s["id"] for s in sensors)
            self._providers = {sid: prov for sid, prov in self._providers.items() if sid in current_sensor_ids}
            for sensor in sensors:
                sid = sensor["id"]
                if sid not in self._providers:
                    self._providers[sid] = get_provider(sensor["provider"], sid)

            if not self._transport or self._protocol != settings.protocol:
                await self._close_transport()
                self._transport = get_transport(settings, self._repo.secrets)
                self._protocol = settings.protocol

            transport = self._transport
            if not transport:  # pragma: no cover
                logger.error("Sensor scheduler missing transport; sleeping.")
                await asyncio.sleep(settings.sampling_interval_sec)
                continue

            for sensor_id, provider in self._providers.items():
                try:
                    temp_c = provider.read_celsius()
                    temp_f = provider.read_fahrenheit()
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning("Sensor %s read failed: %s", sensor_id, exc)
                    continue

                recorded_at = datetime.now(timezone.utc)
                payload = {
                    "device": settings.device_id,
                    "sensor": sensor_id,
                    "temperatureC": temp_c,
                    "temperatureF": temp_f,
                    "time": recorded_at.isoformat(),
                }
                transport_status = "disabled"
                transport_error: Optional[str] = None
                if settings.publish_enabled:
                    try:
                        await transport.send(payload)
                        transport_status = "success"
                        logger.info("Reading sent for sensor %s: %s", sensor_id, payload)
                    except Exception as exc:  # pylint: disable=broad-except
                        transport_status = "failure"
                        transport_error = str(exc)
                        logger.warning("Failed to send reading for sensor %s: %s", sensor_id, exc)
                else:
                    logger.info("Publishing disabled; skipping send for sensor %s", sensor_id)
                add_reading(
                    Reading(
                        recorded_at=recorded_at,
                        temperature_c=temp_c,
                        temperature_f=temp_f,
                        transport_status=transport_status,
                        transport_error=transport_error,
                        sensor_id=sensor_id,
                    )
                )

            await asyncio.sleep(settings.sampling_interval_sec)


scheduler = SensorScheduler()
