from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReadingModel(BaseModel):
    recorded_at: datetime
    temperature_c: float
    temperature_f: float
    transport_status: str
    transport_error: Optional[str]


class ReadingsResponse(BaseModel):
    readings: List[ReadingModel]


class TransportConfigModel(BaseModel):
    protocol: str = Field(..., regex="^(http|mqtts)$")
    domain: str
    region: str
    resource: str
    device_id: str
    sampling_interval_sec: int = Field(..., ge=5, le=3600)
    sensor_provider: str


class ConfigResponse(BaseModel):
    transport: TransportConfigModel


class SecretUpdateRequest(BaseModel):
    username: Optional[str]
    password: Optional[str]
    mqtt_client_cert: Optional[str]
    mqtt_client_key: Optional[str]


class ConfigUpdatePayload(BaseModel):
    transport: Optional[TransportConfigModel]
    secrets: Optional[SecretUpdateRequest]


class TestConnectionRequest(BaseModel):
    protocol_override: Optional[str] = Field(None, regex="^(http|mqtts)$")


class TestConnectionResponse(BaseModel):
    status: str
    message: Optional[str]
