# Pi IoT Gateway

Python-based service for Raspberry Pi devices that reads temperature data from GPIO sensors, forwards the data to an Oracle IoT domain over HTTP or MQTTS, and surfaces a lightweight Oracle JET front-end for monitoring and configuration.

## Features

- FastAPI backend with background scheduler that polls a DS18B20 (1-wire) sensor or a mock sensor for development.
- Pluggable IoT transports supporting Oracle IoT ingestion via HTTPS POST or MQTT over TLS.
- SQLite persistence for historical readings and REST APIs to retrieve telemetry and adjust configuration at runtime.
- Oracle JET single-page UI served directly by the backend for live charts, recent readings, and IoT credential updates.
- Systemd unit and installer script for Raspberry Pi deployment with encrypted secret storage (Fernet).

## Requirements

- Raspberry Pi OS (Bullseye or later) with Python 3.10+.
- 1-wire temperature sensor (e.g., DS18B20) wired to GPIO; enable 1-wire support via `raspi-config`.
- Network connectivity to the Oracle IoT domain.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PI_IOT_FERNET_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
uvicorn backend.app:app --reload
```

Open `http://localhost:8000/` to view the Oracle JET dashboard. API endpoints live under `/api/*`.

To run the unit test suite:

```bash
PYTHONPATH=. pytest
```

## Configuration

- `config/config.yaml` – non-secret defaults (protocol, IoT domain host, resource name, sampling interval, sensor provider).
- `config/secrets.json` – encrypted credentials persisted with Fernet using the key referenced by `PI_IOT_FERNET_KEY` or `PI_IOT_FERNET_KEY_FILE`.
- REST:
  - `GET /api/config` / `PUT /api/config` to fetch or update transport and credential settings.
  - `GET /api/readings?limit=N` to retrieve recent telemetry.
  - `POST /api/test-connection` to validate Oracle IoT connectivity.

## Oracle IoT Integration

- HTTP ingest endpoint: `https://<domain>.device.iot.<region>.oci.oraclecloud.com/<resource>`.
- MQTTS ingest endpoint: `mqtts://<domain>.device.iot.<region>.oci.oraclecloud.com:8883`, publish to topic `iot/<domain>/<deviceId>/<resource>`.
- Provide Oracle IoT device credentials (username/password or X.509 certificate) when updating configuration through the UI or REST API. citeturn0search0

## Deployment on Raspberry Pi

1. Ensure the repo is copied to the device and run the installer as `pi` or another sudo-capable user:
   ```bash
   chmod +x scripts/install_service.sh
   ./scripts/install_service.sh
   ```
2. Edit `/opt/pi-iot-gateway/config/config.yaml` if needed (e.g., switch `sensor_provider` from `mock` to `w1`).
3. Start the service:
   ```bash
   sudo systemctl start pi-iot-gateway.service
   ```
4. Monitor logs:
   ```bash
   journalctl -u pi-iot-gateway.service -f
   ```

The service binds to port `8000` by default. Reverse proxy (e.g., Nginx) as needed for HTTPS termination.

## Troubleshooting

- Ensure the `w1thermsensor` kernel modules are loaded (`dtoverlay=w1-gpio` in `/boot/config.txt`) when using the DS18B20 sensor.
- Verify the Fernet key file exists at `/etc/pi-iot-gateway/fernet.key` and is readable by the service user.
- If MQTT authentication uses certificates, copy `.pem` files to the Pi and update them through the REST API (paths stored in `config/secrets.json`).

