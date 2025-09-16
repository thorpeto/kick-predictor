# GCP Deployment Guide für Kick-Predictor

## Option 1: Cloud Run (Empfohlen)

### Voraussetzungen
```bash
# Google Cloud SDK installieren
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Anmelden und Projekt konfigurieren
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Container Registry aktivieren
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
```

### Backend auf Cloud Run deployen

1. **Dockerfile für Produktion optimieren:**
```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App Code kopieren
COPY . .

# Datenbank initialisieren (falls nötig)
RUN python -c "from real_data_sync import sync_real_data; sync_real_data()"

# Port für Cloud Run
ENV PORT=8080
EXPOSE 8080

# Produktions-Server mit Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "main_real_data:app"]
```

2. **Backend Image bauen und pushen:**
```bash
cd backend

# Image bauen
docker build -f Dockerfile.prod -t gcr.io/YOUR_PROJECT_ID/kick-predictor-backend .

# Image zu Container Registry pushen
docker push gcr.io/YOUR_PROJECT_ID/kick-predictor-backend

# Auf Cloud Run deployen
gcloud run deploy kick-predictor-backend \
  --image gcr.io/YOUR_PROJECT_ID/kick-predictor-backend \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

### Frontend auf Cloud Run deployen

1. **Frontend für Produktion bauen:**
```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
ENV VITE_API_URL=https://YOUR_BACKEND_URL
RUN npm run build

# Production server
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

2. **Nginx Konfiguration:**
```nginx
# frontend/nginx.prod.conf
server {
    listen 80;
    server_name _;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # API Proxy (optional)
    location /api/ {
        proxy_pass https://YOUR_BACKEND_URL/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Frontend deployen:**
```bash
cd frontend

# Image bauen
docker build -f Dockerfile.prod -t gcr.io/YOUR_PROJECT_ID/kick-predictor-frontend .

# Image pushen
docker push gcr.io/YOUR_PROJECT_ID/kick-predictor-frontend

# Auf Cloud Run deployen
gcloud run deploy kick-predictor-frontend \
  --image gcr.io/YOUR_PROJECT_ID/kick-predictor-frontend \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

## Option 2: App Engine

### Backend auf App Engine
```yaml
# backend/app.yaml
runtime: python311

env_variables:
  PORT: 8080

automatic_scaling:
  min_instances: 0
  max_instances: 10

resources:
  cpu: 1
  memory_gb: 1
  disk_size_gb: 10
```

### Frontend auf App Engine
```yaml
# frontend/app.yaml
runtime: nodejs18

env_variables:
  VITE_API_URL: https://YOUR_BACKEND_URL

automatic_scaling:
  min_instances: 0
  max_instances: 5
```

```bash
# Backend deployen
cd backend
gcloud app deploy

# Frontend deployen
cd frontend
gcloud app deploy
```

## Option 3: Google Kubernetes Engine (GKE)

### Kubernetes Manifests
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kick-predictor-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kick-predictor-backend
  template:
    metadata:
      labels:
        app: kick-predictor-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/YOUR_PROJECT_ID/kick-predictor-backend
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: kick-predictor-backend-service
spec:
  selector:
    app: kick-predictor-backend
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

## Datenbank-Optionen

### 1. Cloud SQL (Managed Database)
```bash
# PostgreSQL Instanz erstellen
gcloud sql instances create kick-predictor-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=europe-west1

# Datenbank erstellen
gcloud sql databases create kickpredictor --instance=kick-predictor-db
```

### 2. Cloud Storage für SQLite (einfacher)
```python
# backend/storage_utils.py
from google.cloud import storage

def sync_db_to_cloud_storage():
    """SQLite DB zu Cloud Storage hochladen"""
    client = storage.Client()
    bucket = client.bucket('YOUR_BUCKET_NAME')
    blob = bucket.blob('kick_predictor_final.db')
    blob.upload_from_filename('kick_predictor_final.db')

def download_db_from_cloud_storage():
    """SQLite DB von Cloud Storage herunterladen"""
    client = storage.Client()
    bucket = client.bucket('YOUR_BUCKET_NAME')
    blob = bucket.blob('kick_predictor_final.db')
    blob.download_to_filename('kick_predictor_final.db')
```

## Deployment-Script

```bash
#!/bin/bash
# deploy.sh

PROJECT_ID="your-gcp-project-id"
REGION="europe-west1"

echo "🚀 Deploying Kick-Predictor to GCP..."

# Backend deployen
echo "📦 Building and deploying backend..."
cd backend
docker build -f Dockerfile.prod -t gcr.io/$PROJECT_ID/kick-predictor-backend .
docker push gcr.io/$PROJECT_ID/kick-predictor-backend

gcloud run deploy kick-predictor-backend \
  --image gcr.io/$PROJECT_ID/kick-predictor-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300

# Backend URL abrufen
BACKEND_URL=$(gcloud run services describe kick-predictor-backend --region=$REGION --format="value(status.url)")

echo "✅ Backend deployed: $BACKEND_URL"

# Frontend deployen
echo "📦 Building and deploying frontend..."
cd ../frontend

# Backend URL in .env setzen
echo "VITE_API_URL=$BACKEND_URL" > .env.production

docker build -f Dockerfile.prod -t gcr.io/$PROJECT_ID/kick-predictor-frontend .
docker push gcr.io/$PROJECT_ID/kick-predictor-frontend

gcloud run deploy kick-predictor-frontend \
  --image gcr.io/$PROJECT_ID/kick-predictor-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi

# Frontend URL abrufen
FRONTEND_URL=$(gcloud run services describe kick-predictor-frontend --region=$REGION --format="value(status.url)")

echo "✅ Frontend deployed: $FRONTEND_URL"
echo "🎉 Deployment complete!"
echo "🌐 Access your app at: $FRONTEND_URL"
```

## Monitoring und Logging

```bash
# Cloud Monitoring aktivieren
gcloud services enable monitoring.googleapis.com

# Logs anzeigen
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=kick-predictor-backend" --limit 50
```

## Kosten-Optimierung

1. **Cloud Run**: Automatische Skalierung auf 0 Instanzen
2. **App Engine**: F1/F2 Instanzen für niedrigen Traffic
3. **Cloud Scheduler**: Für regelmäßige Updates
4. **Cloud Storage**: Günstiger als persistente Disks

## Empfehlung für Ihren Use Case

**Für Kick-Predictor empfehle ich Cloud Run**, weil:
- ✅ Einfaches Container-Deployment
- ✅ Automatische Skalierung (auch auf 0)
- ✅ Pay-per-use Pricing
- ✅ Einfache CI/CD Integration
- ✅ Perfekt für Ihre FastAPI + React Architektur

Die SQLite-Datenbank können Sie entweder auf Cloud Storage persistieren oder zu Cloud SQL migrieren für bessere Performance bei höherem Traffic.