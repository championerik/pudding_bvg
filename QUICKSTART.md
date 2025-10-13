# 🚀 Quick Reference

## Lokales Entwickeln (Mac/PC)

```bash
# Setup
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# oder: venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Stationscodes finden
python3 find_station.py "Alexanderplatz"
python3 find_station.py "Warschauer Str"

# Config erstellen
cp config.example.json config.json
# Dann config.json bearbeiten!

# Testen
python3 test_local.py
```

## Deployment auf Raspberry Pi

### Erste Installation

```bash
# 1. Projekt auf Pi kopieren
scp -r bvg_abfahrt/ pi@raspberrypi.local:~/

# 2. Auf dem Pi einloggen
ssh pi@raspberrypi.local

# 3. Setup ausführen
cd ~/bvg_abfahrt
./setup.sh

# 4. Config anpassen
nano config.json

# 5. Starten
docker-compose up -d
```

### Täglicher Betrieb

```bash
# Status prüfen
docker ps
docker-compose ps

# Logs ansehen
docker-compose logs -f

# Neustarten
docker-compose restart

# Stoppen
docker-compose down

# Nach Config-Änderung neustarten
docker-compose restart
```

### Updates

```bash
# Code aktualisieren
cd ~/bvg_abfahrt
git pull  # wenn Git repo

# Oder neu kopieren:
scp -r bvg_abfahrt/ pi@raspberrypi.local:~/

# Neu bauen und starten
docker-compose down
docker-compose build
docker-compose up -d
```

## Nützliche Docker Befehle

```bash
# Container Shell öffnen
docker exec -it bvg_abfahrt_monitor /bin/bash

# Logs der letzten 100 Zeilen
docker-compose logs --tail=100

# Resourcen-Nutzung
docker stats bvg_abfahrt_monitor

# Image neu bauen (ohne Cache)
docker-compose build --no-cache

# Alles aufräumen
docker system prune -a
```

## BVG API Testen

```bash
# Station suchen
curl "https://v6.bvg.transport.rest/locations?query=Alexanderplatz" | python3 -m json.tool

# Abfahrten abrufen
curl "https://v6.bvg.transport.rest/stops/900000100001/departures?duration=30" | python3 -m json.tool

# Nur erste Abfahrt
curl "https://v6.bvg.transport.rest/stops/900000100001/departures?results=1" | python3 -m json.tool
```

## Raspberry Pi Setup

### Docker installieren
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Neuanmeldung erforderlich!
```

### Display-Einstellungen
```bash
# Framebuffer prüfen
ls -l /dev/fb0

# Display-Auflösung anzeigen
fbset

# HDMI Force aktivieren (in /boot/config.txt)
sudo nano /boot/config.txt
# Hinzufügen:
hdmi_force_hotplug=1
hdmi_drive=2
```

### Autostart einrichten
```bash
# Mit Docker Compose (empfohlen)
cd ~/bvg_abfahrt
docker-compose up -d

# Container startet automatisch neu
```

## Troubleshooting

### Display bleibt schwarz
```bash
# Container läuft?
docker ps

# Logs prüfen
docker logs bvg_abfahrt_monitor

# Framebuffer zugreifbar?
sudo chmod 666 /dev/fb0
```

### API-Fehler
```bash
# Internet-Verbindung
ping -c 3 v6.bvg.transport.rest

# API direkt testen
curl https://v6.bvg.transport.rest/stops/900000100001/departures

# DNS-Problem?
sudo nano /etc/resolv.conf
# nameserver 8.8.8.8 hinzufügen
```

### Zu langsam / Hohe CPU
```bash
# In config.json:
# refreshInterval erhöhen (z.B. 30)
# Weniger Stationen konfigurieren

# Container Ressourcen limitieren
docker update --cpus=".5" --memory="256m" bvg_abfahrt_monitor
```

## Config Beispiele

### Minimal (1 Station)
```json
{
  "stations": [
    {
      "id": "900000100001",
      "name": "S+U Alexanderplatz",
      "walkingTime": 5
    }
  ],
  "refreshInterval": 20,
  "displayLines": [],
  "fullscreen": true
}
```

### Mit Linien-Filter
```json
{
  "stations": [
    {
      "id": "900000100001",
      "name": "S+U Alexanderplatz",
      "walkingTime": 5
    }
  ],
  "refreshInterval": 15,
  "displayLines": ["M1", "M8", "S5", "S7", "S9"],
  "fullscreen": true
}
```

### Zwei Stationen
```json
{
  "stations": [
    {
      "id": "900000100001",
      "name": "S+U Alexanderplatz",
      "walkingTime": 5
    },
    {
      "id": "900000023201",
      "name": "U Weinmeisterstr.",
      "walkingTime": 3
    }
  ],
  "refreshInterval": 15,
  "displayLines": [],
  "displayWidth": 800,
  "displayHeight": 480,
  "fullscreen": true
}
```

## Performance Tipps

1. **refreshInterval**: 15-30 Sekunden ist optimal
2. **Linien-Filter**: Nur relevante Linien anzeigen
3. **Stationen**: Max 2-3 Stationen für beste Performance
4. **Display**: 800x480 ist ideal für Pi Zero 2W

## Bekannte Stationen (Berlin)

```
S+U Alexanderplatz: 900000100001
U Weinmeisterstr.: 900000023201
S+U Warschauer Str.: 900000245025
U Eberswalder Str.: 900000110001
S+U Jannowitzbrücke: 900000100004
U Rosenthaler Platz: 900000100016
```

Mehr finden mit: `python3 find_station.py "<Name>"`
