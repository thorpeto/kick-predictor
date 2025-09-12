# API-Verbindungsprobleme auf Render.com beheben

Wenn im Render Deployment keine Daten über die API bezogen werden, gibt es mehrere mögliche Ursachen und Lösungen.

## 1. CORS-Probleme

### Symptome:
- Browser-Konsole zeigt CORS-Fehler
- Requests werden blockiert mit "Access to fetch at '...' from origin '...' has been blocked by CORS policy"

### Lösungen:
1. **Backend CORS-Konfiguration prüfen:**
   - Stellen Sie sicher, dass die Frontend-URL in `ALLOWED_ORIGINS` enthalten ist
   - Verwenden Sie Wildcards für Render.com: `https://*.onrender.com`

2. **Umgebungsvariablen in Render.com setzen:**
   ```
   ALLOWED_ORIGINS=https://ihr-frontend.onrender.com,https://*.onrender.com
   ```

## 2. Falsche API-URL-Konfiguration

### Symptome:
- 404-Fehler oder Connection Refused
- API-Calls gehen an die falsche URL

### Debugging:
1. **Browser-Konsole öffnen** und nach Log-Meldungen suchen:
   ```
   API_URL configured as: ...
   Fetching next matchday from: ...
   ```

2. **Überprüfen Sie die VITE_API_URL:**
   - In Render.com sollte sie auf `https://ihr-backend.onrender.com` zeigen
   - NICHT auf eine relative URL wie `/api`

### Lösung:
Setzen Sie die korrekte Backend-URL in den Render.com Umgebungsvariablen:
```
VITE_API_URL=https://kick-predictor-backend.onrender.com
```

## 3. Backend-Service nicht erreichbar

### Symptome:
- Timeout-Fehler
- 502/503 HTTP-Statuscodes
- "Service Unavailable" Meldungen

### Debugging:
1. **Backend-Health-Check testen:**
   ```
   https://ihr-backend.onrender.com/health
   ```
   Sollte `{"status": "online"}` zurückgeben

2. **Render.com Logs prüfen:**
   - Gehen Sie zu Ihrem Backend-Service in Render.com
   - Überprüfen Sie die "Logs" für Fehler

### Lösungen:
1. **Free Tier Spin-Down:** Kostenlose Render-Services gehen nach 15 Minuten Inaktivität "schlafen"
   - Der erste Request kann 30+ Sekunden dauern
   - Erwägen Sie einen Paid Plan für Production

2. **Backend-Deployment-Fehler:** Überprüfen Sie Build-Logs auf Fehler

## 4. Network/Firewall-Probleme

### Debugging mit Browser Dev Tools:
1. **Network Tab öffnen**
2. **API-Requests verfolgen**
3. **Response Status und Headers prüfen**

### Häufige Status Codes:
- `200`: Erfolgreich
- `404`: Endpoint nicht gefunden
- `500`: Backend-Fehler
- `502/503`: Service nicht verfügbar
- `0` oder keine Response: CORS oder Network-Problem

## 5. Schnelle Debugging-Schritte

1. **API-URL in Browser testen:**
   ```
   https://kick-predictor-backend.onrender.com/health
   ```

2. **Frontend-Konsole prüfen:**
   - F12 → Console Tab
   - Nach Log-Meldungen und Fehlern suchen

3. **Network Tab prüfen:**
   - F12 → Network Tab
   - Seite neu laden und API-Requests beobachten

4. **CORS Test:**
   ```javascript
   // In Browser-Konsole ausführen:
   fetch('https://kick-predictor-backend.onrender.com/health')
     .then(r => r.json())
     .then(console.log)
     .catch(console.error)
   ```

## 6. Produktions-Fallbacks

Wenn weiterhin Probleme auftreten, können Sie diese temporären Lösungen verwenden:

1. **Hardcoded API-URL:** Temporär die Backend-URL direkt im Code setzen
2. **Proxy-Service:** Einen Proxy zwischen Frontend und Backend einrichten
3. **Same-Domain Deployment:** Frontend und Backend auf derselben Domain hosten