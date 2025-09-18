"""
Automatisches Update-System für Spieltage
Läuft zwischen 17:00 und 23:00 Uhr alle 30 Minuten
Optimiert für Bundesliga-Spielzeiten (Freitag, Samstag, Sonntag)
"""
import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from real_data_sync import RealDataSync
import logging

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspaces/kick-predictor/backend/auto_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GamedayAutoUpdater:
    def __init__(self):
        self.sync = RealDataSync()
        self.is_running = False
        self.last_update = None
        self.update_count = 0
        
    def is_gameday_time(self) -> bool:
        """Prüfe ob es gerade Update-Zeit ist (17:30, 20:30 oder 22:30)"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Update-Zeiten: täglich um 17:30, 20:30 und 22:30
        update_times = ["17:30", "20:30", "22:30"]
        
        return current_time in update_times
    
    async def smart_update(self) -> dict:
        """Intelligentes Update - nur wenn nötig"""
        try:
            logger.info("🔍 Starte Smart-Update Prüfung...")
            
            # Prüfe aktuelle Spieltag-Situation
            conn = self.sync.get_db_connection()
            cursor = conn.cursor()
            
            # Aktueller Spieltag
            cursor.execute("""
                SELECT MAX(matchday) 
                FROM matches_real 
                WHERE season = '2025' AND is_finished = 1
            """)
            last_completed = cursor.fetchone()[0] or 3
            next_matchday = last_completed + 1
            
            # Prüfe ob heute Spiele sind (oder in den nächsten Tagen)
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN is_finished = 1 THEN 1 ELSE 0 END) as finished
                FROM matches_real 
                WHERE season = '2025' 
                AND matchday = ?
                AND date(match_date) >= date('now', '-1 day')
                AND date(match_date) <= date('now', '+1 day')
            """, (next_matchday,))
            
            result = cursor.fetchone()
            todays_matches = result[0] if result else 0
            finished_today = result[1] if result else 0
            
            conn.close()
            
            if todays_matches == 0:
                logger.info("ℹ️ Keine relevanten Spiele in naher Zeit - führe trotzdem Update durch")
                # Führe Update trotzdem durch, um sicherzustellen dass wir nichts verpassen
            
            # Lade neue Daten
            logger.info(f"⚽ Prüfe Spieltag {next_matchday} - {todays_matches} Spiele heute, {finished_today} beendet")
            
            # Nur den aktuellen Spieltag laden (effizienter)
            current_matches = await self.sync.fetch_matches_from_season("2025")
            recent_matches = [
                m for m in current_matches 
                if m['matchday'] == next_matchday
            ]
            
            if recent_matches:
                self.sync.save_matches_to_db(recent_matches)
                self.sync.update_season_info()
                
                # Zähle neue beendete Spiele
                new_finished = sum(1 for m in recent_matches if m['isFinished'])
                
                self.last_update = datetime.now()
                self.update_count += 1
                
                logger.info(f"✅ Update #{self.update_count} abgeschlossen - {new_finished} beendete Spiele")
                
                return {
                    "status": "success",
                    "message": f"Spieltag {next_matchday} aktualisiert",
                    "matches_updated": len(recent_matches),
                    "finished_matches": new_finished,
                    "update_count": self.update_count,
                    "last_update": self.last_update.isoformat()
                }
            else:
                logger.info("ℹ️ Keine neuen Daten verfügbar")
                return {"status": "no_new_data", "message": "Keine Änderungen"}
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Smart-Update: {e}")
            return {"status": "error", "message": str(e)}
    
    def run_update_if_gameday(self):
        """Führe Update aus (täglich zu den konfigurierten Zeiten)"""
        logger.info("🎮 Update-Zeit erkannt - starte automatisches Update...")
        
        # Async Update in Thread ausführen
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.smart_update())
            loop.close()
            
            if result["status"] == "success":
                logger.info(f"🎯 Automatisches Update erfolgreich: {result['message']}")
        except Exception as e:
            logger.error(f"❌ Fehler beim automatischen Update: {e}")
    
    def schedule_gameday_updates(self):
        """Plane Updates täglich um 17:30, 20:30 und 22:30"""
        # Täglich um die definierten Zeiten
        schedule.every().day.at("17:30").do(self.run_update_if_gameday)
        schedule.every().day.at("20:30").do(self.run_update_if_gameday)
        schedule.every().day.at("22:30").do(self.run_update_if_gameday)
        
        # Zusätzlich: Montagmorgen Vollupdate (falls etwas verpasst wurde)
        schedule.every().monday.at("03:00").do(self.weekly_cleanup)
        
        logger.info("⏰ Automatische Updates geplant:")
        logger.info("   - Täglich: 17:30, 20:30, 22:30")
        logger.info("   - Montag 03:00: Wöchentliches Cleanup")
    
    def weekly_cleanup(self):
        """Wöchentliches Vollupdate zur Sicherheit"""
        logger.info("🧹 Wöchentliches Cleanup gestartet...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.sync.sync_all_real_data())
            loop.close()
            logger.info("✅ Wöchentliches Cleanup abgeschlossen")
        except Exception as e:
            logger.error(f"❌ Fehler beim wöchentlichen Cleanup: {e}")
    
    def start_scheduler(self):
        """Starte den Scheduler in separatem Thread"""
        if self.is_running:
            logger.warning("⚠️ Scheduler läuft bereits!")
            return
        
        self.is_running = True
        logger.info("🚀 Gameday Auto-Updater gestartet...")
        logger.info(f"   Aktuelle Zeit: {datetime.now().strftime('%A, %H:%M')}")
        logger.info(f"   Nächste Update-Zeit: 17:30, 20:30 oder 22:30")
        
        def scheduler_thread():
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Prüfe jede Minute
                except Exception as e:
                    logger.error(f"❌ Scheduler-Fehler: {e}")
                    time.sleep(300)  # 5 Min warten bei Fehler
        
        thread = threading.Thread(target=scheduler_thread, daemon=True)
        thread.start()
        
        return thread
    
    def stop_scheduler(self):
        """Stoppe den Scheduler"""
        self.is_running = False
        logger.info("⏹️ Gameday Auto-Updater gestoppt")
    
    def get_status(self) -> dict:
        """Hole aktuellen Status"""
        return {
            "is_running": self.is_running,
            "is_gameday_time": self.is_gameday_time(),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "update_count": self.update_count,
            "current_time": datetime.now().isoformat(),
            "next_scheduled_updates": self.get_next_updates()
        }
    
    def get_next_updates(self) -> list:
        """Berechne nächste geplante Updates"""
        now = datetime.now()
        next_updates = []
        
        # Update-Zeiten: 17:30, 20:30, 22:30
        update_times = ["17:30", "20:30", "22:30"]
        
        # Nächste 3 Tage
        for days_ahead in range(3):
            check_date = now + timedelta(days=days_ahead)
            day_name = check_date.strftime('%A')
            
            next_updates.append({
                "date": check_date.strftime('%Y-%m-%d'),
                "day": day_name,
                "times": "17:30, 20:30, 22:30"
            })
        
        return next_updates

# Globale Instanz
auto_updater = GamedayAutoUpdater()

def start_auto_updater():
    """Starte den Auto-Updater"""
    auto_updater.schedule_gameday_updates()
    return auto_updater.start_scheduler()

def stop_auto_updater():
    """Stoppe den Auto-Updater"""
    auto_updater.stop_scheduler()

def get_updater_status():
    """Hole Status des Auto-Updaters"""
    return auto_updater.get_status()

if __name__ == "__main__":
    # Für direkten Start
    updater = GamedayAutoUpdater()
    updater.schedule_gameday_updates()
    
    # Einmaliger Test-Update
    logger.info("🧪 Teste einmaliges Update...")
    asyncio.run(updater.smart_update())
    
    # Dann Scheduler starten
    try:
        updater.start_scheduler()
        logger.info("✅ Auto-Updater läuft - Drücke Ctrl+C zum Beenden")
        
        # Hauptloop
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Auto-Updater wird beendet...")
        updater.stop_scheduler()