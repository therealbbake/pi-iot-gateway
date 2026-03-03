from abc import ABC, abstractmethod
from typing import Dict, Type

from backend.config import SecretSettings, TransportSettings


class BaseTransport(ABC):
    def __init__(self, settings: TransportSettings, secrets: SecretSettings) -> None:
        self.settings = settings
        self.secrets = secrets

    @abstractmethod
    async def send(self, payload: Dict[str, float]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def test_connection(self) -> None:
        raise NotImplementedError


REGISTRY: Dict[str, Type[BaseTransport]] = {}


def register(name: str, cls: Type[BaseTransport]) -> None:
    REGISTRY[name] = cls


def get_transport(settings: TransportSettings, secrets: SecretSettings) -> BaseTransport:
    transport_cls = REGISTRY.get(settings.protocol)
    if not transport_cls:
        raise ValueError(f"Unsupported protocol {settings.protocol}")
    return transport_cls(settings, secrets)

