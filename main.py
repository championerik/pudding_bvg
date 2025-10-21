"""
BVG Abfahrtsmonitor - Hauptprogramm

Zeigt Echtzeit-Abfahrtszeiten von 1-2 BVG-Stationen auf einem Display.
Unterstützt Fußweg-Berechnung, Störungsmeldungen und Verspätungen.
"""
import json
import time
import logging
import sys
from typing import Dict, List
from pathlib import Path

from bvg_api import BVGClient
from display import DisplayManager

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Konstanten
DEFAULT_REFRESH_INTERVAL = 15  # Sekunden
MAX_OFFLINE_TIME = 120  # Sekunden bis "Offline"-Status
TARGET_FPS = 5  # Frames pro Sekunde (reicht für Textanzeige)


class AbfahrtMonitor:
    def __init__(self, config_path: str = 'config.json'):
        """
        Initialisiert den Abfahrtsmonitor
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config = self._load_config(config_path)
        self.bvg_client = BVGClient()
        
        # Display-Einstellungen
        width = self.config.get('displayWidth', 800)
        height = self.config.get('displayHeight', 480)
        fullscreen = self.config.get('fullscreen', False)
        test_mode = self.config.get('testMode', False)
        
        self.display = DisplayManager(width, height, fullscreen, test_mode)
        self.running = True
        
    def _load_config(self, config_path: str) -> Dict:
        """Lädt die Konfiguration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validierung
            if 'stations' not in config or len(config['stations']) == 0:
                raise ValueError("Mindestens eine Station muss konfiguriert sein")
            
            logger.info(f"Konfiguration geladen: {len(config['stations'])} Stationen")
            return config
            
        except FileNotFoundError:
            logger.error(f"Konfigurationsdatei nicht gefunden: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen der Konfiguration: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            sys.exit(1)
    
    def fetch_departures_for_stations(self) -> List[Dict]:
        """
        Holt Abfahrten für alle konfigurierten Stationen
        
        Returns:
            Liste von Stations-Daten mit Abfahrten (leer bei Fehler)
        """
        stations_data = []
        display_lines = self.config.get('displayLines', [])
        has_error = False
        
        for i, station in enumerate(self.config['stations']):
            station_id = station['id']
            station_name = station['name']
            walking_time = station.get('walkingTime', 0)
            
            logger.info(f"Hole Abfahrten für {station_name} ({station_id})")
            
            try:
                departures = self.bvg_client.get_departures(station_id)
                disruptions = self.bvg_client.get_disruptions(station_id)
                
                # Test-Modus: Füge künstliche Störungen hinzu
                if self.config.get('testMode', False):
                    if i == 0:  # Erste Station
                        disruptions = [{
                            'type': 'warning',
                            'summary': 'Ersatzverkehr wegen Bauarbeiten',
                            'text': 'SEV zwischen Station A und B'
                        }]
                    elif i == 1:  # Zweite Station
                        disruptions = [{
                            'type': 'status',
                            'summary': 'Verspätungen möglich',
                            'text': 'Aufgrund von Signalstörungen'
                        }]
                
                # Filtere nach konfigurierten Linien (falls angegeben)
                if display_lines:
                    departures = [d for d in departures if d['line'] in display_lines]
                
                stations_data.append({
                    'id': station_id,
                    'name': station_name,
                    'walkingTime': walking_time,
                    'departures': departures,
                    'disruptions': disruptions
                })
            except Exception as e:
                logger.error(f"Fehler beim Abrufen für {station_name}: {e}")
                has_error = True
        
        # Gib leere Liste zurück wenn alle Anfragen fehlgeschlagen sind
        if has_error and not stations_data:
            return []
        
        return stations_data
    
    def run(self):
        """
        Hauptschleife des Monitors
        
        - Holt regelmäßig neue Daten von der BVG API
        - Aktualisiert das Display kontinuierlich
        - Behandelt Fehler graceful
        """
        refresh_interval = self.config.get('refreshInterval', DEFAULT_REFRESH_INTERVAL)
        last_update = 0
        stations_data = []
        
        logger.info("Abfahrtsmonitor gestartet")
        
        try:
            while self.running:
                # Events verarbeiten (Fenster schließen, etc.)
                if not self.display.handle_events():
                    break
                
                # Daten von API aktualisieren
                current_time = time.time()
                if current_time - last_update >= refresh_interval:
                    new_data = self.fetch_departures_for_stations()
                    if new_data:
                        stations_data = new_data
                        self.display.is_live = True
                        self.display.last_update_time = current_time
                        logger.info("Daten erfolgreich aktualisiert")
                    else:
                        # Keine neuen Daten, aber behalte alte
                        self.display.is_live = False
                        logger.warning("Konnte keine neuen Daten abrufen")
                    last_update = current_time
                
                # Prüfe ob Daten zu alt sind
                if current_time - self.display.last_update_time > MAX_OFFLINE_TIME:
                    self.display.is_live = False
                
                # Display aktualisieren (für Uhrzeit, Countdown, Animationen)
                if stations_data:
                    self.display.draw_departures(stations_data)

                self.display.tick(TARGET_FPS)

        except KeyboardInterrupt:
            logger.info("Abbruch durch Benutzer")
        except Exception as e:
            logger.error(f"Fehler in der Hauptschleife: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Räumt Ressourcen auf"""
        logger.info("Beende Abfahrtsmonitor")
        self.display.quit()


def main():
    """Einstiegspunkt"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else './config/config_example.json'
    
    monitor = AbfahrtMonitor(config_path)
    monitor.run()


if __name__ == '__main__':
    main()
