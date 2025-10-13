#!/bin/bash

# Run-Script für den Monitor

FULLSCREEN=""

if [ "$1" = "--fullscreen" ] || [ "$1" = "-f" ]; then
    FULLSCREEN="true"
    # Aktualisiere config.json für Vollbild
    if command -v jq &> /dev/null; then
        jq '.fullscreen = true' config.json > config.tmp.json && mv config.tmp.json config.json
    fi
fi

echo "🚀 Starte BVG Abfahrtsmonitor..."

# Auf Raspberry Pi mit Display
docker run --rm \
    -v $(pwd)/config.json:/app/config.json:ro \
    -v /dev/fb0:/dev/fb0 \
    --privileged \
    -e SDL_FBDEV=/dev/fb0 \
    bvg-monitor
