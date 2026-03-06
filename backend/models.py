from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class ReadingModel(BaseModel):
    recorded_at: datetime
    temperature_c: float
    temperature_f: float
    transport_status: str
    transport_error: Optional[str]
    sensor_id: Optional[str] = None


class ReadingsResponse(BaseModel):
    readings: List[ReadingModel]


class SensorConfigModel(BaseModel):
    id: str
    provider: Literal["w1", "mock"] = "w1"


class TransportConfigModel(BaseModel):
    protocol: str = Field(..., pattern="^(http|mqtt)$")
    domain: str
    region: str
    resource: str
    device_id: str
    sampling_interval_sec: int = Field(..., ge=5, le=3600)
    publish_enabled: bool = True
    light_gpio_pin: int = Field(17, ge=1, le=40)
    mqtt_host: Optional[str] = None
    mqtt_port: int = Field(1883, ge=1, le=65535)
    mqtt_use_tls: bool = False


class ConfigResponse(BaseModel):
    transport: TransportConfigModel
    sensors: List[SensorConfigModel]


class SecretUpdateRequest(BaseModel):
    external_key: Optional[str]
    secret: Optional[str]


class ConfigUpdatePayload(BaseModel):
    transport: Optional[TransportConfigModel]
    secrets: Optional[SecretUpdateRequest]


class TestConnectionRequest(BaseModel):
    protocol_override: Optional[str] = Field(None, pattern="^(http|mqtt)$")


class SensorsUpdatePayload(BaseModel):
    sensors: List[SensorConfigModel]

class TestConnectionResponse(BaseModel):
    status: str
    message: Optional[str]

TransportConfigModel.model_rebuild()
