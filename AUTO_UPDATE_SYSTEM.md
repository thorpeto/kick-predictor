# Auto-Update System für Kick-Predictor

## Übersicht

Das automatische Update-System sorgt dafür, dass die Bundesliga-Daten während der Spielzeiten automatisch aktualisiert werden, ohne dass manuelle Eingriffe erforderlich sind.

## Funktionsweise

### Zeitplan
- **Spieltage**: Freitag, Samstag, Sonntag
- **Aktive Zeiten**: 17:00 - 23:00 Uhr
- **Update-Intervall**: Alle 30 Minuten
- **Cleanup**: Montags um 03:00 Uhr (wöchentliches Cleanup)

### Automatische Erkennung
Das System erkennt automatisch:
- Spieltage (Freitag-Sonntag)
- Aktive Zeiten (17:00-23:00)
- Neue Spielergebnisse
- Abgeschlossene Spiele

### Smart Update Logic
- Überprüft nur während der aktiven Zeiten
- Verhindert unnötige API-Aufrufe außerhalb der Spielzeiten
- Loggt alle Aktivitäten für Debugging

## Backend-Integration

### Automatischer Start
```python
@app.on_event("startup")
async def startup_event():
    start_auto_updater()
```

### API-Endpoints
- `GET /api/auto-updater/status` - Status des Auto-Updaters
- `POST /api/auto-updater/start` - Manueller Start
- `POST /api/auto-updater/stop` - Manueller Stopp
- `GET /api/next-matchday-info` - Spieltag-Informationen mit Auto-Updater Status

### Status-Monitoring
```json
{
  "is_running": true,
  "is_gameday_time": false,
  "last_update": "2025-09-16T17:30:00",
  "update_count": 5,
  "current_time": "2025-09-16T11:32:56",
  "next_scheduled_updates": [
    {
      "date": "2025-09-19",
      "day": "Friday", 
      "times": "17:00-23:00 (alle 30min)"
    }
  ]
}
```

## Frontend-Interface

### Update-Management-Seite
Neue erweiterte Update-Seite mit:
- **Auto-Updater Status**: Live-Anzeige des Updater-Status
- **Spieltag-Informationen**: Nächste Spiele und Wochenenden
- **Manuelle Kontrolle**: Start/Stopp des Auto-Updaters
- **Status-Monitoring**: Automatische Aktualisierung alle 30 Sekunden

### Funktionen
1. **Live-Status**: Echtzeit-Anzeige des Auto-Updater Status
2. **Smart Control**: Ein-/Ausschalten des automatischen Updates
3. **Manual Override**: Sofortige manuelle Updates möglich
4. **Scheduling Info**: Anzeige der geplanten Update-Zeiten

## Technische Details

### Verwendete Bibliotheken
- `schedule`: Python-Bibliothek für zeitbasierte Tasks
- `threading`: Hintergrund-Ausführung ohne UI-Blockierung
- `logging`: Umfassendes Logging aller Aktivitäten

### Dateien
- `gameday_updater.py`: Haupt-Auto-Updater Klasse
- `main_real_data.py`: Integration in FastAPI
- `UpdatePage.tsx`: Frontend-Interface
- `real_data_sync.py`: Daten-Synchronisation

### Konfiguration
```python
# Zeitplan-Konfiguration
GAMEDAY_START_HOUR = 17
GAMEDAY_END_HOUR = 23
UPDATE_INTERVAL_MINUTES = 30
GAMEDAYS = ['friday', 'saturday', 'sunday']
```

## Verwendung

### Automatisch
Das System startet automatisch beim Backend-Start und läuft im Hintergrund.

### Manuell über Frontend
1. Öffne die Update-Seite
2. Sieh den aktuellen Status ein
3. Starte/Stoppe den Auto-Updater bei Bedarf
4. Führe manuelle Updates durch wenn nötig

### API-Aufrufe
```bash
# Status prüfen
curl http://localhost:8000/api/auto-updater/status

# Auto-Updater starten
curl -X POST http://localhost:8000/api/auto-updater/start

# Manuelles Update
curl -X POST http://localhost:8000/api/update-data
```

## Vorteile

1. **Automatisierung**: Keine manuellen Updates während Spielzeiten nötig
2. **Effizienz**: Updates nur wenn tatsächlich Spiele stattfinden
3. **Zuverlässigkeit**: Kontinuierliche Datenaktualisierung
4. **Flexibilität**: Manuelle Kontrolle weiterhin möglich
5. **Monitoring**: Vollständige Transparenz über alle Update-Aktivitäten

## Logs und Debugging

Das System loggt alle Aktivitäten:
```
INFO:gameday_updater:⏰ Automatische Updates geplant:
INFO:gameday_updater:   - Freitag, Samstag, Sonntag: 17:00-23:00 alle 30 Min
INFO:gameday_updater:🚀 Gameday Auto-Updater gestartet...
INFO:gameday_updater:   Aktuelle Zeit: Tuesday, 11:32
INFO:gameday_updater:   Spieltag-Zeit aktiv: False
```

Die Logs helfen bei der Diagnose von Problemen und bieten vollständige Transparenz über alle Update-Aktivitäten.