# Supabase Setup Guide für Kick-Predictor

## 1. Supabase Account erstellen

1. Gehe zu [supabase.com](https://supabase.com)
2. Klicke auf "Start your project"
3. Melde dich mit GitHub an (empfohlen)
4. Akzeptiere die Terms of Service

## 2. Neues Projekt erstellen

1. Klicke auf "New Project"
2. Wähle eine Organisation (falls noch keine vorhanden, wird automatisch erstellt)
3. Projekt Details:
   - **Project Name**: `kick-predictor`
   - **Database Password**: Erstelle ein starkes Passwort (wird für PostgreSQL benötigt)
   - **Region**: `Europe (Frankfurt)` (für bessere Performance in Deutschland)
   - **Pricing Plan**: `Free` (bis zu 500MB Storage)

4. Klicke auf "Create new project"
5. Warte 2-3 Minuten bis das Projekt erstellt ist

## 3. Database Connection String holen

1. In deinem neuen Projekt gehe zu **Settings** (linke Seitenleiste)
2. Klicke auf **Database**
3. Scrolle runter zu **Connection string**
4. Wähle **URI** aus dem Dropdown
5. Kopiere die Connection String - sie sieht so aus:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

## 4. Environment Variable setzen

### Für lokale Entwicklung:
Erstelle eine `.env` Datei im `backend/` Verzeichnis:
```bash
# Supabase PostgreSQL Connection
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Optional: Für Development Logging
ENVIRONMENT=development
```

### Für Render Deployment:
1. Gehe zu deinem Render Service Dashboard
2. Gehe zu **Environment** Tab
3. Füge neue Environment Variable hinzu:
   - **Key**: `DATABASE_URL`
   - **Value**: `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres`

## 5. Deployment testen

Nach dem Setup solltest du:
1. Lokale Tests durchführen
2. Neue Version auf Render deployen
3. Überprüfen dass die API funktioniert
4. Datenbank-Sync testen

## 6. Vorteile von Supabase

✅ **500MB kostenloses Storage**  
✅ **Persistent Storage** (keine Datenverluste)  
✅ **Automatische Backups**  
✅ **PostgreSQL** (robuster als SQLite)  
✅ **SSL-verschlüsselte Verbindungen**  
✅ **Dashboard für Datenbank-Management**  
✅ **API-Performance Monitoring**  

## 7. Nächste Schritte

1. Kopiere die Database URL aus Supabase
2. Setze die Environment Variable (lokal und auf Render)
3. Starte die Anwendung neu
4. Checke die Logs für erfolgreiche PostgreSQL Verbindung

## Troubleshooting

**Connection Failed?**
- Überprüfe das Passwort in der DATABASE_URL
- Stelle sicher, dass die Project Reference korrekt ist
- Checke ob SSL aktiviert ist (sollte automatisch sein)

**Slow Performance?**
- Supabase Free Tier hat Limits, aber sollte für deine App ausreichen
- Bei zu vielen Requests kannst du später upgraden

**Need Help?**
- Supabase Docs: https://supabase.com/docs
- Ihr Dashboard zeigt Logs und Performance Metrics