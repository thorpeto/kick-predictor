#!/bin/bash

# Skript zum Erstellen von Secret Manager Secrets für die Anwendung
# Führen Sie dieses Skript mit der GCP CLI aus, nachdem Sie sich authentifiziert haben

# Überprüfen, ob gcloud installiert ist
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud ist nicht installiert. Bitte installieren Sie die Google Cloud SDK."
    exit 1
fi

# Projekt-ID festlegen
read -p "Bitte geben Sie Ihre GCP Projekt-ID ein: " PROJECT_ID

# Prüfen, ob Secret Manager API aktiviert ist
gcloud services enable secretmanager.googleapis.com --project $PROJECT_ID

# Backend-Secrets erstellen
echo "Erstelle Secrets für das Backend..."

# Beispiel für ein Secret - ersetzen Sie mit Ihren tatsächlichen Secrets
read -s -p "Bitte geben Sie das API-Secret ein (wird nicht angezeigt): " API_SECRET
echo

# Secret erstellen
echo -n "$API_SECRET" | gcloud secrets create kick-predictor-api-secret \
    --replication-policy="automatic" \
    --data-file=- \
    --project=$PROJECT_ID

echo "Secret 'kick-predictor-api-secret' wurde erstellt."

# Secret-Zugriff für Cloud Run konfigurieren
SERVICE_ACCOUNT="$(gcloud iam service-accounts list --filter="displayName:Cloud Run Service Agent" --format='value(email)' --project=$PROJECT_ID)"

gcloud secrets add-iam-policy-binding kick-predictor-api-secret \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo "IAM-Bindung für Cloud Run Service Agent hinzugefügt."

echo "Secret-Setup abgeschlossen."