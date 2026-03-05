import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Literal, Optional, List

from backend.models import SensorConfigModel

import yaml
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, validator

CONFIG_PATH = Path("config/config.yaml")
SECRETS_PATH = Path("config/secrets.json")
DEFAULT_FERNET_PATH = Path("/etc/pi-iot-gateway/fernet.key")
ENV_FERNET_KEY = "PI_IOT_FERNET_KEY"
ENV_FERNET_FILE = "PI_IOT_FERNET_KEY_FILE"


class TransportSettings(BaseModel):
    protocol: Literal["http", "mqtt"] = "http"
    domain: str = "example"
    region: str = "us-ashburn-1"
    resource: str = "sampletopic"
    device_id: str = "pi-gateway-01"
    sampling_interval_sec: int = Field(30, ge=5, le=3600)
    publish_enabled: bool = True
    sensors: List[SensorConfigModel] = Field(default_factory=list)
    light_gpio_pin: int = Field(17, ge=1, le=40)  # GPIO pin for light control
    mqtt_host: Optional[str] = None
    mqtt_port: int = Field(1883, ge=1, le=65535)
    mqtt_use_tls: bool = False

@validator("domain")
def domain_must_not_be_empty(cls, value: str, values) -> str:
    if values.get("publish_enabled", True) and not value:
        raise ValueError("domain must not be empty when publishing is enabled")
    return value

    @validator("resource")
    def resource_strip_slash(cls, value: str) -> str:
        return value.lstrip("/")

TransportSettings.model_rebuild()


class SecretSettings(BaseModel):
    username: str = "iot_client"
    password: str = "changeme"
    mqtt_client_cert: Optional[str] = None
    mqtt_client_key: Optional[str] = None


class AppSettings(BaseModel):
    transport: TransportSettings = TransportSettings()

AppSettings.model_rebuild()


class SecretManager:
    def __init__(self, allow_generate: bool = False) -> None:
        self.allow_generate = allow_generate

    def _resolve_key_path(self) -> Optional[Path]:
        env_path = os.getenv(ENV_FERNET_FILE)
        if env_path:
            return Path(env_path)
        if DEFAULT_FERNET_PATH.exists():
            return DEFAULT_FERNET_PATH
        return None

    def _load_key(self) -> Optional[bytes]:
        env_key = os.getenv(ENV_FERNET_KEY)
        if env_key:
            return env_key.encode("ascii")
        key_path = self._resolve_key_path()
        if key_path and key_path.exists():
            return key_path.read_bytes().strip()
        if self.allow_generate:
            key = Fernet.generate_key()
            key_path = self._resolve_key_path() or DEFAULT_FERNET_PATH
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_bytes(key)
            return key
        return None

    def _fernet(self) -> Optional[Fernet]:
        key = self._load_key()
        return Fernet(key) if key else None

    def load(self) -> SecretSettings:
        if not SECRETS_PATH.exists():
            return SecretSettings()
        encrypted = json.loads(SECRETS_PATH.read_text())
        fernet = self._fernet()
        if not fernet:
            raise RuntimeError("Fernet key not available; set PI_IOT_FERNET_KEY or provide key file.")
        decrypted = fernet.decrypt(encrypted["payload"].encode("ascii"))
        data = json.loads(decrypted.decode("utf-8"))
        return SecretSettings(**data)

    def save(self, secrets: SecretSettings) -> None:
        fernet = self._fernet()
        if not fernet:
            raise RuntimeError("Fernet key not available; cannot save secrets.")
        payload = json.dumps(secrets.dict()).encode("utf-8")
        token = fernet.encrypt(payload).decode("ascii")
        SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SECRETS_PATH.write_text(json.dumps({"payload": token}))


class ConfigRepository:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._settings = self._load_settings()
        self._secrets = self._load_secrets()

    def _load_settings(self) -> AppSettings:
        if not CONFIG_PATH.exists():
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(yaml.safe_dump(AppSettings().dict()))
        with CONFIG_PATH.open() as handle:
            data = yaml.safe_load(handle) or {}
        return AppSettings(**data)

    def _load_secrets(self) -> SecretSettings:
        manager = SecretManager()
        try:
            return manager.load()
        except RuntimeError:
            return SecretSettings()

    @property
    def settings(self) -> AppSettings:
        with self._lock:
            return self._settings

    @property
    def secrets(self) -> SecretSettings:
        with self._lock:
            return self._secrets

    def update(
        self,
        updates: Dict[str, Any],
        secret_updates: Optional[Dict[str, Any]] = None,
    ) -> AppSettings:
        with self._lock:
            if updates:
                merged = self._settings.dict()
                merged_transport = {**merged["transport"], **updates.get("transport", updates)}
                merged["transport"] = merged_transport
                self._settings = AppSettings(**merged)
                CONFIG_PATH.write_text(yaml.safe_dump(self._settings.dict()))
            if secret_updates:
                merged_secret = self._secrets.dict()
                merged_secret.update(secret_updates)
                self._secrets = SecretSettings(**merged_secret)
                manager = SecretManager(allow_generate=True)
                manager.save(self._secrets)
        return self._settings


config_repository = ConfigRepository()
