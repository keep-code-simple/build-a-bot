#!/bin/bash
# Sets up the Robot Box on a Raspberry Pi 5 (Raspberry Pi OS 64-bit, "Trixie").
# Run it ON THE PI, from the robot-box folder:
#
#   bash setup/install.sh                  Path B: the full box (screen, speaker, buttons)
#   bash setup/install.sh --path-a         Path A: no screen, the Chapter 1 Arduino on USB
#   bash setup/install.sh --uninstall-autostart     stop the box from starting by itself
#
# It is safe to run again. It takes a while the first time (it downloads the AI).
#
# NOT TESTED YET: this script was written without a Raspberry Pi on the desk.
# Read each step's message. If one fails, the message says which step it was.

set -e
cd "$(dirname "$0")/.."
BOX="$(pwd)"
LABWC_AUTOSTART="$HOME/.config/labwc/autostart"
SERVICE=/etc/systemd/system/robot-box.service

remove_autostart() {
    if [ -f "$LABWC_AUTOSTART" ]; then
        sed -i '/# robot-box$/d' "$LABWC_AUTOSTART"
    fi
    if [ -f "$SERVICE" ]; then
        sudo systemctl disable --now robot-box.service || true
        sudo rm -f "$SERVICE"
        sudo systemctl daemon-reload
    fi
}

if [ "$1" = "--uninstall-autostart" ]; then
    remove_autostart
    echo "Done. The box no longer starts by itself. Start it by hand with: bash setup/run_box.sh"
    exit 0
fi

echo "== Step 1 of 5: system packages (camera, buttons, sound) =="
sudo apt update
sudo apt install -y python3-venv python3-picamera2 python3-gpiozero python3-lgpio \
    espeak-ng alsa-utils git
# The AI Camera's firmware and built-in models. Harmless if you have a normal camera.
sudo apt install -y imx500-all || echo "Couldn't install imx500-all. Fine unless you have the AI Camera."

echo "== Step 2 of 5: the box's private Python =="
# Picamera2 only comes from apt, so this Python must be able to see the system's packages.
if [ ! -d .venv ]; then
    python3 -m venv --system-site-packages .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install "mediapipe==1.1.0" pygame pyserial piper-tts

echo "== Step 3 of 5: AI models and the robot's voice =="
.venv/bin/python setup/download_models.py hands voice

echo "== Step 4 of 5: check =="
.venv/bin/python -c "import cv2, mediapipe, pygame, serial, picamera2; print('All set!')"

echo "== Step 5 of 5: start by itself when plugged in =="
remove_autostart
chmod +x setup/run_box.sh
if [ "$1" = "--path-a" ]; then
    # No screen: a background service starts Rock Paper Scissors with the Arduino.
    sudo tee "$SERVICE" > /dev/null <<UNIT
[Unit]
Description=Robot Box (Path A: Rock Paper Scissors with the Arduino)
After=multi-user.target

[Service]
User=$USER
WorkingDirectory=$BOX
ExecStart=$BOX/.venv/bin/python $BOX/box.py --app rps --arduino
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
    sudo systemctl daemon-reload
    sudo systemctl enable robot-box.service
    echo "Done! Plug in the Arduino, then restart the Pi:  sudo reboot"
else
    # With a screen: log in to the desktop automatically, and the desktop starts the box.
    sudo raspi-config nonint do_boot_behaviour B4
    mkdir -p "$(dirname "$LABWC_AUTOSTART")"
    echo "\"$BOX/setup/run_box.sh\" & # robot-box" >> "$LABWC_AUTOSTART"
    echo "Done! Restart the Pi and the menu appears by itself:  sudo reboot"
fi
