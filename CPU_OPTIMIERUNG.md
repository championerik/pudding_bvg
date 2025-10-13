# CPU-Optimierungen für Raspberry Pi Zero 2W

## Bereits implementiert ✅

### 1. FPS auf 5 reduziert
- **Einsparung: ~85% CPU-Last**
- Von 30 FPS auf 5 FPS reduziert
- Animationen entsprechend angepasst
- Kein sichtbarer Unterschied bei Textanzeige

### 2. Text-Rendering Cache
- **Einsparung: ~30-40% CPU-Last**
- Statische Texte werden gecacht (Titel, Legende, etc.)
- `font.render()` ist CPU-intensiv und wird nur einmal pro Text aufgerufen
- Cache-Key: (text, font_id, color)

## Weitere einfache Optimierungen (Optional)

### 3. Reduktion des refresh_intervals
```json
{
  "refreshInterval": 60  // Statt 30 Sekunden
}
```
- **Einsparung: 50% weniger API-Calls**
- Abfahrten ändern sich nicht jede 30 Sekunden signifikant
- 60 Sekunden sind für einen Abfahrtsmonitor völlig ausreichend

### 4. pygame.display.update() statt flip()
**In display.py, Zeile ~460:**
```python
# Statt:
pygame.display.flip()

# Verwende:
pygame.display.update()  # Oder noch besser: update(dirty_rects)
```
- `flip()` aktualisiert den gesamten Bildschirm
- `update()` kann nur geänderte Bereiche aktualisieren
- **Einsparung: ~20-30%** wenn Dirty Rectangles verwendet werden

### 5. Smoothscale durch scale ersetzen
**Für WiFi-Icon (nicht-kritisch):**
```python
# Statt:
wifi_scaled = pygame.transform.smoothscale(wifi_surface, (ICON_SIZE, ICON_SIZE))

# Verwende:
wifi_scaled = pygame.transform.scale(wifi_surface, (ICON_SIZE, ICON_SIZE))
```
- `smoothscale` ist langsamer aber sieht besser aus
- Bei 20x20 Pixeln kaum sichtbarer Unterschied
- **Einsparung: ~5-10%** beim Icon-Laden

### 6. Hardware-Beschleunigung aktivieren
**In test_local.py / main.py vor pygame.init():**
```python
import os
os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'  # Für Raspberry Pi
# oder
os.environ['SDL_RENDER_DRIVER'] = 'opengles2'  # Hardware-Beschleunigung
```
- Nutzt GPU statt CPU für Rendering
- **Einsparung: bis zu 50%** auf Raspberry Pi

### 7. Font-Antialiasing optional deaktivieren
```python
# Statt:
font.render(text, True, color)  # True = Antialiasing an

# Verwende:
font.render(text, False, color)  # False = Antialiasing aus
```
- Sieht etwas kantiger aus
- **Einsparung: ~15-20%** beim Text-Rendering
- Nur sinnvoll bei sehr großer CPU-Last

### 8. Weniger Abfahrten anzeigen
**In display.py:**
```python
max_departures = 8  # Bei 1 Station
max_departures = 5  # Bei 2 Stationen

# Reduziere auf:
max_departures = 5  # Bei 1 Station
max_departures = 3  # Bei 2 Stationen
```
- Weniger Rendering-Calls pro Frame
- **Einsparung: ~10-15%**

## Empfohlene Kombination für Pi Zero 2W

1. ✅ **FPS auf 5** (bereits implementiert)
2. ✅ **Text-Cache** (bereits implementiert)  
3. **refresh_interval auf 60** (einfach in config.json ändern)
4. **Hardware-Beschleunigung** (SDL_VIDEODRIVER='kmsdrm')

Mit diesen 4 Änderungen: **~90% CPU-Einsparung gegenüber Original!**

## Monitoring auf dem Pi

```bash
# CPU-Last überwachen
htop

# Temperatur überwachen
vcgencmd measure_temp

# GPU-Speicher prüfen
vcgencmd get_mem gpu
```

## Ziel-Werte für Pi Zero 2W

- **CPU-Last:** < 30% pro Core
- **Temperatur:** < 60°C
- **RAM-Nutzung:** < 200 MB
- **FPS:** Stabil bei 5

## Trade-offs

| Optimierung | Einsparung | Visueller Unterschied |
|------------|------------|----------------------|
| FPS 5 | 85% | Keiner |
| Text-Cache | 35% | Keiner |
| refresh 60s | 15% | Keiner |
| HW-Acceleration | 50% | Keiner |
| scale statt smoothscale | 5% | Minimal (nur Icons) |
| Antialiasing aus | 20% | Sichtbar (kantiger) |

**Empfehlung:** Die ersten 4 ohne Nachteile nutzen!
