.PHONY: help setup build run stop logs clean test find-station validate

help:
	@echo "🚊 BVG Abfahrtsmonitor - Befehle"
	@echo ""
	@echo "  make setup          - Initiales Setup (Config erstellen)"
	@echo "  make validate       - Config validieren"
	@echo "  make build          - Docker Image bauen"
	@echo "  make run            - Monitor starten"
	@echo "  make stop           - Monitor stoppen"
	@echo "  make restart        - Monitor neustarten"
	@echo "  make logs           - Logs anzeigen"
	@echo "  make test           - Lokales Testen (Python)"
	@echo "  make find-station   - Station suchen (STATION='Name')"
	@echo "  make clean          - Alles aufräumen"

setup:
	@if [ ! -f config.json ]; then \
		cp config.example.json config.json; \
		echo "✅ config.json erstellt"; \
		echo "📝 Bitte bearbeite config.json mit deinen Stationen!"; \
	else \
		echo "⚠️  config.json existiert bereits"; \
	fi

validate:
	@python3 validate_config.py

build:
	@echo "🔨 Baue Docker Image..."
	docker-compose build

run:
	@echo "🚀 Starte Monitor..."
	docker-compose up -d
	@echo "✅ Monitor läuft! Logs mit: make logs"

stop:
	@echo "🛑 Stoppe Monitor..."
	docker-compose down

restart:
	@echo "🔄 Starte Monitor neu..."
	docker-compose restart

logs:
	docker-compose logs -f

test:
	@echo "🧪 Starte lokalen Test..."
	@if [ ! -d venv ]; then \
		echo "Erstelle Virtual Environment..."; \
		python3 -m venv venv; \
		. venv/bin/activate && pip install -r requirements.txt; \
	fi
	@. venv/bin/activate && python3 test_local.py

find-station:
	@if [ -z "$(STATION)" ]; then \
		echo "❌ Bitte gib einen Stationsnamen an:"; \
		echo "   make find-station STATION='Alexanderplatz'"; \
	else \
		python3 find_station.py "$(STATION)"; \
	fi

clean:
	@echo "🧹 Räume auf..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Fertig!"

install:
	@echo "📦 Installiere Python Dependencies..."
	pip install -r requirements.txt
