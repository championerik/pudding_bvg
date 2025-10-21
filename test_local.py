#!/usr/bin/env python3
"""
Test-Script zum lokalen Testen (ohne Raspberry Pi)
Simuliert das Display in einem normalen Fenster
"""
import sys
import os
import platform

# Setze Display-Modus für lokales Testen
if platform.system() == 'Darwin':  # macOS
    os.environ['SDL_VIDEODRIVER'] = 'cocoa'
elif platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windows'
else:  # Linux
    os.environ['SDL_VIDEODRIVER'] = 'x11'

from main import AbfahrtMonitor

def main():
    print("🧪 Test-Modus - Startet Monitor im Fenster")
    print("Drücke ESC oder Q zum Beenden")
    print()
    
    config_path = './config/config.json'
    
    # Erstelle Test-Konfiguration falls nötig
    if not os.path.exists(config_path):
        print("⚠️  Keine config.json gefunden. Bitte erstelle eine!")
        sys.exit(1)
    
    monitor = AbfahrtMonitor(config_path=config_path)
    monitor.run()


if __name__ == '__main__':
    main()
