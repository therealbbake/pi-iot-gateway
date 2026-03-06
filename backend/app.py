import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router as api_router
import backend.transports  # noqa: F401
from backend.mqtt_subscriber import MQTTSubscriber
from backend.scheduler import scheduler
from backend.storage import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Pi IoT Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    await scheduler.start()
    subscriber = MQTTSubscriber()
    subscriber.start()
    app.state.mqtt_subscriber = subscriber


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await scheduler.stop()
    subscriber.stop()


app.include_router(api_router)

frontend_dir = Path("frontend/public")
if frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )


@app.get("/healthz")
async def health() -> dict:
    mqtt_status = app.state.mqtt_subscriber.status if hasattr(app.state, 'mqtt_subscriber') else "unknown"
    return {"status": "ok", "mqtt_status": mqtt_status}
