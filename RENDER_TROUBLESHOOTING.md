# Render Deployment Troubleshooting Guide

## Problem: Frontend lädt unendlich trotz erfolgreichem Deployment

### Hauptursache: Backend-Database-Probleme

Das häufigste Problem ist, dass die SQLite-Datenbank auf Render nicht erstellt werden kann.

#### Sofort-Diagnose:
```bash
# 1. Backend Health Check
curl https://kick-predictor-backend.onrender.com/health
# Erwartete Antwort: {"status":"online"}

# 2. Database Debug Check  
curl https://kick-predictor-backend.onrender.com/api/db/debug
# Zeigt detaillierte Database-Konfiguration

# 3. Database Status
curl https://kick-predictor-backend.onrender.com/api/db/stats
# Zeigt Anzahl von Teams, Matches, Predictions
```

### Mögliche Ursachen und Lösungen:

#### 1. **Database-Disk nicht gemountet (häufigste Ursache)**
- **Problem**: Render Free Tier Disk Mount dauert Zeit oder schlägt fehl
- **Lösung**: System verwendet automatisch Fallback-Pfade (/tmp, /app)
- **Test**: `/api/db/debug` zeigt verfügbare Pfade und deren Status
- **Wartezeit**: 2-3 Minuten nach Deployment für Disk-Mount

#### 2. **Backend schläft (Free Tier)**
- **Problem**: Free Tier Backend schläft nach 15min Inaktivität ein
- **Lösung**: Erste API-Anfrage kann 30-60 Sekunden dauern
- **Test**: https://kick-predictor-backend.onrender.com/health aufrufen

#### 2. **CORS-Probleme**
- **Problem**: Backend erlaubt Frontend-Domain nicht
- **Lösung**: `ALLOWED_ORIGINS` in Render Backend-Service setzen
- **Wert**: `https://kick-predictor-frontend.onrender.com`

#### 3. **Falsche API-URLs**
- **Problem**: Frontend verwendet falsche Backend-URL
- **Test**: `/api-debug` Seite aufrufen für URL-Debugging
- **Fix**: `VITE_API_URL` in Frontend-Service setzen

#### 4. **Database nicht verfügbar**
- **Problem**: SQLite-Datenbank nicht initialisiert
- **Test**: `/api/db/stats` aufrufen
- **Fix**: `/api/db/full-sync` ausführen

### Debugging-Schritte:

1. **Backend Health Check**:
   ```
   curl https://kick-predictor-backend.onrender.com/health
   ```
   Erwartete Antwort: `{"status":"online"}`

2. **Frontend Debug-Seite**:
   - Besuche: `https://kick-predictor-frontend.onrender.com/api-debug`
   - Teste alle Endpoints
   - Prüfe Browser-Konsole für Fehler

3. **Database Status**:
   ```
   curl https://kick-predictor-backend.onrender.com/api/db/stats
   ```

4. **CORS Test**:
   ```
   curl -H "Origin: https://kick-predictor-frontend.onrender.com" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS https://kick-predictor-backend.onrender.com/api/test
   ```

### Fix-Reihenfolge:

1. **Warte 2-3 Minuten** nach Deployment (Backend + DB Startup)
2. **Teste Database Debug** `/api/db/debug` für detaillierte Infos
3. **Synchronisiere Datenbank** `POST /api/db/full-sync` (falls leer)  
4. **Teste Backend direkt** (Health Endpoint)
5. **Prüfe CORS-Konfiguration**
6. **Teste Frontend über Debug-Seite**

### Neue Debug-Tools:

#### Database Debug Endpoint:
```bash
curl https://kick-predictor-backend.onrender.com/api/db/debug
```
Zeigt:
- Database-Pfad-Konfiguration
- Fallback-Pfad-Tests  
- Verzeichnis-Berechtigungen
- Connection-Status

#### Frontend Debug-Seite:
- Besuche: `https://kick-predictor-frontend.onrender.com/api-debug`
- Teste API-Endpoints interaktiv
- Zeigt CORS und Connectivity-Probleme

### Render-spezifische Einstellungen:

#### Backend Service:
```yaml
envVars:
  - key: ENVIRONMENT
    value: production
  - key: ALLOWED_ORIGINS  
    value: "https://kick-predictor-frontend.onrender.com"
  - key: DATABASE_URL
    value: sqlite:////app/data/kick_predictor.db
```

#### Frontend Service:
```yaml
envVars:
  - key: VITE_API_URL
    value: https://kick-predictor-backend.onrender.com
```

### Logs prüfen:
- Render Dashboard → Services → Logs
- Browser Console (F12)
- Network Tab für failed requests

### Häufige Fehlermeldungen:

- **"Network Error"**: Backend schläft → warten oder aufwecken
- **"CORS policy"**: `ALLOWED_ORIGINS` falsch konfiguriert  
- **"404 Not Found"**: API-URL falsch oder Backend nicht deployed
- **"Database error"**: Datenbank-Sync erforderlich

### Quick Fix Commands:

```bash
# Backend aufwecken
curl https://kick-predictor-backend.onrender.com/health

# Datenbank synchronisieren  
curl -X POST https://kick-predictor-backend.onrender.com/api/db/full-sync

# Frontend neu deployen
git push origin main
```