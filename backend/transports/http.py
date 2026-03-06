import asyncio
import json
from datetime import datetime, timezone

import httpx
from httpx import HTTPError

from backend.config import SecretSettings, TransportSettings
from backend.transports.base import BaseTransport, register


class HttpTransport(BaseTransport):
    def __init__(self, settings: TransportSettings, secrets: SecretSettings) -> None:
        super().__init__(settings, secrets)
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=20.0))

    @property
    def endpoint(self) -> str:
        return (
            f"https://{self.settings.domain}.device.iot."
            f"{self.settings.region}.oci.oraclecloud.com/"
            f"{self.settings.resource}"
        )

    async def send(self, payload: dict) -> None:
        if not self.settings.publish_enabled:
            return  # Skip sending if publishing is disabled
        try:
            response = await self._client.post(
                self.endpoint,
                content=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                auth=(self.secrets.external_key, self.secrets.secret),
            )
            response.raise_for_status()
        except HTTPError as exc:
            raise RuntimeError(f"HTTP send failed: {exc}") from exc

    async def test_connection(self) -> None:
        probe = {
            "device": self.settings.device_id,
            "test": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await self.send(probe)
        except RuntimeError as exc:
            raise RuntimeError(f"HTTP test failed: {exc}") from exc

    async def close(self) -> None:
        await self._client.aclose()


register("http", HttpTransport)
