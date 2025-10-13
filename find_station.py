#!/usr/bin/env python3
"""
Script zum Finden von BVG Stationscodes
"""
import sys
import requests


def search_station(query: str):
    """Sucht nach Stationen"""
    url = "https://v6.bvg.transport.rest/locations"
    params = {
        'query': query,
        'results': 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        locations = response.json()
        
        if not locations:
            print(f"❌ Keine Stationen gefunden für: '{query}'")
            return
        
        print(f"\n🔍 Suchergebnisse für '{query}':\n")
        print(f"{'ID':<15} {'Name':<40} {'Typ'}")
        print("-" * 80)
        
        for loc in locations:
            if loc.get('type') == 'stop' or loc.get('type') == 'station':
                loc_id = loc.get('id', 'N/A')
                name = loc.get('name', 'N/A')
                loc_type = loc.get('type', 'N/A')
                
                print(f"{loc_id:<15} {name:<40} {loc_type}")
        
        print("\n💡 Kopiere die ID in deine config.json\n")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python find_station.py <stationsname>")
        print("\nBeispiel:")
        print("  python find_station.py Alexanderplatz")
        print("  python find_station.py 'Warschauer Str'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    search_station(query)


if __name__ == '__main__':
    main()
