#!/bin/bash
set -euo pipefail

# This script sets up Raspberry Pi for kiosk mode, displaying the Pi IoT Gateway UI full-screen on boot.
# It installs necessary packages, configures autologin, and sets up Chromium to launch automatically.

# Update system and install required packages
sudo apt update
sudo apt install --no-install-recommends -y xserver-xorg x11-xserver-utils xinit openbox chromium-browser unclutter

# Configure autologin for pi user
sudo raspi-config nonint do_boot_behaviour B4

# Create .xinitrc for kiosk mode
cat << EOF > ~/.xinitrc
xset s off
xset s noblank
xset -dpms

openbox-session &

while true; do
  timeout 3 bash -c "</dev/tcp/127.0.0.1/8000" >/dev/null 2>&1 && break
  sleep 1
done

chromium-browser --noerrdialogs --disable-session-crashed-bubble --disable-infobars --kiosk http://localhost:8000
EOF

# Hide cursor
sudo sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' /home/pi/.config/chromium/Default/Preferences
sudo sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' /home/pi/.config/chromium/Default/Preferences

# Add unclutter to hide mouse cursor
echo "unclutter -idle 0.1 -root &" >> ~/.xinitrc

echo "Kiosk mode setup complete. Reboot the Pi to start in kiosk mode."
echo "To disable, change boot behavior in raspi-config and remove ~/.xinitrc"
