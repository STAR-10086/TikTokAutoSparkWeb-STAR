FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    xvfb x11vnc openbox \
    fonts-wqy-microhei fonts-wqy-zenhei fontconfig \
    curl \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY main.py .

# VNC password
RUN mkdir -p ~/.vnc && x11vnc -storepasswd 123456 ~/.vnc/password

EXPOSE 5000

CMD ["python", "main.py"]
