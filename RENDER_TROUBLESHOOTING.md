# Render Deployment Troubleshooting Guide

## Problem: Frontend lädt unendlich trotz erfolgreichem Deployment

### Mögliche Ursachen und Lösungen:

#### 1. **Backend nicht erreichbar (häufigste Ursache)**
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

1. **Warte 2-3 Minuten** nach Deployment (Backend Startup)
2. **Teste Backend direkt** (Health Endpoint)
3. **Synchronisiere Datenbank** (falls leer)
4. **Prüfe CORS-Konfiguration**
5. **Teste Frontend über Debug-Seite**

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