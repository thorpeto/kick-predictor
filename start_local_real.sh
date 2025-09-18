#!/bin/bash

# Lokaler Development Server mit echten Daten (GCP-Standard)
echo "🚀 Starte Kick Predictor Backend (Lokale Entwicklung - GCP Standard)"
echo "📊 Backend: main_real_data.py (echte Bundesliga-Daten)"
echo "🗄️  Datenbank: kick_predictor_final.db"
echo "🤖 Auto-Updater: Aktiviert (täglich 17:30, 20:30, 22:30)"
echo ""

cd backend

# Environment check
if [ ! -f "kick_predictor_final.db" ]; then
    echo "❌ Datenbank nicht gefunden!"
    echo "💡 Führe zuerst die Synchronisation aus:"
    echo "   python sync_local_to_gcp.py"
    exit 1
fi

# Check if teams are populated
TEAM_COUNT=$(sqlite3 kick_predictor_final.db "SELECT COUNT(*) FROM teams_real;")
if [ "$TEAM_COUNT" -lt 18 ]; then
    echo "⚠️  Datenbank unvollständig (nur $TEAM_COUNT Teams)"
    echo "💡 Führe zuerst die Synchronisation aus:"
    echo "   python sync_local_to_gcp.py"
    exit 1
fi

echo "✅ Datenbank vollständig ($TEAM_COUNT Teams)"
echo "🌐 Server startet auf http://localhost:8000"
echo "📋 API-Dokumentation: http://localhost:8000/docs"
echo ""

# Start server
/workspaces/kick-predictor/.venv/bin/python -m uvicorn main_real_data:app --host 0.0.0.0 --port 8000 --reload
