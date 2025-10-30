"""
BVG Abfahrtsmonitor - Textual UI Version

Terminal-basierter Echtzeit-Abfahrtsmonitor mit Textual
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, DataTable, Label, Button, Input, Select
from textual.reactive import reactive
from textual import work
from textual.timer import Timer
from textual.screen import ModalScreen
from textual.containers import Center

# Für den Import der bestehenden Module
try:
    from bvg_api import BVGClient
except ImportError:
    # Fallback für Demo/Testing
    class BVGClient:
        def get_departures(self, station_id):
            return []
        def get_disruptions(self, station_id):
            return []

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bvg_monitor.log'
)
logger = logging.getLogger(__name__)


class AddStationModal(ModalScreen):
    """Modal zum Hinzufügen einer neuen Station"""
    
    CSS = """
    AddStationModal {
        align: center middle;
    }
    
    #modal-dialog {
        width: 80;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }
    
    #modal-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #search-input {
        margin-bottom: 1;
    }
    
    #station-select {
        margin-bottom: 1;
        height: 10;
    }
    
    #walking-time-input {
        width: 20;
        margin-bottom: 1;
    }
    
    .button-row {
        height: auto;
        margin-top: 1;
    }
    
    .add-button {
        margin-right: 1;
    }
    
    #status-label {
        color: $text-muted;
        margin-top: 1;
        text-align: center;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.search_results: List[Dict] = []
        self.selected_station: Optional[Dict] = None
    
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("🚉 Station hinzufügen", id="modal-title")
            yield Input(
                placeholder="Stationsname eingeben (z.B. Alexanderplatz)...",
                id="search-input"
            )
            yield Select(
                [(f"Suche nach Station...", "none")],
                id="station-select",
                allow_blank=False,
                prompt="Wähle eine Station"
            )
            yield Label("Gehzeit (Minuten, optional):")
            yield Input(
                placeholder="z.B. 5",
                id="walking-time-input",
                type="integer"
            )
            yield Label("", id="status-label")
            with Horizontal(classes="button-row"):
                yield Button("✓ Hinzufügen", id="add-button", variant="success", classes="add-button")
                yield Button("Abbrechen", id="cancel-button", variant="default")
    
    def on_mount(self) -> None:
        """Fokussiere das Suchfeld beim Öffnen"""
        self.query_one("#search-input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Suche starten wenn Enter im Suchfeld gedrückt wird"""
        if event.input.id == "search-input":
            query = event.value.strip()
            if query:
                self.search_stations(query)
    
    @work(exclusive=True)
    async def search_stations(self, query: str) -> None:
        """Sucht nach Stationen über die API"""
        status_label = self.query_one("#status-label", Label)
        status_label.update("🔍 Suche...")
        
        url = "https://v6.bvg.transport.rest/locations"
        params = {
            'query': query,
            'results': 10
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            locations = response.json()
            
            # Filtere nur Stationen/Haltestellen
            stations = [
                loc for loc in locations 
                if loc.get('type') in ['stop', 'station']
            ]
            
            if not stations:
                status_label.update(f"❌ Keine Stationen gefunden für '{query}'")
                return
            
            # Erstelle Select-Optionen
            options = [
                (f"{loc.get('name', 'N/A')} ({loc.get('id', 'N/A')})", loc.get('id', ''))
                for loc in stations
            ]
            
            # Aktualisiere Select Widget
            select = self.query_one("#station-select", Select)
            select.set_options(options)
            
            self.search_results = stations
            status_label.update(f"✓ {len(stations)} Station(en) gefunden")
            
            logger.info(f"Stationssuche: {len(stations)} Ergebnisse für '{query}'")
            
        except requests.RequestException as e:
            status_label.update(f"❌ Netzwerkfehler: {e}")
            logger.error(f"Fehler bei Stationssuche: {e}")
        except Exception as e:
            status_label.update(f"❌ Fehler: {e}")
            logger.error(f"Allgemeiner Fehler bei Stationssuche: {e}")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Wenn eine Station ausgewählt wird"""
        if event.select.id == "station-select":
            station_id = event.value
            
            # Finde die entsprechende Station in den Suchergebnissen
            self.selected_station = next(
                (s for s in self.search_results if s.get('id') == station_id),
                None
            )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handler für Button-Klicks"""
        if event.button.id == "cancel-button":
            self.dismiss(None)
        
        elif event.button.id == "add-button":
            if not self.selected_station:
                status_label = self.query_one("#status-label", Label)
                status_label.update("❌ Bitte wähle eine Station aus")
                return
            
            # Gehzeit auslesen
            walking_input = self.query_one("#walking-time-input", Input)
            try:
                walking_time = int(walking_input.value) if walking_input.value else 0
            except ValueError:
                walking_time = 0
            
            # Station-Daten zusammenstellen
            new_station = {
                'id': self.selected_station.get('id'),
                'name': self.selected_station.get('name'),
                'walkingTime': walking_time
            }
            
            self.dismiss(new_station)


class DisruptionWidget(Static):
    """Widget für Störungsmeldungen"""
    
    def __init__(self, disruptions: List[Dict], **kwargs):
        super().__init__(**kwargs)
        self.disruptions = disruptions
    
    def compose(self) -> ComposeResult:
        if not self.disruptions:
            return
        
        for disruption in self.disruptions:
            dtype = disruption.get('type', 'info')
            symbol = "⚠️" if dtype == "warning" else "ℹ️"
            summary = disruption.get('summary', 'Störung')
            yield Label(f"{symbol} {summary}", classes=f"disruption-{dtype}")


class DepartureTable(Static):
    """Widget für Abfahrtstabelle einer Station"""
    
    def __init__(self, station_data: Dict, station_index: int, **kwargs):
        super().__init__(**kwargs)
        self.station_data = station_data
        self.station_index = station_index
    
    def compose(self) -> ComposeResult:
        station_name = self.station_data['name']
        walking_time = self.station_data.get('walkingTime', 0)
        
        # Header mit Stationsname und Delete-Button
        with Horizontal(classes="station-header-container"):
            header_text = f"🚉 {station_name}"
            if walking_time > 0:
                header_text += f" (🚶 {walking_time} min)"
            yield Label(header_text, classes="station-header")
            yield Button("X", id=f"delete-{self.station_index}", classes="delete-button", variant="error", flat=True)
        
        # Störungsmeldungen
        disruptions = self.station_data.get('disruptions', [])
        if disruptions:
            yield DisruptionWidget(disruptions, classes="disruptions")
        
        # Abfahrtstabelle
        table = DataTable(classes="departures-table")
        table.add_columns("Linie", "Richtung", "Abfahrt", "Verspätung")
        table.cursor_type = "none"
        
        departures = self.station_data.get('departures', [])
        
        if not departures:
            yield Label("Keine Abfahrten verfügbar", classes="no-data")
        else:
            for dep in departures[:8]:  # Maximal 8 Abfahrten
                line = dep.get('line', '?')
                direction = dep.get('direction', 'Unbekannt')
                when = dep.get('when', '')
                delay = dep.get('delay', 0)
                
                # Zeitberechnung
                try:
                    # Handle both datetime objects and ISO strings
                    if isinstance(when, datetime):
                        dep_time = when
                    else:
                        dep_time = datetime.fromisoformat(when.replace('Z', '+00:00'))
                    
                    now = datetime.now(dep_time.tzinfo) if dep_time.tzinfo else datetime.now()
                    minutes = int((dep_time - now).total_seconds() / 60)
                    
                    if minutes <= 0:
                        time_str = "Jetzt"
                    elif minutes == 1:
                        time_str = "1 min"
                    else:
                        time_str = f"{minutes} min"
                except Exception as e:
                    # Fallback: try to display 'minutes' field if available
                    if 'minutes' in dep:
                        minutes = dep['minutes']
                        time_str = f"{minutes} min" if minutes > 1 else "1 min"
                    else:
                        time_str = str(when)[:5] if when else "?"
                
                # Verspätung
                if delay and delay > 0:
                    delay_str = f"+{delay // 60} min"
                    delay_class = "delay"
                else:
                    delay_str = "pünktlich"
                    delay_class = "on-time"
                
                # Kürze lange Richtungsnamen
                if len(direction) > 40:
                    direction = direction[:39] + "..."
                
                table.add_row(
                    f"[bold cyan]{line}[/]",
                    direction,
                    f"[yellow]{time_str}[/]",
                    f"[{delay_class}]{delay_str}[/]"
                )
            
            yield table


class AddStationButton(Static):
    """Button zum Hinzufügen einer neuen Station"""
    
    CSS = """
    AddStationButton {
        height: auto;
        margin: 1 2; 
        padding: 1;
        align: center middle;
    }
    
    #add-station-btn {
        width: auto; 
        min-width: 15;  
        align: center middle;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Center():
            yield Button("+", id="add-station-btn", variant="success", flat=True)


class StatusBar(Static):
    """Statusleiste mit Uhrzeit und Update-Info"""
    
    is_live = reactive(True)
    current_time = reactive("")
    last_update = reactive("")
    has_unsaved_changes = reactive(False)
    
    def compose(self) -> ComposeResult:
        yield Label(id="status-content")
    
    def watch_is_live(self, is_live: bool) -> None:
        self.update_status()
    
    def watch_current_time(self, time: str) -> None:
        self.update_status()
    
    def watch_last_update(self, time: str) -> None:
        self.update_status()
    
    def watch_has_unsaved_changes(self, has_changes: bool) -> None:
        self.update_status()
    
    def update_status(self) -> None:
        status_label = self.query_one("#status-content", Label)
        
        status_icon = "🟢" if self.is_live else "🔴"
        status_text = "Live" if self.is_live else "Offline"
        
        content = f"{status_icon} {status_text} | 🕐 {self.current_time}"
        if self.last_update:
            content += f" | Aktualisiert: {self.last_update}"
        if self.has_unsaved_changes:
            content += " | ⚠️ Ungespeicherte Änderungen"
        
        status_label.update(content)


class BVGMonitorApp(App):
    """Hauptanwendung für den BVG Monitor"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $accent;
        color: $text;
    }
    
    .station-header-container {
        background: $primary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
        height: auto;
        align: right top;
    }
    
    .station-header {
        width: 1fr;
        text-style: bold;
    }
    
    .delete-button {
        width: auto;
        min-width: 3;  # Changed from 10
        margin-left: 1;
        margin-top: 0;  # Add this line
        margin-right: 1;  # Add this line
    }
    
    .disruptions {
        background: $warning;
        color: $text;
        padding: 1;
        margin-bottom: 1;
    }
    
    .disruption-warning {
        color: $error;
        text-style: bold;
    }
    
    .disruption-status {
        color: $warning;
    }
    
    .departures-table {
        height: auto;
        margin-bottom: 2;
    }
    
    .no-data {
        color: $text-muted;
        padding: 1;
        text-align: center;
    }
    
    StatusBar {
        dock: bottom;
        height: 3;
        background: $panel;
        color: $text;
        padding: 1;
    }
    
    #main-container {
        height: 100%;
        overflow-y: auto;
    }
    
    .station-container {
        border: solid $primary;
        margin: 1 2;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Beenden"),
        ("f5", "refresh", "Aktualisieren"),
        ("s", "save", "Speichern"),
        ("a", "add_station", "Station hinzufügen"),
    ]
    
    def __init__(self, config_path: str = 'config.json'):
        super().__init__()
        self.config_path = config_path
        self.config = {}
        self.original_config = {}  # Für Änderungsverfolgung
        self.bvg_client = BVGClient()
        self.stations_data = []
        self.update_timer: Timer | None = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield VerticalScroll(id="main-container")
        yield StatusBar(id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Wird beim Start aufgerufen"""
        self.title = "BVG Abfahrtsmonitor"
        self.sub_title = "Echtzeit-Abfahrtsinformationen"
        
        # Konfiguration laden
        if not self._load_config():
            self.exit(message="Fehler beim Laden der Konfiguration")
            return
        
        # Erste Daten laden
        self.refresh_data()
        
        # Auto-Update Timer starten
        refresh_interval = self.config.get('refreshInterval', 15)
        self.update_timer = self.set_interval(refresh_interval, self.refresh_data)
        
        # Uhrzeit-Timer
        self.set_interval(1, self.update_clock)
    
    def _load_config(self) -> bool:
        """Lädt die Konfiguration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Original-Konfiguration speichern
            self.original_config = json.loads(json.dumps(self.config))
            
            if 'stations' not in self.config:
                self.config['stations'] = []
            
            logger.info(f"Konfiguration geladen: {len(self.config['stations'])} Stationen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            return False
    
    def _save_config(self) -> bool:
        """Speichert die Konfiguration in die Datei"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            # Original-Konfiguration aktualisieren
            self.original_config = json.loads(json.dumps(self.config))
            
            # Status aktualisieren
            status_bar = self.query_one(StatusBar)
            status_bar.has_unsaved_changes = False
            
            logger.info("Konfiguration erfolgreich gespeichert")
            self.notify("Konfiguration gespeichert ✓", severity="information")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            self.notify(f"Fehler beim Speichern: {e}", severity="error")
            return False
    
    def _has_unsaved_changes(self) -> bool:
        """Prüft, ob es ungespeicherte Änderungen gibt"""
        return json.dumps(self.config, sort_keys=True) != json.dumps(self.original_config, sort_keys=True)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handler für Button-Klicks"""
        button_id = event.button.id
        
        if button_id and button_id.startswith("delete-"):
            # Station-Index aus Button-ID extrahieren
            station_index = int(button_id.split("-")[1])
            self.delete_station(station_index)
        
        elif button_id == "add-station-btn":
            self.action_add_station()
    
    def delete_station(self, station_index: int) -> None:
        """Löscht eine Station aus der Konfiguration"""
        if 0 <= station_index < len(self.config['stations']):
            station_name = self.config['stations'][station_index]['name']
            
            # Station aus Konfiguration entfernen
            del self.config['stations'][station_index]
            
            # Status aktualisieren
            status_bar = self.query_one(StatusBar)
            status_bar.has_unsaved_changes = self._has_unsaved_changes()
            
            # Daten neu laden
            self.refresh_data()
            
            self.notify(f"Station '{station_name}' entfernt (nicht gespeichert)", severity="information")
            logger.info(f"Station gelöscht: {station_name}")
    
    def action_add_station(self) -> None:
        """Öffnet den Dialog zum Hinzufügen einer Station"""
        def handle_result(new_station: Optional[Dict]) -> None:
            if new_station:
                self.add_station(new_station)
        
        self.push_screen(AddStationModal(), handle_result)
    
    def add_station(self, station_data: Dict) -> None:
        """Fügt eine neue Station zur Konfiguration hinzu"""
        # Prüfe ob Station bereits existiert
        existing = any(s['id'] == station_data['id'] for s in self.config['stations'])
        
        if existing:
            self.notify(f"Station '{station_data['name']}' bereits vorhanden!", severity="warning")
            return
        
        # Station hinzufügen
        self.config['stations'].append(station_data)
        
        # Status aktualisieren
        status_bar = self.query_one(StatusBar)
        status_bar.has_unsaved_changes = self._has_unsaved_changes()
        
        # Daten neu laden
        self.refresh_data()
        
        self.notify(f"Station '{station_data['name']}' hinzugefügt (nicht gespeichert)", severity="information")
        logger.info(f"Station hinzugefügt: {station_data['name']}")
    
    @work(exclusive=True)
    async def refresh_data(self) -> None:
        """Holt neue Daten von der API"""
        stations_data = []
        display_lines = self.config.get('displayLines', [])
        
        for i, station in enumerate(self.config['stations']):
            station_id = station['id']
            station_name = station['name']
            walking_time = station.get('walkingTime', 0)
            
            try:
                departures = self.bvg_client.get_departures(station_id)
                disruptions = self.bvg_client.get_disruptions(station_id)
                
                # Test-Modus: Künstliche Daten
                if self.config.get('testMode', False):
                    departures = self._generate_test_departures(i)
                    if i == 0:
                        disruptions = [{
                            'type': 'warning',
                            'summary': 'Ersatzverkehr wegen Bauarbeiten',
                            'text': 'SEV zwischen Station A und B'
                        }]
                
                # Filtere nach konfigurierten Linien
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
        
        self.stations_data = stations_data
        self.update_display()
        
        status_bar = self.query_one(StatusBar)
        status_bar.is_live = True
        status_bar.last_update = datetime.now().strftime("%H:%M:%S")
    
    def _generate_test_departures(self, station_index: int) -> List[Dict]:
        """Generiert Test-Abfahrten"""
        from datetime import timedelta
        
        lines = [
            ("U5", "Hönow"), ("U5", "Hauptbahnhof"),
            ("M5", "Hackescher Markt"), ("M5", "Zingster Str."),
            ("142", "S+U Pankow"), ("N5", "S Hackescher Markt")
        ]
        
        departures = []
        now = datetime.now()
        
        for i, (line, direction) in enumerate(lines):
            dep_time = now + timedelta(minutes=2 + i * 3 + station_index * 2)
            delay = 60 if i % 3 == 0 else 0  # Jede dritte Linie verspätet
            
            departures.append({
                'line': line,
                'direction': direction,
                'when': dep_time.isoformat(),
                'delay': delay
            })
        
        return departures
    
    def update_display(self) -> None:
        """Aktualisiert die Anzeige mit neuen Daten"""
        container = self.query_one("#main-container", VerticalScroll)
        container.remove_children()
        
        for i, station_data in enumerate(self.stations_data):
            station_widget = DepartureTable(
                station_data,
                station_index=i,
                classes="station-container"
            )
            container.mount(station_widget)
        
        # Button zum Hinzufügen einer Station (immer am Ende)
        container.mount(AddStationButton())
    
    def update_clock(self) -> None:
        """Aktualisiert die Uhrzeit in der Statusleiste"""
        status_bar = self.query_one(StatusBar)
        status_bar.current_time = datetime.now().strftime("%H:%M:%S")
    
    def action_refresh(self) -> None:
        """Manuelles Aktualisieren"""
        self.refresh_data()
    
    def action_save(self) -> None:
        """Speichert die Konfiguration"""
        if not self._has_unsaved_changes():
            self.notify("Keine Änderungen zum Speichern", severity="information")
            return
        
        self._save_config()
    
    def action_quit(self) -> None:
        """Beendet die Anwendung"""
        if self._has_unsaved_changes():
            # Warnung bei ungespeicherten Änderungen
            self.notify("Warnung: Ungespeicherte Änderungen gehen verloren!", severity="warning")
        self.exit()


def main():
    """Einstiegspunkt"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else './config/config.json'
    
    app = BVGMonitorApp(config_path)
    app.run()


if __name__ == '__main__':
    main()