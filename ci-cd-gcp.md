# CI/CD Pipeline für automatisches Deployment

## GitHub Actions Workflow

### .github/workflows/deploy-gcp.yml
```yaml
name: Deploy to Google Cloud Run

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: europe-west1

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Google Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}

    - name: Configure Docker
      run: gcloud auth configure-docker

    - name: Build and deploy backend
      run: |
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

    - name: Get backend URL
      id: backend
      run: |
        URL=$(gcloud run services describe kick-predictor-backend --region=$REGION --format="value(status.url)")
        echo "url=$URL" >> $GITHUB_OUTPUT

    - name: Build and deploy frontend
      run: |
        cd frontend
        echo "VITE_API_URL=${{ steps.backend.outputs.url }}" > .env.production
        
        docker build -f Dockerfile.prod -t gcr.io/$PROJECT_ID/kick-predictor-frontend .
        docker push gcr.io/$PROJECT_ID/kick-predictor-frontend
        
        gcloud run deploy kick-predictor-frontend \
          --image gcr.io/$PROJECT_ID/kick-predictor-frontend \
          --platform managed \
          --region $REGION \
          --allow-unauthenticated \
          --memory 512Mi

    - name: Get frontend URL
      id: frontend
      run: |
        URL=$(gcloud run services describe kick-predictor-frontend --region=$REGION --format="value(status.url)")
        echo "url=$URL" >> $GITHUB_OUTPUT

    - name: Deploy summary
      run: |
        echo "🎉 Deployment complete!"
        echo "Backend: ${{ steps.backend.outputs.url }}"
        echo "Frontend: ${{ steps.frontend.outputs.url }}"
```

## Benötigte Secrets in GitHub

1. **GCP_PROJECT_ID**: Ihre GCP Projekt-ID
2. **GCP_SA_KEY**: Service Account Key (JSON)

### Service Account erstellen:
```bash
# Service Account erstellen
gcloud iam service-accounts create github-actions \
  --description="Service Account für GitHub Actions" \
  --display-name="GitHub Actions"

# Erforderliche Rollen zuweisen
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Key generieren
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Cloud Build Alternative

### cloudbuild.yaml
```yaml
steps:
  # Backend bauen
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'backend/Dockerfile.prod', '-t', 'gcr.io/$PROJECT_ID/kick-predictor-backend', './backend']

  # Backend pushen
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/kick-predictor-backend']

  # Backend deployen
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args: 
      - 'run'
      - 'deploy'
      - 'kick-predictor-backend'
      - '--image=gcr.io/$PROJECT_ID/kick-predictor-backend'
      - '--region=europe-west1'
      - '--platform=managed'
      - '--allow-unauthenticated'

  # Frontend bauen und deployen
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'frontend/Dockerfile.prod', '-t', 'gcr.io/$PROJECT_ID/kick-predictor-frontend', './frontend']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/kick-predictor-frontend']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args: 
      - 'run'
      - 'deploy'
      - 'kick-predictor-frontend'
      - '--image=gcr.io/$PROJECT_ID/kick-predictor-frontend'
      - '--region=europe-west1'
      - '--platform=managed'
      - '--allow-unauthenticated'
```

### Trigger einrichten:
```bash
gcloud builds triggers create github \
  --repo-name=kick-predictor \
  --repo-owner=thorpeto \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```