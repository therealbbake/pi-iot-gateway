import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, List


class BaseSensorProvider(ABC):
    name: str

    def __init__(self, sensor_id: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def read_celsius(self) -> float:
        raise NotImplementedError

    def read_fahrenheit(self) -> float:
        return self.read_celsius() * 9.0 / 5.0 + 32.0


class MockSensorProvider(BaseSensorProvider):
    name = "mock"

    def __init__(self, sensor_id: Optional[str] = None) -> None:
        super().__init__(sensor_id)
        self._seed = int(time.time()) + (hash(sensor_id) if sensor_id else 0)

    def read_celsius(self) -> float:
        random.seed(self._seed + int(time.time()))
        base = 22.5
        offset = random.uniform(-1.5, 1.5)
        return round(base + offset, 2)


class W1ThermSensorProvider(BaseSensorProvider):
    name = "w1"

    def __init__(self, sensor_id: Optional[str] = None) -> None:
        super().__init__(sensor_id)
        try:
            from w1thermsensor import W1ThermSensor  # type: ignore
        except ImportError as exc:  # pragma: no cover - hardware dependent
            raise RuntimeError(
                "w1thermsensor library not available. Install with 'pip install w1thermsensor'."
            ) from exc
        self._sensor = W1ThermSensor(sensor_id=sensor_id) if sensor_id else W1ThermSensor()

    def read_celsius(self) -> float:  # pragma: no cover - hardware dependent
        return round(self._sensor.get_temperature(), 2)


PROVIDERS: Dict[str, Type[BaseSensorProvider]] = {
    MockSensorProvider.name: MockSensorProvider,
    W1ThermSensorProvider.name: W1ThermSensorProvider,
}


def get_provider(name: str, sensor_id: Optional[str] = None) -> BaseSensorProvider:
    provider_cls = PROVIDERS.get(name, MockSensorProvider)
    return provider_cls(sensor_id=sensor_id)


def discover_w1_sensors() -> List[str]:
    try:
        from w1thermsensor import W1ThermSensor  # type: ignore
        return [sensor.id for sensor in W1ThermSensor.get_available_sensors()]
    except ImportError:  # pragma: no cover - hardware dependent
        return []
    except Exception:  # pragma: no cover - hardware dependent
        return []
