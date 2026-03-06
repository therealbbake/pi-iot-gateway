import asyncio
import json
import ssl
from typing import Optional

from paho.mqtt import client as mqtt_client

from backend.config import SecretSettings, TransportSettings
from backend.transports.base import BaseTransport, register


class MqttTransport(BaseTransport):
    def __init__(self, settings: TransportSettings, secrets: SecretSettings) -> None:
        super().__init__(settings, secrets)
        self._loop = asyncio.get_event_loop()

    @property
    def host(self) -> str:
        if self.settings.mqtt_use_tls:
            return f"{self.settings.domain}.device.iot.{self.settings.region}.oci.oraclecloud.com"
        return self.settings.mqtt_host

    @property
    def port(self) -> int:
        if self.settings.mqtt_use_tls:
            return 8883
        return self.settings.mqtt_port

    @property
    def topic(self) -> str:
        if self.settings.mqtt_use_tls:
            return "/data"
        return f"iot/{self.settings.device_id}/{self.settings.resource}"

    def _build_client(self) -> mqtt_client.Client:
        client = mqtt_client.Client(client_id=self.settings.device_id)
        if self.settings.mqtt_use_tls:
            client.username_pw_set(self.secrets.external_key, self.secrets.secret)
            context = ssl.create_default_context()
            client.tls_set_context(context)
            client.tls_insecure_set(False)
        return client

    def _publish_sync(self, message: str) -> None:
        client = self._build_client()
        result = client.connect(self.host, port=self.port, keepalive=60)
        if result != mqtt_client.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT connect failed: {mqtt_client.error_string(result)}")
        status, _ = client.publish(self.topic, message, qos=1)
        client.disconnect()
        if status != mqtt_client.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed: {mqtt_client.error_string(status)}")

    async def send(self, payload: dict) -> None:
        message = json.dumps(payload)
        await self._loop.run_in_executor(None, self._publish_sync, message)

    async def test_connection(self) -> None:
        probe = json.dumps({"device": self.settings.device_id, "test": True})
        await self._loop.run_in_executor(None, self._publish_sync, probe)


register("mqtt", MqttTransport)
