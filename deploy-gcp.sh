#!/bin/bash

# GCP Deployment Script für Kick-Predictor
# Verwendung: ./deploy-gcp.sh YOUR_PROJECT_ID

if [ $# -eq 0 ]; then
    echo "❌ Fehler: Projekt-ID erforderlich"
    echo "Verwendung: ./deploy-gcp.sh YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_ID=$1
REGION="europe-west1"

echo "🚀 Deploying Kick-Predictor to GCP..."
echo "📋 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo ""

# Projekt und Services konfigurieren
echo "⚙️  Configuring GCP project..."
gcloud config set project $PROJECT_ID
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com

# Backend deployen
echo ""
echo "📦 Building and deploying backend..."
cd backend

# Produktions-Dockerfile erstellen
cat > Dockerfile.prod << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn for production
RUN pip install gunicorn

# Copy application code
COPY . .

# Ensure database exists and is populated
RUN python -c "
import os
from real_data_sync import sync_real_data
if not os.path.exists('kick_predictor_final.db'):
    print('Initializing database...')
    sync_real_data()
    print('Database initialized.')
else:
    print('Database already exists.')
"

# Environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE 8080

# Production server with gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 300 main_real_data:app
EOF

# Backend Image bauen und deployen
docker build -f Dockerfile.prod -t gcr.io/$PROJECT_ID/kick-predictor-backend .
docker push gcr.io/$PROJECT_ID/kick-predictor-backend

gcloud run deploy kick-predictor-backend \
  --image gcr.io/$PROJECT_ID/kick-predictor-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --concurrency 80

# Backend URL abrufen
BACKEND_URL=$(gcloud run services describe kick-predictor-backend --region=$REGION --format="value(status.url)")

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Fehler: Backend URL konnte nicht abgerufen werden"
    exit 1
fi

echo "✅ Backend deployed: $BACKEND_URL"

# Frontend deployen
echo ""
echo "📦 Building and deploying frontend..."
cd ../frontend

# Environment für Production setzen
echo "VITE_API_URL=$BACKEND_URL" > .env.production

# Produktions-Dockerfile erstellen
cat > Dockerfile.prod << 'EOF'
# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

# Nginx Produktions-Konfiguration erstellen
cat > nginx.prod.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Main location
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Frontend Image bauen und deployen
docker build -f Dockerfile.prod -t gcr.io/$PROJECT_ID/kick-predictor-frontend .
docker push gcr.io/$PROJECT_ID/kick-predictor-frontend

gcloud run deploy kick-predictor-frontend \
  --image gcr.io/$PROJECT_ID/kick-predictor-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --concurrency 100

# Frontend URL abrufen
FRONTEND_URL=$(gcloud run services describe kick-predictor-frontend --region=$REGION --format="value(status.url)")

if [ -z "$FRONTEND_URL" ]; then
    echo "❌ Fehler: Frontend URL konnte nicht abgerufen werden"
    exit 1
fi

echo "✅ Frontend deployed: $FRONTEND_URL"

# Deployment Summary
echo ""
echo "🎉 Deployment erfolgreich abgeschlossen!"
echo "=================================="
echo "🖥️  Backend:  $BACKEND_URL"
echo "🌐 Frontend: $FRONTEND_URL"
echo ""
echo "📊 Nützliche Commands:"
echo "# Logs anzeigen:"
echo "gcloud logs read \"resource.type=cloud_run_revision AND resource.labels.service_name=kick-predictor-backend\" --limit 50"
echo ""
echo "# Services verwalten:"
echo "gcloud run services list --region=$REGION"
echo ""
echo "# Kosten überwachen:"
echo "gcloud billing budgets list"
echo ""
echo "🚀 Ihre Kick-Predictor App ist jetzt live unter: $FRONTEND_URL"