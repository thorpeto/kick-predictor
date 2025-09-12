# Render Deployment Fehlerbehebung

Wenn Sie Probleme beim Deployment auf Render.com haben, folgen Sie dieser Anleitung zur Fehlerbehebung.

## Allgemeine Fehler

### Fehlercode 127 (Command not found)

Dieser Fehler tritt auf, wenn ein Befehl nicht gefunden werden kann, oft wegen Berechtigungsproblemen oder fehlenden Abhängigkeiten.

**Lösungen:**
1. Verwenden Sie direkte Befehle in der render.yaml statt Shell-Skripte:
   ```yaml
   buildCommand: pip install -r requirements.txt # anstatt ./build.sh
   ```

2. Falls Sie dennoch Skripte verwenden möchten, stellen Sie sicher, dass:
   - Die Skripte ausführbar sind (im lokalen Repository)
   - Die Skripte Unix-Zeilenenden haben (LF, nicht CRLF)
   - Die Skripte die korrekte Shebang-Zeile haben (`#!/bin/bash` oder `#!/usr/bin/env python`)

### Python-spezifische Probleme

1. **Pakete nicht gefunden:** Stellen Sie sicher, dass alle Abhängigkeiten in `requirements.txt` aufgeführt sind.
2. **Fehler mit dem Starten der Anwendung:** Überprüfen Sie, ob der PORT korrekt aus der Umgebungsvariable gelesen wird.

### Node.js-spezifische Probleme

1. **npm-Fehler mit package-lock.json:**
   - Fehler wie `Missing: serve@14.2.5 from lock file` weisen auf eine Diskrepanz zwischen package.json und package-lock.json hin
   - Verwenden Sie `npm install` statt `npm ci` im Build-Befehl, um die package-lock.json automatisch zu aktualisieren
   - Alternativ können Sie lokal `npm install` ausführen und die aktualisierte package-lock.json committen

2. **Serve-Fehler:** 
   - Stellen Sie sicher, dass `serve` in den Abhängigkeiten in `package.json` aufgeführt ist
   - Bei Bedarf installieren: `npm install serve --save`

3. **Fehlende Abhängigkeiten:**
   - Überprüfen Sie, ob alle benötigten Abhängigkeiten in `dependencies` (nicht nur in `devDependencies`) aufgeführt sind
   - Render setzt `NODE_ENV=production`, was dazu führt, dass devDependencies nicht installiert werden

## Render-Logs überprüfen

Die detailliertesten Informationen finden Sie in den Build- und Deployment-Logs auf der Render-Plattform:

1. Gehen Sie zu Ihrem Service auf Render.com
2. Klicken Sie auf den Tab "Logs"
3. Wählen Sie "Build Logs" oder "Runtime Logs"

## Lokales Testen

Bevor Sie erneut deployen, können Sie Ihre Build- und Start-Befehle lokal testen:

```bash
# Für das Backend
cd backend
pip install -r requirements.txt
python server.py

# Für das Frontend
cd frontend
npm ci
npm run build
npx serve -s dist -l 3000
```

## Weitere Schritte

Wenn die oben genannten Lösungen nicht funktionieren:

1. Überprüfen Sie die Render-Dokumentation für spezifische Einschränkungen des gewählten Plans
2. Vereinfachen Sie Ihre Anwendung für das erste Deployment und fügen Sie schrittweise Komplexität hinzu
3. Kontaktieren Sie den Render-Support, wenn weiterhin Probleme auftreten