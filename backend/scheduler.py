import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config import ConfigRepository, TransportSettings, config_repository
from backend.sensor.base import BaseSensorProvider, get_provider
from backend.storage import Reading, add_reading
from backend.transports.base import BaseTransport, get_transport

logger = logging.getLogger("pi_iot_gateway.scheduler")


class SensorScheduler:
    def __init__(self, repository: ConfigRepository = config_repository) -> None:
        self._repo = repository
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._provider: Optional[BaseSensorProvider] = None
        self._transport: Optional[BaseTransport] = None
        self._protocol: Optional[str] = None
        self._provider_name: Optional[str] = None

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
            if not self._provider or self._provider_name != settings.sensor_provider:
                self._provider = get_provider(settings.sensor_provider)
                self._provider_name = settings.sensor_provider
            if not self._transport or self._protocol != settings.protocol:
                await self._close_transport()
                self._transport = get_transport(settings, self._repo.secrets)
                self._protocol = settings.protocol
            provider = self._provider
            transport = self._transport
            if not provider or not transport:  # pragma: no cover
                logger.error("Sensor scheduler missing provider or transport; sleeping.")
                await asyncio.sleep(settings.sampling_interval_sec)
                continue
            recorded_at = datetime.now(timezone.utc)
            transport_status = "success"
            transport_error: Optional[str] = None
            try:
                temp_c = provider.read_celsius()
                temp_f = provider.read_fahrenheit()
                payload = {
                    "device": settings.device_id,
                    "temperatureC": temp_c,
                    "temperatureF": temp_f,
                    "timestamp": recorded_at.isoformat(),
                }
                await transport.send(payload)
                logger.info("Reading sent: %s", payload)
            except Exception as exc:  # pylint: disable=broad-except
                transport_status = "failure"
                transport_error = str(exc)
                logger.exception("Failed to send reading: %s", exc)
                # also persist reading even if sensor read failed?
                temp_c = temp_f = float("nan")
            finally:
                add_reading(
                    Reading(
                        recorded_at=recorded_at,
                        temperature_c=temp_c if "temp_c" in locals() else float("nan"),
                        temperature_f=temp_f if "temp_f" in locals() else float("nan"),
                        transport_status=transport_status,
                        transport_error=transport_error,
                    )
                )
            await asyncio.sleep(settings.sampling_interval_sec)


scheduler = SensorScheduler()
