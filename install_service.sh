#!/bin/bash

# Installiert den systemd Service für Autostart

set -e

echo "📦 Installiere BVG Monitor Systemd Service"
echo ""

# Check ob wir auf dem Pi sind
if [ ! -d "/home/pi" ]; then
    echo "⚠️  Dieses Script ist für Raspberry Pi gedacht"
    echo "    Pfade müssen evtl. angepasst werden"
fi

# Kopiere Service-Datei
echo "📝 Kopiere Service-Datei..."
sudo cp bvg-monitor.service /etc/systemd/system/

# Reload systemd
echo "🔄 Lade systemd neu..."
sudo systemctl daemon-reload

# Enable service
echo "✅ Aktiviere Service..."
sudo systemctl enable bvg-monitor.service

echo ""
echo "✅ Installation abgeschlossen!"
echo ""
echo "Befehle:"
echo "  sudo systemctl start bvg-monitor    # Starten"
echo "  sudo systemctl stop bvg-monitor     # Stoppen"
echo "  sudo systemctl status bvg-monitor   # Status"
echo "  sudo systemctl restart bvg-monitor  # Neustarten"
echo "  sudo journalctl -u bvg-monitor -f   # Logs ansehen"
echo ""
echo "Der Monitor startet jetzt automatisch beim Booten! 🎉"
