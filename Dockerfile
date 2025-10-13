# Multi-stage build für Raspberry Pi Zero 2W (ARM)
FROM python:3.11-slim-bookworm

# System dependencies für pygame und Display
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Umgebungsvariablen für SDL (kein X11 benötigt)
ENV SDL_VIDEODRIVER=fbcon
ENV SDL_FBDEV=/dev/fb0
ENV SDL_NOMOUSE=1

CMD ["python", "main.py"]
