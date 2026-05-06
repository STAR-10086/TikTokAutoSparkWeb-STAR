#!/bin/bash
set -e

echo "=== Starting VNC Desktop ==="
# Start Xvfb
Xvfb :99 -screen 0 1280x1024x24 -ac &
sleep 1

# Start openbox window manager
openbox &
sleep 1

# Start x11vnc
x11vnc -display :99 -forever -shared -rfbauth ~/.vnc/password -rfbport 5900 &
sleep 1

echo "=== Adapting backend for Linux ==="
# Copy original backend and adapt for Chromium (no source modification)
cp /app/backend.py /app/backend_linux.py

# Replace Edge with Chromium
sed -i 's/from selenium.webdriver.edge.service import Service/from selenium.webdriver.chrome.service import Service/' /app/backend_linux.py
sed -i 's/service = Service(executable_path=r.*$/service = Service()/' /app/backend_linux.py
sed -i 's/options = webdriver.EdgeOptions()/options = webdriver.ChromeOptions()/' /app/backend_linux.py
sed -i 's/driver = webdriver.Edge(service=service, options=options)/driver = webdriver.Chrome(service=service, options=options)/' /app/backend_linux.py

# Remove interactive input prompts (set to non-empty to show browser in VNC)
sed -i "s/off_ui_input = input.*/off_ui_input = 'show'/" /app/backend_linux.py
sed -i "s/prot = input.*/prot = os.environ.get('PORT', '5000')/" /app/backend_linux.py

# Change host from localhost to 0.0.0.0
sed -i 's/host="localhost"/host="0.0.0.0"/' /app/backend_linux.py

# Add Chrome-specific options
sed -i "/options.add_argument('--no-sandbox')/a\\    options.add_argument('--disable-dev-shm-usage')" /app/backend_linux.py

# Add static file serving for frontend (at the end of file)
sed -i 's/from fastapi import FastAPI, Header, Request, Query, Body/from fastapi import FastAPI, Header, Request, Query, Body\nfrom fastapi.staticfiles import StaticFiles/' /app/backend_linux.py
# Add static mount after uvicorn.run line
sed -i "/uvicorn.run/i\\
# Static files must be mounted after all API routes\\
import os\\
from starlette.responses import FileResponse\\
\\
@app.middleware('http')\\
async def serve_spa(request, call_next):\\
    response = await call_next(request)\\
    if response.status_code == 404 and not request.url.path.startswith('/Api') and not request.url.path.startswith('/Time') and not request.url.path.startswith('/Home'):\\
        file_path = os.path.join('/app/dist', request.url.path.lstrip('/'))\\
        if os.path.isfile(file_path):\\
            return FileResponse(file_path)\\
        return FileResponse('/app/dist/index.html')\\
    return response\\
" /app/backend_linux.py

echo "=== Starting Backend Service ==="
cd /app
python3 backend_linux.py
