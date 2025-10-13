# 🚊 BVG Abfahrtsmonitor

Minimalistisches Abfahrtsanzeige-System für Raspberry Pi Zero 2W mit mini-HDMI Display. Perfekt für #### Methode 3: Mit Docker Compose

```bash
# Starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f

# Stoppen
docker-compose down
```

#### Methode 4: Manuellm die nächsten Abfahrten auf einen Blick zu sehen!

## ✨ Features

- 📊 Zeigt Abfahrtszeiten von 1-2 BVG-Stationen (dynamisches Layout)
- ⏱️ Aktualisiert automatisch alle paar Sekunden (konfigurierbar)
- 🚶 Zieht Fußweg-Zeit ab - siehst nur die Züge, die du wirklich erreichst!
- 🎨 Minimalistisches, übersichtliches Design
- 🔴 Farbcodierung: Rot (knapp ≤2 min), Gelb (eilig 3-5 min), Grün (entspannt >5 min)
- ⏰ Zeigt Verspätungen an
- ⚠️ Störungswarnungen von der BVG
- 🚇 Produkt-Badges (U-Bahn, S-Bahn, Tram, Bus) in offiziellen BVG-Farben
- 📜 Automatisches Scrollen bei langen Zielnamen
- ⚡ Blinken bei "jetzt"-Abfahrten (Badge, Name und Zeit)
- 🐳 Läuft in Docker auf Raspberry Pi Zero 2W
- 🔌 Plug & Play mit mini-HDMI Display

## 🚀 Quick Start

### 1. Stationscodes finden

Nutze das Helper-Script:

```bash
python3 find_station.py "Alexanderplatz"
# oder mit Make:
make find-station STATION="Alexanderplatz"
```

Oder besuche: https://v6.bvg.transport.rest/locations?query=DeineStation

### 2. Konfiguration erstellen

Kopiere `config.example.json` nach `config.json` und passe sie an:

**Option A: Zwei Stationen (Zweispalten-Layout):**
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
  "fullscreen": false
}
```

**Option B: Eine Station (Vollbreite, mehr Abfahrten):**
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
  "displayLines": [],
  "displayWidth": 800,
  "displayHeight": 480,
  "fullscreen": false
}
```

**Wichtige Parameter:**
- `stations`: 1-2 Stationen (1 = volle Breite, 2 = zweispaltig)
- `walkingTime`: Minuten von deiner Haustür zur Station
- `refreshInterval`: Sekunden zwischen API-Updates (empfohlen: 10-30)
- `displayLines`: Leer = alle Linien, oder z.B. `["M1", "M8", "S5"]` für bestimmte Linien
- `fullscreen`: `true` für Vollbild auf dem Pi
- `testMode`: `true` für Test-Störungsmeldungen

### 3. Lokales Testen (optional)

Teste das Display lokal auf deinem Mac/PC:

```bash
# Python Environment erstellen
python3 -m venv venv
source venv/bin/activate  # auf macOS/Linux

# Dependencies installieren
pip install -r requirements.txt

# Starten
python3 test_local.py
```

## 🔧 Installation auf Raspberry Pi Zero 2W

### Voraussetzungen

1. **Raspberry Pi OS Lite** (oder Full) installiert
2. **Docker installiert:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   # Neuanmeldung erforderlich!
   ```

### Deployment

#### Methode 1: Mit Makefile (am einfachsten!)

```bash
# Setup
make setup

# Config bearbeiten
nano config.json

# Bauen und starten
make build
make run

# Logs ansehen
make logs

# Hilfe
make help
```

#### Methode 2: Mit Setup-Script

```bash
# Projekt auf den Pi kopieren
scp -r bvg_abfahrt pi@raspberry.local:~/

# Auf dem Pi
cd ~/bvg_abfahrt
./setup.sh

# Starten
./run.sh --fullscreen
```

#### Methode 3: Mit Docker Compose

```bash
# Starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f

# Stoppen
docker-compose down
```

#### Methode 3: Manuell

```bash
# Image bauen
docker build -t bvg-monitor .

