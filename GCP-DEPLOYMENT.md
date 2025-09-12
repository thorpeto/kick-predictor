# GCP Deployment - Schritt für Schritt Anleitung

Diese Anleitung beschreibt die notwendigen Schritte, um die Kick Predictor App auf Google Cloud Platform (GCP) zu deployen.

## Voraussetzungen

1. Ein Google Cloud Platform Konto
2. Ein GCP Projekt (erstellen Sie ein neues, wenn nötig)
3. Aktivierte Abrechnung für das GCP Projekt
4. Installation der Google Cloud SDK (`gcloud`) auf Ihrem lokalen System
5. Installation von Terraform (für die Infrastructure-as-Code Option)

## 1. GitHub Repository Secrets einrichten

Für die CI/CD-Pipeline mit GitHub Actions benötigen Sie die folgenden Repository Secrets:

1. `GCP_PROJECT_ID`: Ihre Google Cloud Projekt-ID
2. `GCP_SA_KEY`: Der Base64-codierte Inhalt des Service Account Keys (JSON)
3. `ALLOWED_ORIGINS`: Komma-getrennte Liste der erlaubten Ursprünge für CORS

So erstellen Sie den Service Account und den Key:

```bash
# Service Account erstellen
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"

# Service Account Berechtigungen zuweisen
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Service Account Key erstellen
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Base64-codieren (für GitHub Secrets)
cat key.json | base64
```

## 2. GCP APIs aktivieren

Aktivieren Sie die notwendigen Google Cloud APIs:

```bash
gcloud services enable cloudrun.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## 3. Secrets für die Anwendung einrichten

Führen Sie das bereitgestellte Skript aus, um die benötigten Secrets in Secret Manager zu erstellen:

```bash
bash scripts/setup-secrets.sh
```

## 4. Manuelle Deployment-Option mit Terraform

Wenn Sie ein manuelles Deployment bevorzugen, können Sie Terraform verwenden:

```bash
cd terraform

# Kopieren Sie die Beispiel-Variablendatei und passen Sie sie an
cp terraform.tfvars.example terraform.tfvars
# Editieren Sie die Datei terraform.tfvars mit Ihren Projektwerten

# Terraform initialisieren und ausführen
terraform init
terraform plan  # Überprüfen Sie den Plan
terraform apply  # Führen Sie das Deployment aus
```

## 5. Automatisches Deployment mit GitHub Actions

Für das automatische Deployment mit GitHub Actions:

1. Pushen Sie Ihren Code ins GitHub-Repository
2. Der Workflow wird automatisch bei Pushes in den `main`-Branch ausgeführt
3. Sie können den Workflow auch manuell in der GitHub Actions-Oberfläche auslösen

## 6. Überprüfen des Deployments

Nach dem Deployment können Sie die URLs der bereitgestellten Dienste überprüfen:

```bash
# Für Backend
gcloud run services describe kick-predictor-backend --region=europe-west3 --format='value(status.url)'

# Für Frontend
gcloud run services describe kick-predictor-frontend --region=europe-west3 --format='value(status.url)'
```

## 7. Monitoring und Logging

Sie können die Logs und Metriken Ihrer Anwendung im GCP Console überwachen:

- Cloud Run Dienste: https://console.cloud.google.com/run
- Logs: https://console.cloud.google.com/logs
- Monitoring: https://console.cloud.google.com/monitoring

## 8. Fehlerbehebung

Bei Problemen können Sie die folgenden Schritte ausprobieren:

1. Überprüfen Sie die Cloud Run Logs für Backend und Frontend
2. Überprüfen Sie die GitHub Actions Workflow-Logs
3. Stellen Sie sicher, dass alle benötigten APIs aktiviert sind
4. Überprüfen Sie die Service Account-Berechtigungen