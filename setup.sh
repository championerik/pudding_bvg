#!/bin/bash

# Setup-Script für Raspberry Pi Zero 2W

set -e

echo "🚀 BVG Abfahrtsmonitor Setup"
echo "=============================="
echo ""

# Docker check
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert!"
    echo "Bitte installiere Docker zuerst:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker $USER"
    exit 1
fi

echo "✅ Docker gefunden"

# Config check
if [ ! -f "config.json" ]; then
    echo "⚠️  config.json nicht gefunden. Erstelle aus Beispiel..."
    cp config.example.json config.json
    echo "📝 Bitte bearbeite config.json mit deinen Stationen!"
    exit 0
fi

echo "✅ config.json gefunden"

# Build Docker Image
echo ""
echo "🔨 Baue Docker Image..."
docker build -t bvg-monitor .

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "Zum Starten:"
echo "  ./run.sh"
echo ""
echo "Für Vollbild auf dem Pi:"
echo "  ./run.sh --fullscreen"
echo ""
