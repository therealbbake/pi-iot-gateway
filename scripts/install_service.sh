#!/usr/bin/env bash
set -euo pipefail

APP_ROOT=${APP_ROOT:-/opt/pi-iot-gateway}
SERVICE_USER=${SERVICE_USER:-pi}
PYTHON_BIN=${PYTHON_BIN:-python3}
FERNET_KEY_FILE=${PI_IOT_FERNET_KEY_FILE:-/etc/pi-iot-gateway/fernet.key}
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VENV_DIR="$APP_ROOT/.venv"

echo "[pi-iot-gateway] Installing to $APP_ROOT"

sudo mkdir -p "$APP_ROOT"
sudo rsync -a --delete --exclude ".venv" --exclude "__pycache__" "$REPO_ROOT/" "$APP_ROOT/"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python binary $PYTHON_BIN not found" >&2
  exit 1
fi

sudo "$PYTHON_BIN" -m venv "$VENV_DIR"
sudo "$VENV_DIR/bin/pip" install --upgrade pip wheel
sudo "$VENV_DIR/bin/pip" install -r "$APP_ROOT/requirements.txt"

echo "[pi-iot-gateway] Installing Docker if not present"
if ! command -v docker >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y docker.io
  sudo systemctl enable docker
  sudo systemctl start docker
  sudo usermod -aG docker $SERVICE_USER
fi

echo "[pi-iot-gateway] Starting EMQX MQTT broker via Docker"
sudo docker run -d --name emqx -p 1883:1883 -p 8083:8083 -p 8084:8084 -p 18083:18083 emqx/emqx

sudo mkdir -p "$(dirname "$FERNET_KEY_FILE")"
if [ ! -f "$FERNET_KEY_FILE" ]; then
  sudo "$VENV_DIR/bin/python" -c "from cryptography.fernet import Fernet; import pathlib; pathlib.Path('$FERNET_KEY_FILE').write_bytes(Fernet.generate_key())"
  sudo chmod 600 "$FERNET_KEY_FILE"
fi
sudo chown "$SERVICE_USER":"$SERVICE_USER" "$FERNET_KEY_FILE"

sudo chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_ROOT"

sudo install -m 644 "$APP_ROOT/systemd/pi-iot-gateway.service" /etc/systemd/system/pi-iot-gateway.service
sudo systemctl daemon-reload
sudo systemctl enable pi-iot-gateway.service
echo "Installation complete. Start the service with: sudo systemctl start pi-iot-gateway.service"
