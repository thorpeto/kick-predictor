# Kick Predictor Frontend

Dieses Frontend bietet eine Benutzeroberfläche für die Anzeige von Bundesliga-Spielvorhersagen basierend auf historischen Daten und Formkurven.

## Technologien

- React: UI-Bibliothek
- TypeScript: Typsicheres JavaScript
- Tailwind CSS: Utility-First CSS-Framework
- Chart.js: Für Datenvisualisierungen
- Vite: Moderner Build-Tool und Entwicklungsserver

## Installation

1. Node.js (>= 16) installieren
2. Abhängigkeiten installieren:
   ```bash
   npm install
   ```

## Entwicklung

1. Entwicklungsserver starten:
   ```bash
   npm run dev
   ```
2. Frontend aufrufen unter http://localhost:3000

## Build

Produktionsbereit bauen:
```bash
npm run build
```

Vorschau des Builds:
```bash
npm run preview
```

## Docker

Container bauen:
```bash
docker build -t kick-predictor-frontend .
```

Container starten:
```bash
docker run -p 80:80 kick-predictor-frontend
```
