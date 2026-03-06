#!/usr/bin/env bash
set -euo pipefail

APP_ROOT=${APP_ROOT:-/opt/pi-iot-gateway}
SERVICE_USER=${SERVICE_USER:-pi}
PYTHON_BIN=${PYTHON_BIN:-python3}
FERNET_KEY_FILE=${PI_IOT_FERNET_KEY_FILE:-/etc/pi-iot-gateway/fernet.key}
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VENV_DIR="$APP_ROOT/.venv"

echo "[pi-iot-gateway] Installing to $APP_ROOT"

if [ -d "$APP_ROOT" ]; then
  echo "[pi-iot-gateway] Existing installation detected at $APP_ROOT. Updating files..."
  sudo rsync -a --exclude ".venv" --exclude "__pycache__" --exclude "config/secrets.json" "$REPO_ROOT/" "$APP_ROOT/"
else
  sudo mkdir -p "$APP_ROOT"
  sudo rsync -a --exclude ".venv" --exclude "__pycache__" "$REPO_ROOT/" "$APP_ROOT/"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python binary $PYTHON_BIN not found" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  sudo "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
sudo "$VENV_DIR/bin/pip" install --upgrade pip wheel
sudo "$VENV_DIR/bin/pip" install -r "$APP_ROOT/requirements.txt"

echo "[pi-iot-gateway] Installing EMQX as a native service if not present"
if ! dpkg -l | grep -q emqx; then
  sudo apt update
  curl -s https://assets.emqx.com/scripts/install-emqx-deb.sh | sudo bash
  sudo apt-get install -y emqx
fi
sudo systemctl enable emqx
sudo systemctl start emqx || true

sudo mkdir -p "$(dirname "$FERNET_KEY_FILE")"
if [ ! -f "$FERNET_KEY_FILE" ]; then
  sudo "$VENV_DIR/bin/python" -c "from cryptography.fernet import Fernet; import pathlib; pathlib.Path('$FERNET_KEY_FILE').write_bytes(Fernet.generate_key())"
  sudo chmod 600 "$FERNET_KEY_FILE"
fi
sudo chown "$SERVICE_USER":"$SERVICE_USER" "$FERNET_KEY_FILE"

sudo chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_ROOT"

# Dynamically replace User in the service file with SERVICE_USER
sudo cp "$APP_ROOT/systemd/pi-iot-gateway.service" /etc/systemd/system/pi-iot-gateway.service
sudo sed -i "s/User=pi/User=$SERVICE_USER/g" /etc/systemd/system/pi-iot-gateway.service
sudo chmod 644 /etc/systemd/system/pi-iot-gateway.service
sudo systemctl daemon-reload
sudo systemctl enable pi-iot-gateway.service
echo "Installation complete. Start the service with: sudo systemctl start pi-iot-gateway.service"
