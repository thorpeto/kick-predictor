"""
Automatisches Update-System für neue Spieltage
Überwacht neue Ergebnisse und aktualisiert Vorhersagen automatisch
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from real_data_sync import RealDataSync
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoUpdater:
    def __init__(self):
        self.sync = RealDataSync()
        
    async def check_for_new_results(self):
        """Prüfe ob neue Spielergebnisse verfügbar sind"""
        logger.info("🔍 Prüfe auf neue Spielergebnisse...")
        
        # Lade nur den aktuellen Spieltag
        current_matchday = await self.get_current_matchday()
        matches = await self.sync.fetch_matches_from_season("2025")
        
        # Filtere nur neue/geänderte Matches
        new_results_count = 0
        for match in matches:
            if match['matchday'] >= current_matchday - 1:  # Aktueller + vorheriger Spieltag
                if match['isFinished']:
                    new_results_count += 1
        
        logger.info(f"✅ {new_results_count} neue Ergebnisse gefunden")
        return new_results_count > 0
    
    async def get_current_matchday(self) -> int:
        """Ermittle aktuellen Spieltag"""
        conn = self.sync.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(matchday) 
            FROM matches_real 
            WHERE season = '2025' AND is_finished = 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        return (result[0] + 1) if result and result[0] else 4
    
    async def incremental_update(self):
        """Inkrementelles Update - nur neue Daten laden"""
        logger.info("⚡ Starte inkrementelles Update...")
        
        try:
            # Nur die letzten 2 Spieltage aktualisieren
            current_matchday = await self.get_current_matchday()
            
            # Update der aktuellen Saison (nur relevante Spieltage)
            matches = await self.sync.fetch_matches_from_season("2025")
            recent_matches = [
                m for m in matches 
                if m['matchday'] >= current_matchday - 1
            ]
            
            if recent_matches:
                self.sync.save_matches_to_db(recent_matches)
                self.sync.update_season_info()
                logger.info(f"✅ {len(recent_matches)} Matches aktualisiert")
                return True
            else:
                logger.info("ℹ️ Keine neuen Daten verfügbar")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim inkrementellen Update: {e}")
            return False
    
    async def full_weekly_update(self):
        """Wöchentliches vollständiges Update"""
        logger.info("🔄 Starte wöchentliches Vollupdate...")
        await self.sync.sync_all_real_data()
    
    def schedule_updates(self):
        """Plane automatische Updates"""
        # Inkrementelle Updates: Alle 2 Stunden während der Spieltage
        schedule.every(2).hours.do(lambda: asyncio.run(self.incremental_update()))
        
        # Vollupdate: Jeden Montag um 03:00 (nach dem Spieltagsende)
        schedule.every().monday.at("03:00").do(lambda: asyncio.run(self.full_weekly_update()))
        
        # Spieltag-spezifische Updates:
        # Freitag 22:00 (nach Freitagsspiel)
        schedule.every().friday.at("22:00").do(lambda: asyncio.run(self.incremental_update()))
        
        # Samstag 19:00 und 22:00 (nach Samstagsspielen)
        schedule.every().saturday.at("19:00").do(lambda: asyncio.run(self.incremental_update()))
        schedule.every().saturday.at("22:00").do(lambda: asyncio.run(self.incremental_update()))
        
        # Sonntag 19:00 und 22:00 (nach Sonntagsspielen)
        schedule.every().sunday.at("19:00").do(lambda: asyncio.run(self.incremental_update()))
        schedule.every().sunday.at("22:00").do(lambda: asyncio.run(self.incremental_update()))
        
        logger.info("⏰ Update-Schedule eingerichtet")
    
    def run_scheduler(self):
        """Starte den Scheduler"""
        logger.info("🚀 Auto-Updater gestartet...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Prüfe jede Minute

# API Endpoint für manuelles Update
async def manual_update_endpoint():
    """API-Endpoint für manuelles Update (kann in main_real_data.py integriert werden)"""
    updater = AutoUpdater()
    success = await updater.incremental_update()
    return {
        "status": "success" if success else "no_new_data",
        "updated_at": datetime.now().isoformat(),
        "message": "Update erfolgreich" if success else "Keine neuen Daten"
    }

if __name__ == "__main__":
    updater = AutoUpdater()
    
    # Einmaliges Update beim Start
    asyncio.run(updater.incremental_update())
    
    # Dann Scheduler starten
    updater.schedule_updates()
    updater.run_scheduler()