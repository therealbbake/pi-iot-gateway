import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Type


class BaseSensorProvider(ABC):
    name: str

    @abstractmethod
    def read_celsius(self) -> float:
        raise NotImplementedError

    def read_fahrenheit(self) -> float:
        return self.read_celsius() * 9.0 / 5.0 + 32.0


class MockSensorProvider(BaseSensorProvider):
    name = "mock"

    def __init__(self) -> None:
        self._seed = int(time.time())

    def read_celsius(self) -> float:
        random.seed(self._seed + int(time.time()))
        base = 22.5
        offset = random.uniform(-1.5, 1.5)
        return round(base + offset, 2)


class W1ThermSensorProvider(BaseSensorProvider):
    name = "w1"

    def __init__(self) -> None:
        try:
            from w1thermsensor import W1ThermSensor  # type: ignore
        except ImportError as exc:  # pragma: no cover - hardware dependent
            raise RuntimeError(
                "w1thermsensor library not available. Install with 'pip install w1thermsensor'."
            ) from exc
        self._sensor = W1ThermSensor()

    def read_celsius(self) -> float:  # pragma: no cover - hardware dependent
        return round(self._sensor.get_temperature(), 2)


PROVIDERS: Dict[str, Type[BaseSensorProvider]] = {
    MockSensorProvider.name: MockSensorProvider,
    W1ThermSensorProvider.name: W1ThermSensorProvider,
}


def get_provider(name: str) -> BaseSensorProvider:
    provider_cls = PROVIDERS.get(name, MockSensorProvider)
    return provider_cls()

