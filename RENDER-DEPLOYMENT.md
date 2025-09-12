# Deployment auf Render.com

Diese Anleitung beschreibt, wie Sie die Kick Predictor App auf [Render.com](https://render.com) deployen können.

## Voraussetzungen

1. Ein Render.com-Konto (kostenlos für Basisfunktionen)
2. Ein GitHub-Repository mit dem Projektcode

## Option 1: Manuelles Setup

### Backend-Deployment

1. Melden Sie sich bei Render.com an
2. Klicken Sie auf "New +" und wählen Sie "Web Service"
3. Verbinden Sie Ihr GitHub-Repository oder verwenden Sie die public URL
4. Konfigurieren Sie den Service:
   - **Name**: `kick-predictor-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Plan**: Wählen Sie den entsprechenden Plan (z.B. Free)

5. Fügen Sie die Umgebungsvariablen hinzu:
   - `ENVIRONMENT`: `production`
   - `ALLOWED_ORIGINS`: `https://kick-predictor-frontend.onrender.com`
   - `PORT`: `10000`

6. Klicken Sie auf "Create Web Service"

### Frontend-Deployment

1. Klicken Sie erneut auf "New +" und wählen Sie "Web Service"
2. Verbinden Sie dasselbe GitHub-Repository
3. Konfigurieren Sie den Service:
   - **Name**: `kick-predictor-frontend`
   - **Root Directory**: `frontend`
   - **Environment**: `Node`
   - **Build Command**: `npm ci && npm run build`
   - **Start Command**: `npx serve -s dist -l $PORT`
   - **Plan**: Wählen Sie den entsprechenden Plan (z.B. Free)

4. Fügen Sie die Umgebungsvariablen hinzu:
   - `NODE_ENV`: `production`
   - `VITE_API_URL`: `https://kick-predictor-backend.onrender.com` (ersetzen Sie dies mit der tatsächlichen URL Ihres Backend-Services)

5. Klicken Sie auf "Create Web Service"

## Option 2: Blueprint-Deployment (empfohlen)

Die `render.yaml`-Datei im Root-Verzeichnis des Projekts ermöglicht ein automatisiertes Deployment über Render Blueprints.

1. Pushen Sie den Code mit der `render.yaml`-Datei in Ihr GitHub-Repository
2. Gehen Sie zu Render.com und klicken Sie auf "New +"
3. Wählen Sie "Blueprint"
4. Verbinden Sie Ihr GitHub-Repository
5. Render erkennt automatisch die `render.yaml`-Datei und zeigt die zu erstellenden Services an
6. Überprüfen Sie die Konfiguration und klicken Sie auf "Apply"
7. Render erstellt nun beide Services mit den in der YAML-Datei angegebenen Konfigurationen

## Hinweise für das Deployment

### Kostenlose Instanzen auf Render

Beachten Sie, dass kostenlose Instanzen auf Render nach 15 Minuten Inaktivität in den Ruhezustand versetzt werden. Dies führt dazu, dass der erste Aufruf nach einer Inaktivitätsphase langsamer sein kann, da die Instanz erst wieder gestartet werden muss.

### CORS-Konfiguration

Die CORS-Einstellungen im Backend sind so konfiguriert, dass sie Anfragen von der Frontend-Domain akzeptieren. Wenn Sie andere Domains verwenden, müssen Sie die `ALLOWED_ORIGINS`-Umgebungsvariable entsprechend anpassen.

### Umgebungsvariablen

Für zusätzliche Sicherheit können Sie sensible Umgebungsvariablen (z.B. API-Schlüssel) direkt in der Render-Benutzeroberfläche konfigurieren, anstatt sie in den Dateien zu speichern.

## Überprüfen des Deployments

Nach dem erfolgreichen Deployment können Sie auf Ihre Anwendung über die von Render bereitgestellten URLs zugreifen:

- Frontend: `https://kick-predictor-frontend.onrender.com`
- Backend: `https://kick-predictor-backend.onrender.com`

## Fehlerbehebung

Bei Problemen mit dem Deployment:

1. Überprüfen Sie die Logs in der Render-Benutzeroberfläche
2. Stellen Sie sicher, dass alle erforderlichen Umgebungsvariablen korrekt gesetzt sind
3. Überprüfen Sie, ob die `build.sh`-Skripte ausführbar sind (`chmod +x build.sh`)
4. Prüfen Sie die CORS-Konfiguration, wenn Frontend-Backend-Kommunikationsprobleme auftreten