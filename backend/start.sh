#!/bin/bash
set -e

# Start Xvfb
Xvfb :99 -screen 0 1280x1024x24 -ac &
sleep 1

# Start window manager
openbox &
sleep 1

# Start VNC server
x11vnc -display :99 -forever -shared -rfbauth /root/.vnc/password -rfbport 5900 &

# Start noVNC websocket proxy
cd /opt/noVNC && ./utils/novnc_proxy --vnc localhost:5900 --listen 6080 &

# Start backend
cd /app && python main.py
