#!/bin/bash

# Deployment Script für Kick Predictor Backend
# 
# Usage: ./deploy.sh [PROJECT_ID] [REGION]
# 
# Beispiel: ./deploy.sh my-project-123 europe-west1

set -e

# Standardwerte
PROJECT_ID=${1:-"kick-predictor-project"}
REGION=${2:-"europe-west1"}
SERVICE_NAME="kick-predictor-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Kick Predictor Backend to Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Image: ${IMAGE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "📋 Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the container image
echo "🏗️ Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars DATABASE_PATH=/app/kick_predictor_final.db

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "✅ Deployment completed!"
echo "🌐 Backend URL: ${SERVICE_URL}"
echo ""
echo "🧪 Test endpoints:"
echo "  Health: ${SERVICE_URL}/health"
echo "  API Status: ${SERVICE_URL}/"
echo "  Next Matchday: ${SERVICE_URL}/api/next-matchday-info"
echo ""
echo "📝 Next steps:"
echo "1. Update your frontend to use this backend URL"
echo "2. Test the Update page: ${SERVICE_URL}/api/update-data"
echo "3. Configure auto-updater: ${SERVICE_URL}/api/auto-updater/start"