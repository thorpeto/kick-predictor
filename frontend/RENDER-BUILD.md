# Frontend-Build auf Render.com

Diese Datei erklärt, wie der Frontend-Build auf Render.com konfiguriert ist und wie potenzielle Probleme behoben werden können.

## Build-Konfiguration

Der Build auf Render.com wird mit den folgenden Schritten durchgeführt:

1. Node.js-Version: `18.17.1` (LTS, unterstützt bis April 2025)
2. Build-Befehl: `NODE_ENV=development npm install && npm run build`
   - `NODE_ENV=development` stellt sicher, dass alle Abhängigkeiten installiert werden
   - `npm install` installiert alle Abhängigkeiten
   - `npm run build` führt den Vite-Build-Prozess aus
3. Start-Befehl: `npx serve -s dist -l $PORT`
   - Startet einen statischen Webserver für die gebauten Dateien

## Wichtige Abhängigkeiten

In der `package.json` sind alle Build-Abhängigkeiten in `dependencies` (nicht in `devDependencies`) aufgeführt:

- `vite`: Build-Tool
- `@vitejs/plugin-react`: React-Plugin für Vite
- `typescript`: TypeScript-Compiler
- `autoprefixer`, `postcss`, `tailwindcss`: CSS-Verarbeitung
- `serve`: Statischer Webserver für die gebauten Dateien

## Häufige Probleme und Lösungen

### "vite: not found" oder ähnliche Fehler

**Problem:** Build-Tools werden nicht gefunden.

**Ursache:** In Produktionsumgebungen werden standardmäßig nur `dependencies` installiert, nicht `devDependencies`.

**Lösungen:**
1. Verschieben Sie alle für den Build benötigten Pakete von `devDependencies` nach `dependencies`
2. Oder setzen Sie `NODE_ENV=development` beim Build-Befehl

### Node.js-Version veraltet

**Problem:** Die Node.js-Version hat das End-of-Life erreicht.

**Lösungen:**
1. Aktualisieren Sie die `.node-version`-Datei auf eine unterstützte Version
2. Oder setzen Sie die `NODE_VERSION`-Umgebungsvariable in der Render-Konfiguration

### Fehlende Umgebungsvariablen

**Problem:** Frontend kann nicht auf das Backend zugreifen.

**Lösung:** Stellen Sie sicher, dass `VITE_API_URL` korrekt gesetzt ist und auf die Backend-URL zeigt

## Manuelles Testen des Builds

Um den Build-Prozess lokal zu testen:

```bash
cd frontend
NODE_ENV=development npm install
npm run build
npx serve -s dist -l 3000
```

Öffnen Sie http://localhost:3000 im Browser, um die gebaute Anwendung zu testen.