"""
BVG API Client

Wrapper für die BVG REST API v6 (https://v6.bvg.transport.rest)
Holt Abfahrtszeiten und Störungsmeldungen.
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# API Konstanten
API_BASE_URL = "https://v6.bvg.transport.rest"
API_TIMEOUT = 10  # Sekunden
DEFAULT_RESULTS = 20  # Anzahl Ergebnisse pro Anfrage
DEFAULT_DURATION = 60  # Minuten Zeitfenster


class BVGClient:
    """Client für die BVG REST API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BVG-Abfahrt-Monitor/1.0'
        })
    
    def get_departures(self, station_id: str, duration: int = DEFAULT_DURATION) -> List[Dict]:
        """
        Holt Abfahrten für eine Station
        
        Args:
            station_id: BVG Stations-ID (z.B. "900000100001")
            duration: Zeitfenster in Minuten
            
        Returns:
            Liste von Abfahrts-Dictionaries mit Feldern:
            - line: Liniennummer
            - direction: Zielrichtung
            - minutes: Minuten bis Abfahrt
            - delay: Verspätung in Minuten
            - product: Produkttyp (subway, bus, etc.)
        """
        try:
            url = f"{API_BASE_URL}/stops/{station_id}/departures"
            params = {
                'duration': duration,
                'results': DEFAULT_RESULTS,
                'remarks': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            departures = response.json().get('departures', [])
            return self._parse_departures(departures)
            
        except requests.RequestException as e:
            logger.error(f"API-Fehler beim Abrufen der Abfahrten: {e}")
            return []
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Abrufen der Abfahrten: {e}")
            return []
    
    def get_disruptions(self, station_id: str) -> List[Dict]:
        """
        Holt Störungsmeldungen für eine Station
        
        Args:
            station_id: BVG Stations-ID
            
        Returns:
            Liste von Störungs-Dictionaries mit Feldern:
            - type: Art der Störung (warning, status, hint)
            - summary: Kurzbeschreibung
            - text: Volltext
        """
        try:
            url = f"{API_BASE_URL}/stops/{station_id}"
            params = {'remarks': 'true'}
            
            response = self.session.get(url, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            remarks = data.get('remarks', [])
            
            # Filtere relevante Störungen
            disruptions = []
            for remark in remarks:
                remark_type = remark.get('type', '')
                if remark_type in ['warning', 'status', 'hint']:
                    disruptions.append({
                        'type': remark_type,
                        'summary': remark.get('summary', remark.get('text', 'Störung')),
                        'text': remark.get('text', '')
                    })
            
            return disruptions
            
        except requests.RequestException as e:
            logger.error(f"API-Fehler beim Abrufen der Störungen: {e}")
            return []
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Abrufen der Störungen: {e}")
            return []
    
    def _parse_departures(self, departures: List[Dict]) -> List[Dict]:
        """Parst und filtert Abfahrtsdaten"""
        parsed = []
        now = datetime.now()
        
        for dep in departures:
            try:
                # Geplante und tatsächliche Abfahrtszeit
                when_str = dep.get('when')
                planned_when_str = dep.get('plannedWhen')
                
                if not when_str:
                    continue
                
                # Parse ISO 8601 datetime
                when = datetime.fromisoformat(when_str.replace('Z', '+00:00'))
                planned_when = datetime.fromisoformat(planned_when_str.replace('Z', '+00:00')) if planned_when_str else when
                
                # Konvertiere zu lokaler Zeit (naive datetime für Vergleich)
                when = when.replace(tzinfo=None)
                planned_when = planned_when.replace(tzinfo=None)
                
                # Verspätung berechnen
                delay = int((when - planned_when).total_seconds() / 60)
                
                # Minuten bis Abfahrt
                minutes_until = int((when - now).total_seconds() / 60)
                
                if minutes_until < 0:
                    continue
                
                line = dep.get('line', {})
                
                parsed.append({
                    'line': line.get('name', '?'),
                    'direction': dep.get('direction', 'Unbekannt'),
                    'minutes': minutes_until,
                    'delay': delay,
                    'when': when,
                    'product': line.get('product', 'unknown')
                })
                
            except Exception as e:
                logger.warning(f"Fehler beim Parsen einer Abfahrt: {e}")
                continue
        
        # Sortiere nach Zeit
        parsed.sort(key=lambda x: x['minutes'])
        return parsed
