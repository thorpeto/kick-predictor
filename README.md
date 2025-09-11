# Kick Predictor

Eine Webapplikation zur Vorhersage von Bundesliga-Spielergebnissen basierend auf Daten der letzten 6 Wochen, Formkurven und Expected Goals.

## Überblick

Kick Predictor analysiert historische Bundesliga-Daten, berechnet Formkurven und prognostiziert mithilfe eines datenbasierten Modells die wahrscheinlichsten Ergebnisse für kommende Spieltage. Dabei werden verschiedene Faktoren berücksichtigt:

- Erzielte Tore und Gegentore
- Expected Goals (xG)
- Heimvorteil
- Historische Begegnungen

## Projektstruktur

Das Projekt besteht aus zwei Hauptkomponenten:

### Backend (Python/FastAPI)

- API für Spielergebnisse und Vorhersagen
- Datenerfassung und -verarbeitung
- Vorhersagemodell

### Frontend (React/Tailwind CSS)

- Benutzerfreundliche Oberfläche
- Anzeige von Vorhersagen und Formkurven
- Datenvisualisierung mit Chart.js

## Installation und Entwicklung

### Voraussetzungen

- Python 3.8+
- Node.js 16+
- Docker (optional)

### Backend starten

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend starten

```bash
cd frontend
npm install
npm run dev
```

### Mit Docker

Das gesamte Projekt kann einfach mit Docker Compose gestartet werden:

```bash
docker-compose up
```

## API-Endpunkte

- GET `/api/next-matchday`: Nächste Spieltags-Daten
- GET `/api/predictions/{matchday}`: Vorhersagen für einen bestimmten Spieltag
- GET `/api/team/{team_id}/form`: Formberechnung für ein Team

## Weiterentwicklung

Das Projekt kann in folgenden Bereichen erweitert werden:

1. Integration weiterer Datenquellen (z.B. API für Live-Daten)
2. Verbesserung des Vorhersagemodells mit Machine Learning
3. Erweiterung der Benutzeroberfläche um weitere Visualisierungen
4. Implementierung von Benutzerkonten zum Speichern von Vorhersagen