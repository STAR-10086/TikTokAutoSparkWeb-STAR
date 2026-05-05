# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --production=false
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

# Stage 2: Final image
FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Install all dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python
    python3 python3-pip python3-venv \
    # Browser & driver
    chromium chromium-driver \
    # VNC & desktop
    xvfb x11vnc openbox \
    # Chinese fonts
    fonts-wqy-microhei fonts-wqy-zenhei fontconfig \
    # Utilities
    curl ca-certificates \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/*

WORKDIR /app

# Install Python dependencies in virtual environment
COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

# Copy project files
COPY 抖音自动续火花-后端.py ./backend.py
COPY start.sh .
COPY --from=frontend-builder /build/dist ./dist

# Create data directory for persistence
RUN mkdir -p /app/data

# VNC password
RUN mkdir -p ~/.vnc && x11vnc -storepasswd 123456 ~/.vnc/password

EXPOSE 5000 5900

CMD ["/bin/bash", "/app/start.sh"]
