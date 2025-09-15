# Render Deployment Guide

## Updates für SQLite-Integration

Die Render-Konfiguration wurde für die neue SQLite-basierte Architektur aktualisiert:

### Backend-Updates:
- **Persistente Datenbank**: 1GB Disk-Space für SQLite-Datenbank unter `/app/data`
- **Docker-basiertes Deployment**: Produktions-optimiertes Dockerfile mit Health Checks
- **Umgebungsabhängige Konfiguration**: Automatische Pfad-Erkennung für verschiedene Deployment-Umgebungen
- **Neue Umgebungsvariablen**:
  - `DATABASE_URL`: SQLite-Datenbankpfad (`sqlite:////app/data/kick_predictor.db`)
  - `ENABLE_BACKGROUND_SYNC`: Aktiviert automatische Synchronisation
  - `SYNC_INTERVAL_HOURS`: Sync-Intervall (6 Stunden)
  - `ENVIRONMENT`: `production` für Produktionseinstellungen

### Frontend-Updates:
- **nginx-basiertes Deployment**: Verwendet jetzt Docker mit nginx statt einfachem serve
- **Optimierte Proxy-Konfiguration**: Verbesserte API-Weiterleitung

### Bugfixes:
- ✅ **PermissionError behoben**: Umgebungsabhängige Pfad-Konfiguration
- ✅ **Database Initialization**: Graceful Error Handling für Produktionsumgebung  
- ✅ **User Permissions**: Non-root User mit korrekten Verzeichnis-Berechtigungen

## Deployment-Befehle:

1. **Initial Deployment:**
   ```bash
   render deploy
   ```

2. **Manuelle Datensynchronisation** (nach erstem Deploy):
   ```bash
   curl -X POST https://kick-predictor-backend.onrender.com/api/db/full-sync
   ```

3. **Überwachung der Datenbank**:
   ```bash
   curl https://kick-predictor-backend.onrender.com/api/db/stats
   ```

## Wichtige Hinweise:

- Die SQLite-Datenbank wird automatisch erstellt beim ersten Start
- Background-Sync läuft alle 6 Stunden automatisch
- Logs können in der Render-Console überwacht werden
- Bei Problemen: Health Check unter `/health` verfügbar
- **Render Disk Mount**: `/app/data` wird als persistenter Speicher gemountet

## Performance-Verbesserungen:

- ✅ Lokale SQLite-Datenbank statt API-Calls
- ✅ nginx-Proxy für bessere Frontend-Performance
- ✅ Docker-optimierte Builds
- ✅ Automatische Hintergrund-Synchronisation
- ✅ Umgebungsabhängige Konfiguration ohne hardcodierte Pfade