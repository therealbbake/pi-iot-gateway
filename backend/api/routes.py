from fastapi import APIRouter, HTTPException

from backend.config import config_repository
from backend.models import (
    ConfigResponse,
    ConfigUpdatePayload,
    ReadingsResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from typing import List
from backend.sensor.base import discover_w1_sensors
from backend.storage import list_readings
from backend.scheduler import scheduler as sensor_scheduler
from backend.transports.base import get_transport

router = APIRouter(prefix="/api")


@router.get("/readings", response_model=ReadingsResponse)
async def readings(limit: int = 100) -> ReadingsResponse:
    items = [
        {
            "recorded_at": reading.recorded_at,
            "temperature_c": reading.temperature_c,
            "temperature_f": reading.temperature_f,
            "transport_status": reading.transport_status,
            "transport_error": reading.transport_error,
            "sensor_id": reading.sensor_id,
        }
        for reading in list_readings(limit=limit)
    ]
    return ReadingsResponse(readings=items)


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    settings = config_repository.settings
    return ConfigResponse(transport=settings.transport.dict())


@router.put("/config", response_model=ConfigResponse)
async def update_config(payload: ConfigUpdatePayload) -> ConfigResponse:
    updates = {}
    secrets = None
    if payload.transport:
        updates["transport"] = payload.transport.dict()
    if payload.secrets:
        secrets = payload.secrets.dict(exclude_unset=True, exclude_none=True)
    try:
        config_repository.update(updates, secret_updates=secrets)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await sensor_scheduler.start()
    return await get_config()


@router.get("/sensors/discover", response_model=List[str])
async def discover_sensors() -> List[str]:
    return discover_w1_sensors()

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest) -> TestConnectionResponse:
    settings = config_repository.settings.transport.copy()
    secrets = config_repository.secrets
    if request.protocol_override:
        settings = settings.copy(update={"protocol": request.protocol_override})
    transport = get_transport(settings, secrets)
    try:
        await transport.test_connection()
        return TestConnectionResponse(status="ok", message="Connection test succeeded")
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail=str(exc)) from exc
