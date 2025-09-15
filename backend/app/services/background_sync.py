"""
Background Sync Scheduler für automatische Daten-Synchronisation
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading
import time

from app.services.openliga_client import OpenLigaDBClient
from app.database.database_service import DatabaseService

logger = logging.getLogger(__name__)

class BackgroundSyncScheduler:
    def __init__(self):
        self.league = "bl1"
        self.season = "2025"
        self.sync_interval_minutes = 30  # Alle 30 Minuten
        self.is_running = False
        self.sync_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def start(self):
        """Startet den Background Sync Scheduler"""
        if self.is_running:
            logger.warning("Sync scheduler is already running")
            return
            
        self.is_running = True
        self.stop_event.clear()
        self.sync_thread = threading.Thread(target=self._run_sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("Background sync scheduler started")
    
    def stop(self):
        """Stoppt den Background Sync Scheduler"""
        if not self.is_running:
            return
            
        self.stop_event.set()
        self.is_running = False
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
            
        logger.info("Background sync scheduler stopped")
    
    def _run_sync_loop(self):
        """Haupt-Loop für Background Sync"""
        logger.info(f"Sync loop started - interval: {self.sync_interval_minutes} minutes")
        
        # Führe initialen Sync durch
        asyncio.run(self._perform_sync("initial"))
        
        while not self.stop_event.is_set():
            try:
                # Warte für das Sync-Interval
                if self.stop_event.wait(timeout=self.sync_interval_minutes * 60):
                    break  # Stop event was set
                
                # Führe Sync durch
                asyncio.run(self._perform_sync("scheduled"))
                
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                # Bei Fehler warte 5 Minuten bevor retry
                if self.stop_event.wait(timeout=300):
                    break
    
    async def _perform_sync(self, sync_type: str = "manual"):
        """Führt Synchronisation durch"""
        start_time = datetime.utcnow()
        logger.info(f"Starting {sync_type} sync at {start_time.isoformat()}")
        
        try:
            # Teams synchronisieren
            teams_synced = await self._sync_teams()
            
            # Matches synchronisieren
            matches_synced = await self._sync_matches()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Sync completed in {duration:.2f}s - Teams: {teams_synced}, Matches: {matches_synced}")
            
            # Update globalen Sync Status
            with DatabaseService() as db:
                db.update_sync_status(
                    "background_sync", 
                    True, 
                    f"{sync_type} sync completed - {teams_synced} teams, {matches_synced} matches",
                    teams_synced + matches_synced
                )
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            # Update Fehlerstatus
            with DatabaseService() as db:
                db.update_sync_status("background_sync", False, str(e), 0)
    
    async def _sync_teams(self) -> int:
        """Synchronisiert Teams"""
        try:
            async with OpenLigaDBClient() as client:
                # Vereinfachter Team-Sync
                try:
                    # Versuche Teams direkt zu holen
                    teams_data = await client.get_request(f"/teams/{self.league}/{self.season}")
                except:
                    # Fallback: Teams aus Matches extrahieren
                    matches_data = await client.get_request(f"/matches/{self.league}/{self.season}")
                    teams_set = set()
                    
                    for match in matches_data[:20]:  # Erste 20 Matches
                        if 'team1' in match and match['team1']:
                            team_id = match['team1'].get('teamId')
                            team_name = match['team1'].get('teamName')
                            if team_id and team_name:
                                teams_set.add((team_id, team_name, match['team1'].get('shortName', team_name[:3])))
                        
                        if 'team2' in match and match['team2']:
                            team_id = match['team2'].get('teamId')
                            team_name = match['team2'].get('teamName')
                            if team_id and team_name:
                                teams_set.add((team_id, team_name, match['team2'].get('shortName', team_name[:3])))
                    
                    teams_data = [
                        {
                            "teamId": tid,
                            "teamName": name,
                            "shortName": short_name
                        }
                        for tid, name, short_name in teams_set
                    ]
                
                synced_count = 0
                with DatabaseService() as db:
                    for team_data in teams_data:
                        if not team_data.get('teamId') or not team_data.get('teamName'):
                            continue
                            
                        team_dict = {
                            'id': team_data['teamId'],
                            'name': team_data['teamName'],
                            'short_name': team_data.get('shortName', team_data['teamName'][:3]),
                            'logo_url': team_data.get('teamIconUrl')
                        }
                        
                        db.get_or_create_team(team_dict)
                        synced_count += 1
                
                return synced_count
                
        except Exception as e:
            logger.error(f"Team sync failed: {str(e)}")
            return 0
    
    async def _sync_matches(self) -> int:
        """Synchronisiert Matches"""
        try:
            async with OpenLigaDBClient() as client:
                matches_data = await client.get_request(f"/matches/{self.league}/{self.season}")
                
                synced_count = 0
                with DatabaseService() as db:
                    for match_data in matches_data:
                        try:
                            match_dict = self._convert_match_data(match_data)
                            if match_dict:
                                db.get_or_create_match(match_dict)
                                synced_count += 1
                        except Exception as e:
                            logger.warning(f"Error syncing match {match_data.get('matchID')}: {str(e)}")
                            continue
                
                return synced_count
                
        except Exception as e:
            logger.error(f"Match sync failed: {str(e)}")
            return 0
    
    def _convert_match_data(self, api_match: dict) -> Optional[dict]:
        """Konvertiert API Match-Daten"""
        try:
            team1 = api_match.get('team1', {})
            team2 = api_match.get('team2', {})
            
            if not team1 or not team2:
                return None
            
            # Match Results
            match_results = api_match.get('matchResults', [])
            is_finished = api_match.get('matchIsFinished', False)
            
            home_goals = None
            away_goals = None
            
            if is_finished and match_results:
                final_result = match_results[-1]
                home_goals = final_result.get('pointsTeam1')
                away_goals = final_result.get('pointsTeam2')
            
            return {
                'id': api_match.get('matchID'),
                'home_team': {
                    'id': team1.get('teamId'),
                    'name': team1.get('teamName', ''),
                    'short_name': team1.get('shortName', team1.get('teamName', '')[:3]),
                    'logo_url': team1.get('teamIconUrl')
                },
                'away_team': {
                    'id': team2.get('teamId'),
                    'name': team2.get('teamName', ''),
                    'short_name': team2.get('shortName', team2.get('teamName', '')[:3]),
                    'logo_url': team2.get('teamIconUrl')
                },
                'date': api_match.get('matchDateTime', ''),
                'matchday': api_match.get('group', {}).get('groupOrderID', 1),
                'season': f"BL1 {self.season}",
                'is_finished': is_finished,
                'home_goals': home_goals,
                'away_goals': away_goals
            }
            
        except Exception as e:
            logger.error(f"Error converting match data: {str(e)}")
            return None
    
    async def trigger_manual_sync(self) -> dict:
        """Triggert manuellen Sync"""
        start_time = datetime.utcnow()
        
        try:
            await self._perform_sync("manual")
            
            with DatabaseService() as db:
                stats = db.get_database_stats()
            
            return {
                "success": True,
                "message": "Manual sync completed successfully",
                "stats": stats,
                "sync_time": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Manual sync failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sync_time": start_time.isoformat()
            }

# Global Scheduler Instance
background_scheduler = BackgroundSyncScheduler()