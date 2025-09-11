# Kick Predictor Backend

Dieses Backend bietet eine API zur Vorhersage von Bundesliga-Spielergebnissen basierend auf historischen Daten und Formkurven.

## Technologien

- FastAPI: Modernes Python-Web-Framework
- Pandas & NumPy: Datenverarbeitung und -analyse
- scikit-learn: Machine Learning für die Vorhersagemodelle

## Installation

1. Python 3.8+ installieren
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. .env-Datei mit benötigten Umgebungsvariablen erstellen (siehe .env.example)

## Entwicklung

1. Server mit Hot-Reloading starten:
   ```bash
   uvicorn main:app --reload
   ```
2. API-Dokumentation unter http://localhost:8000/docs aufrufen

## API-Endpunkte

- GET `/`: Willkommensnachricht
- GET `/health`: Health-Check
- GET `/api/next-matchday`: Nächste Spieltags-Daten
- GET `/api/predictions/{matchday}`: Vorhersagen für einen Spieltag
- GET `/api/team/{team_id}/form`: Formberechnung für ein Team

## Docker

Container bauen:
```bash
docker build -t kick-predictor-backend .
```

Container starten:
```bash
docker run -p 8000:8000 --env-file .env kick-predictor-backend
```
