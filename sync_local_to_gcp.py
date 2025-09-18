#!/usr/bin/env python3
"""
Synchronisation Script: Lokale Version auf GCP-Standard bringen
Dieses Script macht die lokale Entwicklungsumgebung identisch zur GCP-Version
"""
import os
import sys
import asyncio
import logging
import subprocess
import shutil
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Zeige Sync-Banner"""
    print("=" * 60)
    print("🚀 KICK PREDICTOR - LOKALE SYNCHRONISATION")
    print("   Lokale Version → GCP Production Standard")
    print("=" * 60)
    print()

async def sync_database():
    """Synchronisiere die Datenbank mit echten Daten"""
    logger.info("📊 Starte Datenbank-Synchronisation...")
    
    try:
        # Prüfe ob kick_predictor_final.db bereits Daten hat
        db_path = Path("backend/kick_predictor_final.db")
        
        if db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Prüfe Teams
            cursor.execute("SELECT COUNT(*) FROM teams_real")
            team_count = cursor.fetchone()[0]
            
            # Prüfe Matches
            cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2025'")
            match_count = cursor.fetchone()[0]
            
            conn.close()
            
            if team_count >= 18 and match_count > 0:
                logger.info(f"✅ Datenbank bereits synchron ({team_count} Teams, {match_count} Matches 2025)")
                return True
        
        # Führe Datensynchronisation durch
        logger.info("🔄 Lade echte Bundesliga-Daten...")
        
        # Verwende real_data_sync
        sys.path.append('backend')
        from real_data_sync import RealDataSync
        
        sync = RealDataSync()
        result = await sync.sync_all_real_data()
        
        logger.info("✅ Datenbank-Synchronisation erfolgreich!")
        logger.info(f"   Teams: {result.get('teams', 0)}")
        logger.info(f"   Matches 2025: {result.get('current_season_matches', 0)}")
        logger.info(f"   Matches 2024: {result.get('previous_season_matches', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Datenbank-Synchronisation: {e}")
        return False

def create_local_dev_scripts():
    """Erstelle lokale Entwicklungsscripts"""
    logger.info("📝 Erstelle lokale Entwicklungsscripts...")
    
    # Backend-Starter Script (echte Daten)
    backend_script = """#!/bin/bash

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
"""
    
    with open('start_local_real.sh', 'w') as f:
        f.write(backend_script)
    os.chmod('start_local_real.sh', 0o755)
    
    # Frontend-Starter Script (angepasste API-URL)
    frontend_script = """#!/bin/bash

# Frontend für lokale Entwicklung mit echtem Backend
echo "🎨 Starte Frontend (Lokale Entwicklung)"
echo "🔗 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo ""

cd frontend

# Check if backend is running
if ! curl -s http://localhost:8000/api/teams > /dev/null 2>&1; then
    echo "⚠️  Backend nicht erreichbar!"
    echo "💡 Starte zuerst das Backend:"
    echo "   ./start_local_real.sh"
    echo ""
    echo "❓ Trotzdem fortfahren? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment for local development
export VITE_API_URL=http://localhost:8000
echo "🔧 API URL: $VITE_API_URL"

# Start frontend
npm run dev
"""
    
    with open('start_local_frontend.sh', 'w') as f:
        f.write(frontend_script)
    os.chmod('start_local_frontend.sh', 0o755)
    
    logger.info("✅ Scripts erstellt:")
    logger.info("   - start_local_real.sh (Backend mit echten Daten)")
    logger.info("   - start_local_frontend.sh (Frontend für lokale Entwicklung)")

def update_frontend_config():
    """Update Frontend für lokale Entwicklung"""
    logger.info("⚙️  Prüfe Frontend-Konfiguration...")
    
    # Prüfe ob Frontend bereits konfiguriert ist
    vite_config = Path("frontend/vite.config.ts")
    if vite_config.exists():
        content = vite_config.read_text()
        if "localhost:8000" in content or "VITE_API_URL" in content:
            logger.info("✅ Frontend bereits für lokale Entwicklung konfiguriert")
            return
    
    # Info für manuielle Konfiguration
    logger.info("ℹ️  Frontend-Konfiguration:")
    logger.info("   Das Frontend verwendet bereits Umgebungsvariablen.")
    logger.info("   Für lokale Entwicklung verwende:")
    logger.info("   export VITE_API_URL=http://localhost:8000")
    logger.info("   (Wird automatisch in start_local_frontend.sh gesetzt)")

async def main():
    """Haupt-Synchronisationsfunktion"""
    print_banner()
    
    logger.info("🔍 Prüfe aktuelle Umgebung...")
    
    # Prüfe ob wir im richtigen Verzeichnis sind
    if not Path("backend").exists() or not Path("frontend").exists():
        logger.error("❌ Falsches Verzeichnis! Führe das Script im Projekt-Root aus.")
        sys.exit(1)
    
    # Prüfe Python-Umgebung
    if not Path(".venv").exists():
        logger.error("❌ Python Virtual Environment nicht gefunden!")
        logger.error("   Erstelle zuerst eine venv und installiere requirements.txt")
        sys.exit(1)
    
    logger.info("✅ Umgebung OK")
    
    # 1. Datenbank synchronisieren
    if not await sync_database():
        logger.error("❌ Datenbank-Synchronisation fehlgeschlagen")
        sys.exit(1)
    
    # 2. Scripts erstellen
    create_local_dev_scripts()
    
    # 3. Frontend konfigurieren
    update_frontend_config()
    
    print()
    logger.info("🎉 Lokale Synchronisation abgeschlossen!")
    print()
    print("=" * 60)
    print("✅ LOKALE ENTWICKLUNG BEREIT")
    print("=" * 60)
    print()
    print("🚀 Nächste Schritte:")
    print("   1. Backend starten:  ./start_local_real.sh")
    print("   2. Frontend starten: ./start_local_frontend.sh")
    print()
    print("🌐 URLs:")
    print("   - Backend API:       http://localhost:8000")
    print("   - API Dokumentation: http://localhost:8000/docs")
    print("   - Frontend:          http://localhost:3000")
    print()
    print("🤖 Auto-Updater:")
    print("   - Automatisch aktiviert bei Backend-Start")
    print("   - Update-Zeiten: täglich 17:30, 20:30, 22:30")
    print("   - Status: http://localhost:8000/api/auto-updater/status")
    print()
    print("📊 Datenbank:")
    print("   - 18 Bundesliga-Teams (Saison 2024/25)")
    print("   - Aktuelle und historische Matches")
    print("   - Echte Daten von OpenLigaDB API")
    print()

if __name__ == "__main__":
    asyncio.run(main())