# Starten
docker run -d \
  --name bvg-monitor \
  --restart unless-stopped \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v /dev/fb0:/dev/fb0 \
  --privileged \
  bvg-monitor
```

## 🎨 Display Layout

```
┌─────────────────────────────────────────────┐
│ BVG Abfahrten              12:34:56         │
├─────────────────────────────────────────────┤
│ S+U Alexanderplatz (Fußweg: 5 min)         │
├─────────────────────────────────────────────┤
│ M1   → Rosenthal Nord              3 min    │
│ M8   → Ahrensfelde                 7 min    │
│ S5   → Strausberg Nord            12 min    │
│ S7   → Ahrensfelde                14 min    │
│                                              │
│ U Weinmeisterstr. (Fußweg: 3 min)          │
├─────────────────────────────────────────────┤
│ U8   → Hermannstraße              2 min     │
│ U8   → Wittenau                   8 min     │
└─────────────────────────────────────────────┘
```

**Farbcodierung der Zeiten:**
- 🔴 Rot: ≤ 2 min (knapp!) oder bereits verpasst
- 🟡 Gelb: 3-5 min (beeilen!)
- 🟢 Grün: > 5 min (entspannt)

## 📁 Projektstruktur

```
bvg_abfahrt/
├── main.py              # Hauptprogramm
├── bvg_api.py          # BVG API Client
├── display.py          # Display Manager (pygame)
├── find_station.py     # Helper: Stationscodes finden
├── test_local.py       # Lokales Testen
├── config.json         # Deine Konfiguration
├── config.example.json # Beispiel-Config
├── requirements.txt    # Python Dependencies
├── Dockerfile          # Docker Image Definition
├── docker-compose.yml  # Docker Compose Config
├── setup.sh           # Setup-Script für Pi
├── run.sh             # Run-Script
└── README.md          # Diese Datei
```

## 🔍 Troubleshooting

### Display zeigt nichts an

```bash
# Prüfe ob Container läuft
docker ps

# Logs ansehen
docker logs bvg-monitor

# Framebuffer prüfen
ls -l /dev/fb0
```

### API-Fehler

```bash
# Teste API manuell
curl "https://v6.bvg.transport.rest/stops/900000100001/departures"

# Prüfe Internet-Verbindung
ping -c 3 v6.bvg.transport.rest
```

### Falsche Stationscodes

```bash
# Suche nach richtigen Codes
python3 find_station.py "Deine Station"
```

## 🔄 Autostart auf dem Pi

Damit der Monitor beim Booten automatisch startet:

```bash
# Mit Docker Compose
cd ~/bvg_abfahrt
docker-compose up -d

# Docker Compose startet Container automatisch neu (restart: unless-stopped)
```

Oder mit systemd:

```bash
sudo nano /etc/systemd/system/bvg-monitor.service
```

```ini
[Unit]
Description=BVG Abfahrtsmonitor
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/bvg_abfahrt
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bvg-monitor
sudo systemctl start bvg-monitor
```

## 🛠️ Entwicklung

```bash
# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Lokales Testen
python3 test_local.py

# Code-Style (optional)
pip install black
black *.py
```

## 📝 Nützliche Links

- [BVG REST API Dokumentation](https://v6.bvg.transport.rest/api.html)
- [Pygame Dokumentation](https://www.pygame.org/docs/)
- [Docker auf Raspberry Pi](https://docs.docker.com/engine/install/debian/)

## 🤝 Beitragen

Pull Requests sind willkommen! Für größere Änderungen bitte zuerst ein Issue öffnen.

## 📄 Lizenz

MIT License - Nutze es wie du möchtest!

## 💡 Ideen für Erweiterungen

- [x] Störungsmeldungen
- [ ] Touch-Interface für Einstellungen
- [ ] Web-Interface für Remote-Konfiguration
- [ ] Nachtmodus (Display aus zwischen 23-6 Uhr)
- [ ] Mehrere Anzeigeseiten (durchrotieren)
- [ ] Integration mit Home Assistant
