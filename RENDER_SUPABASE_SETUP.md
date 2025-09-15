# Render Deployment mit Supabase - Quick Setup

## Variante 1: Render Dashboard (Empfohlen)

### Schritt 1: Render Dashboard öffnen
1. Gehe zu https://dashboard.render.com
2. Wähle deinen `kick-predictor-backend` Service
3. Klicke auf **"Environment"** Tab

### Schritt 2: DATABASE_URL hinzufügen/bearbeiten
1. Suche nach der `DATABASE_URL` Variable (falls vorhanden) oder klicke **"Add Environment Variable"**
2. **Key**: `DATABASE_URL`
3. **Value**: Deine Supabase Connection String:
   ```
   postgresql://postgres:[DEIN-PASSWORT]@db.[PROJEKT-REF].supabase.co:5432/postgres
   ```
4. Klicke **"Save Changes"**

### Schritt 3: Auto-Deploy
Render wird automatisch neu deployen sobald du die Environment Variable gespeichert hast.

---

## Variante 2: Git Push mit render.yaml

### Option A: render.yaml direkt bearbeiten
1. Öffne `render.yaml` in diesem Repository
2. Ersetze in Zeile 16 die Platzhalter:
   ```yaml
   - key: DATABASE_URL
     value: postgresql://postgres:[DEIN-PASSWORT]@db.[PROJEKT-REF].supabase.co:5432/postgres
   ```
3. Committe und pushe die Änderung

### Option B: Environment Variable in Render Dashboard (sicherer)
- Lass die render.yaml wie sie ist
- Setze DATABASE_URL nur im Dashboard (überschreibt render.yaml)

---

## Was passiert nach dem Deployment?

✅ **Automatische PostgreSQL Verbindung**  
✅ **Tabellen werden automatisch erstellt**  
✅ **Auto-Sync läuft weiterhin**  
✅ **Persistente Datenbank** (keine Datenverluste mehr!)  
✅ **Bessere Performance** als SQLite  

## Logs checken

Nach dem Deployment check die Logs in Render:
1. Service auswählen
2. **"Logs"** Tab
3. Schaue nach: `"Enhanced database initialization successful"`
4. Schaue nach: `"Database initialized successfully (postgresql)"`

## Troubleshooting

**Connection Failed?**
- Überprüfe DATABASE_URL Schreibweise
- Stelle sicher, dass das Passwort korrekt ist
- Checke Projekt-Referenz in der URL

**Need Help?**
Die Enhanced Database Config hat Fallback zu SQLite wenn PostgreSQL fehlschlägt.