#!/bin/bash

# Script zur Installation des Google Cloud SDK in diesem Dev Container

echo "🔧 Installiere Google Cloud SDK..."

# Download und Installation
curl https://sdk.cloud.google.com | bash

# Restart shell oder source
exec -l $SHELL

# Nach Neustart:
# gcloud init
# gcloud auth login
# gcloud config set project YOUR_PROJECT_ID

echo "✅ Installation abgeschlossen!"
echo "Führe aus: source ~/.bashrc"
echo "Dann: gcloud init"