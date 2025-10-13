#!/usr/bin/env python3
"""
Validiert die config.json
"""
import json
import sys
from pathlib import Path


def validate_config(config_path='config.json'):
    """Validiert die Konfiguration"""
    errors = []
    warnings = []
    
    # Datei existiert?
    if not Path(config_path).exists():
        print(f"❌ Datei nicht gefunden: {config_path}")
        return False
    
    # JSON parsen
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Ungültiges JSON: {e}")
        return False
    
    # Stations prüfen
    if 'stations' not in config:
        errors.append("'stations' fehlt")
    elif not isinstance(config['stations'], list):
        errors.append("'stations' muss eine Liste sein")
    elif len(config['stations']) == 0:
        errors.append("Mindestens eine Station erforderlich")
    else:
        for i, station in enumerate(config['stations']):
            if 'id' not in station:
                errors.append(f"Station {i}: 'id' fehlt")
            if 'name' not in station:
                warnings.append(f"Station {i}: 'name' fehlt (empfohlen)")
            if 'walkingTime' not in station:
                warnings.append(f"Station {i}: 'walkingTime' fehlt (Standard: 0)")
    
    # refreshInterval prüfen
    if 'refreshInterval' in config:
        interval = config['refreshInterval']
        if not isinstance(interval, (int, float)) or interval < 5:
            warnings.append(f"refreshInterval sollte >= 5 sein (aktuell: {interval})")
    
    # displayLines prüfen
    if 'displayLines' in config:
        if not isinstance(config['displayLines'], list):
            errors.append("'displayLines' muss eine Liste sein")
    
    # Display-Dimensionen
    if 'displayWidth' in config and config['displayWidth'] < 480:
        warnings.append(f"displayWidth sehr klein: {config['displayWidth']}")
    if 'displayHeight' in config and config['displayHeight'] < 320:
        warnings.append(f"displayHeight sehr klein: {config['displayHeight']}")
    
    # Ergebnisse ausgeben
    print("🔍 Validierung der config.json\n")
    
    if errors:
        print("❌ Fehler gefunden:")
        for error in errors:
            print(f"   - {error}")
        print()
    
    if warnings:
        print("⚠️  Warnungen:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ Konfiguration ist valide!")
        print(f"\n📊 Zusammenfassung:")
        print(f"   - Stationen: {len(config['stations'])}")
        print(f"   - Refresh: {config.get('refreshInterval', 15)}s")
        print(f"   - Linien-Filter: {len(config.get('displayLines', []))} Linien")
        print(f"   - Display: {config.get('displayWidth', 800)}x{config.get('displayHeight', 480)}")
        print(f"   - Vollbild: {config.get('fullscreen', False)}")
        return True
    
    return len(errors) == 0


if __name__ == '__main__':
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    success = validate_config(config_path)
    sys.exit(0 if success else 1)
