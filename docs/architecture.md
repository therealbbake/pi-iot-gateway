# Pi IoT Gateway Architecture

## Overview

The Pi IoT Gateway is a two-tier application designed for Raspberry Pi devices. It collects temperature readings from a GPIO-connected sensor, forwards the data to an Oracle IoT domain via HTTP or MQTTS, and exposes a lightweight Oracle JET web front-end for monitoring and configuration.

```
[Sensor] ──> [Python Backend Service] ──> [Oracle IoT Domain]
                                 │
                                 └──> [Oracle JET Front-end]
```

## Components

### Backend (Python / FastAPI)

- **Sensor Abstraction**: A provider interface decouples the core service from the physical sensor. Two implementations ship by default:
  - `W1ThermSensorProvider` for DS18B20 one-wire sensors using the `w1thermsensor` library.
  - `MockSensorProvider` that generates deterministic pseudo-random readings for development.
- **Data Scheduler**: An asyncio task polls the sensor on a configurable interval. Readings are persisted to SQLite (`data/telemetry.db`) and forwarded to Oracle IoT via the selected transport.
- **IoT Transports**:
  - `HttpTransport` posts JSON payloads to the Oracle IoT ingestion endpoint using basic authentication and TLS.
  - `MqttsTransport` publishes MQTT messages over TLS (port `8883`) using the Oracle IoT topic conventions.
- **REST API**:
  - `GET /api/readings` – returns the latest readings (paged).
  - `GET /api/config` / `PUT /api/config` – reads and updates transport, credentials, and sampling interval.
  - `POST /api/test-connection` – validates outbound connectivity without persisting data.
  - `GET /healthz` – probes service health for systemd.
- **Configuration Management**:
  - `config/config.yaml` stores non-secret settings (intervals, protocol, topic).
  - `config/secrets.json` encrypts sensitive values using Fernet with a key in `/etc/pi-iot-gateway/fernet.key`; the key path is configurable via `PI_IOT_FERNET_KEY`.

### Front-end (Oracle JET)

- Single-page app hosted from `frontend/public/` and served via FastAPI static files.
- Views:
  - **Dashboard** – chart of recent temperatures (oj-chart) plus status banner.
  - **Configuration** – form for IoT domain host, device ID, auth token, topic/resource, protocol selector, and sampling interval.
- Uses Oracle JET modules via CDN imports to avoid local build tooling on the Pi. REST interactions hit the backend API.

### System Service

- `systemd/pi-iot-gateway.service` runs the backend with `uvicorn`, ensures automatic restarts, and logs to the journal.
- A helper script `scripts/install_service.sh` installs Python dependencies, creates directories, seeds the Fernet key, and registers the systemd unit.

## Data Flow

1. Scheduler triggers sensor read (default every 30 seconds).
2. Reading is validated and stored in SQLite.
3. Payload is shaped as:

```json
{
  "device": "<deviceId>",
  "temperatureC": 23.4,
  "temperatureF": 74.1,
  "timestamp": "2026-03-03T15:15:00Z"
}
```

4. Selected transport transmits payload to Oracle IoT:
   - HTTP: `POST https://<domain>.device.iot.<region>.oci.oraclecloud.com/<resource>`
   - MQTTS: publish to topic `iot/<domain>/<deviceId>/<resource>`

5. Front-end polls `/api/readings` every 10 seconds to update the chart.

## Extensibility

- Additional sensors can subclass `BaseSensorProvider` and register via entry point in `config/config.yaml`.
- Extra transports (e.g., AMQP) may extend `BaseTransport` with new config schema entries.

## Security Considerations

- Secrets file encrypted to prevent accidental disclosure.
- HTTPS/TLS enforced for all external traffic.
- Configuration updates require admin password (configurable via Fernet-protected secrets).
- Scheduler handles transient send failures via exponential backoff and stores error context in SQLite for the UI.

