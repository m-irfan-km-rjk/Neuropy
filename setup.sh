#!/bin/bash

# NeuroPi Setup Script
# Run this on the Raspberry Pi

echo "Starting NeuroPi Setup..."

# 1. Install System Dependencies
echo "Updating system..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv chromium-browser unclutter

# 2. Set up Python Environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create Autostart for Kiosk Mode
echo "Configuring Kiosk Mode..."
mkdir -p /home/pi/.config/lxsession/LXDE-pi
cat <<EOT > /home/pi/.config/lxsession/LXDE-pi/autostart
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root
@chromium-browser --noerrdialogs --kiosk --incognito http://localhost:5000
EOT

# 4. Create Systemd Service for Flask App
echo "Creating Systemd Service..."
sudo bash -c 'cat <<EOT > /etc/systemd/system/neuropi.service
[Unit]
Description=NeuroPi Web Server
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/NeuroPi
Environment="PATH=/home/pi/NeuroPi/venv/bin"
ExecStart=/home/pi/NeuroPi/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOT'

echo "Enabling Service..."
sudo systemctl enable neuropi.service
sudo systemctl start neuropi.service

echo "Setup Complete! Rebooting in 5 seconds..."
sleep 5
# sudo reboot
