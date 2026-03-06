#!/usr/bin/env bash
set -euo pipefail

APP_ROOT=${APP_ROOT:-/opt/pi-iot-gateway}
SERVICE_USER=${SERVICE_USER:-pi}
FERNET_KEY_FILE=${PI_IOT_FERNET_KEY_FILE:-/etc/pi-iot-gateway/fernet.key}

echo "[pi-iot-gateway] Uninstalling from $APP_ROOT"

# Stop and disable the service
if systemctl is-active --quiet pi-iot-gateway.service; then
  sudo systemctl stop pi-iot-gateway.service
fi
sudo systemctl disable pi-iot-gateway.service

# Remove the service file
sudo rm -f /etc/systemd/system/pi-iot-gateway.service
sudo systemctl daemon-reload

# Remove the application directory
if [ -d "$APP_ROOT" ]; then
  sudo rm -rf "$APP_ROOT"
fi

# Remove the fernet key and its directory if empty
if [ -f "$FERNET_KEY_FILE" ]; then
  sudo rm -f "$FERNET_KEY_FILE"
fi
FERNET_DIR="$(dirname "$FERNET_KEY_FILE")"
if [ -d "$FERNET_DIR" ] && [ -z "$(ls -A "$FERNET_DIR")" ]; then
  sudo rmdir "$FERNET_DIR"
fi

echo "Uninstallation complete. All traces of the pi-iot-gateway service have been removed."
