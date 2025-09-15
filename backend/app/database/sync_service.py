"""
Synchronisation Service zwischen OpenLigaDB API und lokaler SQLite Database
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.database.database_service import DatabaseService
from app.services.openliga_client import OpenLigaDBClient
from app.services.data_converter import DataConverter
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self):
        self.league = "bl1"
        self.season = "2025"
        self.prediction_service = PredictionService()
    
    async def sync_all_data(self, force_full_sync: bool = False) -> Dict[str, Any]:
        """Synchronisiert alle Daten: Teams, Matches, Predictions"""
        sync_results = {
            "started_at": datetime.utcnow().isoformat(),
            "teams": {"synced": 0, "errors": []},
            "matches": {"synced": 0, "errors": []},
            "predictions": {"synced": 0, "errors": []},
            "quality": {"synced": 0, "errors": []}
        }
        
        try:
            # 1. Sync Teams
            logger.info("Starting teams synchronization...")
            teams_result = await self.sync_teams()
            sync_results["teams"] = teams_result
            
            # 2. Sync Matches
            logger.info("Starting matches synchronization...")
            matches_result = await self.sync_matches(force_full_sync)
            sync_results["matches"] = matches_result
            
            sync_results["completed_at"] = datetime.utcnow().isoformat()
            sync_results["success"] = True
            
            logger.info(f"Sync completed: {sync_results}")
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            sync_results["error"] = str(e)
            sync_results["success"] = False
        
        return sync_results
    
    async def sync_teams(self) -> Dict[str, Any]:
        """Synchronisiert Teams aus der API"""
        try:
            async with OpenLigaDBClient() as client:
                # Hole Teams für aktuelle Saison
                api_teams = await client.get_teams_by_league_season(self.league, self.season)
                
                synced_count = 0
                with DatabaseService() as db:
                    for team_data in api_teams:
                        try:
                            # Konvertiere API-Daten zu unserem Format
                            team_dict = {
                                'id': team_data.get('teamId', team_data.get('id')),
                                'name': team_data.get('teamName', team_data.get('name', '')),
                                'short_name': team_data.get('shortName', team_data.get('teamName', '')[:3]),
                                'logo_url': team_data.get('teamIconUrl', team_data.get('logo_url'))
                            }
                            
                            db.get_or_create_team(team_dict)
                            synced_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error syncing team {team_data}: {str(e)}")
                    
                    # Update Sync Status
                    db.update_sync_status("teams", True, f"Synced {synced_count} teams", synced_count)
                
                return {"synced": synced_count, "errors": []}
                
        except Exception as e:
            logger.error(f"Teams sync failed: {str(e)}")
            with DatabaseService() as db:
                db.update_sync_status("teams", False, str(e), 0)
            return {"synced": 0, "errors": [str(e)]}
    
    async def sync_matches(self, force_full_sync: bool = False) -> Dict[str, Any]:
        """Synchronisiert Matches aus der API"""
        try:
            async with OpenLigaDBClient() as client:
                # Hole alle Matches der Saison
                api_matches = await client.get_matches_by_league_season(self.league, self.season)
                
                synced_count = 0
                errors = []
                
                with DatabaseService() as db:
                    # Prüfe letzten Sync falls kein force_full_sync
                    if not force_full_sync:
                        sync_status = db.get_sync_status("matches")
                        if sync_status and sync_status[0].last_sync:
                            last_sync = sync_status[0].last_sync
                            # Sync nur wenn letzter Sync älter als 30 Minuten
                            if datetime.utcnow() - last_sync < timedelta(minutes=30):
                                logger.info("Matches recently synced, skipping...")
                                return {"synced": 0, "errors": [], "skipped": "Recently synced"}
                    
                    for match_data in api_matches:
                        try:
                            # Konvertiere API-Daten
                            match_dict = self._convert_api_match_to_dict(match_data)
                            
                            if match_dict:
                                db.get_or_create_match(match_dict)
                                synced_count += 1
                            
                        except Exception as e:
                            error_msg = f"Error syncing match {match_data.get('matchID', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                    
                    # Update Sync Status
                    db.update_sync_status("matches", len(errors) == 0, 
                                        f"Synced {synced_count} matches", synced_count)
                
                return {"synced": synced_count, "errors": errors}
                
        except Exception as e:
            logger.error(f"Matches sync failed: {str(e)}")
            with DatabaseService() as db:
                db.update_sync_status("matches", False, str(e), 0)
            return {"synced": 0, "errors": [str(e)]}
    
    def _convert_api_match_to_dict(self, api_match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Konvertiert API Match-Daten zu unserem Dict-Format"""
        try:
            # Extract Team Data
            team1 = api_match.get('team1', {})
            team2 = api_match.get('team2', {})
            
            if not team1 or not team2:
                logger.warning(f"Missing team data for match {api_match.get('matchID')}")
                return None
            
            # Extract Match Results
            match_results = api_match.get('matchResults', [])
            is_finished = api_match.get('matchIsFinished', False)
            
            home_goals = None
            away_goals = None
            
            if is_finished and match_results:
                # Nehme letztes (finales) Ergebnis
                final_result = match_results[-1]
                home_goals = final_result.get('pointsTeam1')
                away_goals = final_result.get('pointsTeam2')
            
            return {
                'id': api_match.get('matchID'),
                'home_team': {
                    'id': team1.get('teamId', team1.get('id')),
                    'name': team1.get('teamName', team1.get('name', '')),
                    'short_name': team1.get('shortName', team1.get('teamName', '')[:3]),
                    'logo_url': team1.get('teamIconUrl', team1.get('logo_url'))
                },
                'away_team': {
                    'id': team2.get('teamId', team2.get('id')),
                    'name': team2.get('teamName', team2.get('name', '')),
                    'short_name': team2.get('shortName', team2.get('teamName', '')[:3]),
                    'logo_url': team2.get('teamIconUrl', team2.get('logo_url'))
                },
                'date': api_match.get('matchDateTime', api_match.get('date', '')),
                'matchday': api_match.get('group', {}).get('groupOrderID', 1),
                'season': f"{self.league.upper()} {self.season}",
                'is_finished': is_finished,
                'home_goals': home_goals,
                'away_goals': away_goals
            }
            
        except Exception as e:
            logger.error(f"Error converting match data: {str(e)}")
            return None
    
    async def quick_sync(self) -> Dict[str, Any]:
        """Schnelle Synchronisation - nur neue/geänderte Daten"""
        logger.info("Starting quick sync...")
        
        # Prüfe nur abgeschlossene Spiele und neue Daten
        sync_results = {
            "type": "quick_sync",
            "started_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Sync nur neue finished matches
            matches_result = await self.sync_matches(force_full_sync=False)
            sync_results["matches"] = matches_result
            
            sync_results["completed_at"] = datetime.utcnow().isoformat()
            sync_results["success"] = True
            
        except Exception as e:
            logger.error(f"Quick sync failed: {str(e)}")
            sync_results["error"] = str(e)
            sync_results["success"] = False
        
        return sync_results
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.database.database_service import DatabaseService
from app.services.openliga_client import OpenLigaDBClient
from app.services.data_converter import DataConverter
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self):
        self.league = "bl1"
        self.season = "2025"
        self.prediction_service = PredictionService()
    
    async def sync_all_data(self, force_full_sync: bool = False) -> Dict[str, Any]:
        """Synchronisiert alle Daten: Teams, Matches, Predictions"""
        sync_results = {
            "started_at": datetime.utcnow().isoformat(),
            "teams": {"synced": 0, "errors": []},
            "matches": {"synced": 0, "errors": []},
            "predictions": {"synced": 0, "errors": []},
            "quality": {"synced": 0, "errors": []}
        }
        
        try:
            # 1. Sync Teams
            logger.info("Starting teams synchronization...")
            teams_result = await self.sync_teams()
            sync_results["teams"] = teams_result
            
            # 2. Sync Matches
            logger.info("Starting matches synchronization...")
            matches_result = await self.sync_matches(force_full_sync)
            sync_results["matches"] = matches_result
            
            # 3. Sync Predictions (nur für kommende Spiele)
            logger.info("Starting predictions synchronization...")
            predictions_result = await self.sync_predictions()
            sync_results["predictions"] = predictions_result
            
            # 4. Update Quality Analysis (nur für neue finished matches)
            logger.info("Starting quality analysis update...")
            quality_result = await self.update_quality_analysis()
            sync_results["quality"] = quality_result
            
            sync_results["completed_at"] = datetime.utcnow().isoformat()
            sync_results["success"] = True
            
            logger.info(f"Sync completed: {sync_results}")
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            sync_results["error"] = str(e)
            sync_results["success"] = False
        
        return sync_results
    
    async def sync_teams(self) -> Dict[str, Any]:
        """Synchronisiert Teams aus der API"""
        try:
            async with OpenLigaDBClient() as client:
                # Hole Teams für aktuelle Saison
                api_teams = await client.get_teams_by_league_season(self.league, self.season)
                
                synced_count = 0
                with DatabaseService() as db:
                    for team_data in api_teams:
                        try:
                            # Konvertiere API-Daten zu unserem Format
                            team_dict = {
                                'id': team_data.get('teamId', team_data.get('id')),
                                'name': team_data.get('teamName', team_data.get('name', '')),
                                'short_name': team_data.get('shortName', team_data.get('teamName', '')[:3]),
                                'logo_url': team_data.get('teamIconUrl', team_data.get('logo_url'))
                            }
                            
                            db.get_or_create_team(team_dict)
                            synced_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error syncing team {team_data}: {str(e)}")
                    
                    # Update Sync Status
                    db.update_sync_status("teams", True, f"Synced {synced_count} teams", synced_count)
                
                return {"synced": synced_count, "errors": []}
                
        except Exception as e:
            logger.error(f"Teams sync failed: {str(e)}")
            with DatabaseService() as db:
                db.update_sync_status("teams", False, str(e), 0)
            return {"synced": 0, "errors": [str(e)]}
    
    async def sync_matches(self, force_full_sync: bool = False) -> Dict[str, Any]:
        """Synchronisiert Matches aus der API"""
        try:
            async with OpenLigaDBClient() as client:
                # Hole alle Matches der Saison
                api_matches = await client.get_matches_by_league_season(self.league, self.season)
                
                synced_count = 0
                errors = []
                
                with DatabaseService() as db:
                    # Prüfe letzten Sync falls kein force_full_sync
                    if not force_full_sync:
                        sync_status = db.get_sync_status("matches")
                        if sync_status and sync_status[0].last_sync:
                            last_sync = sync_status[0].last_sync
                            # Sync nur wenn letzter Sync älter als 30 Minuten
                            if datetime.utcnow() - last_sync < timedelta(minutes=30):
                                logger.info("Matches recently synced, skipping...")
                                return {"synced": 0, "errors": [], "skipped": "Recently synced"}
                    
                    for match_data in api_matches:
                        try:
                            # Konvertiere API-Daten
                            match_dict = self._convert_api_match_to_dict(match_data)
                            
                            if match_dict:
                                db.get_or_create_match(match_dict)
                                synced_count += 1
                            
                        except Exception as e:
                            error_msg = f"Error syncing match {match_data.get('matchID', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                    
                    # Update Sync Status
                    db.update_sync_status("matches", len(errors) == 0, 
                                        f"Synced {synced_count} matches", synced_count)
                
                return {"synced": synced_count, "errors": errors}
                
        except Exception as e:
            logger.error(f"Matches sync failed: {str(e)}")
            with DatabaseService() as db:
                db.update_sync_status("matches", False, str(e), 0)
            return {"synced": 0, "errors": [str(e)]}
    
    async def sync_predictions(self) -> Dict[str, Any]:
        """Synchronisiert Vorhersagen für kommende Spiele"""
        try:
            synced_count = 0
            errors = []
            
            with DatabaseService() as db:
                # Hole alle nicht-abgeschlossenen Matches
                from app.database.models import Match as DBMatch
                unfinished_matches = db.session.query(DBMatch).filter(
                    DBMatch.is_finished == False
                ).all()
                
                # TODO: Implementiere Prediction Sync für unfinished matches
                # Für jedes Match: Berechne Prediction und speichere in DB
                
                return {"synced": synced_count, "errors": errors}
                
        except Exception as e:
            logger.error(f"Predictions sync failed: {str(e)}")
            return {"synced": 0, "errors": [str(e)]}
    
    async def update_quality_analysis(self) -> Dict[str, Any]:
        """Update Qualitäts-Analyse für neue abgeschlossene Spiele"""
        try:
            synced_count = 0
            errors = []
            
            with DatabaseService() as db:
                # Hole abgeschlossene Matches ohne Quality-Analyse
                finished_matches = db.get_matches_for_quality_analysis()
                
                for match in finished_matches:
                    try:
                        # Prüfe ob Quality-Analyse bereits existiert
                        from app.database.models import PredictionQuality as DBQuality
                        existing_quality = db.session.query(DBQuality).filter(
                            DBQuality.match_id == match.id
                        ).first()
                        
                        if not existing_quality:
                            # Berechne Quality für dieses Match
                            # TODO: Implementiere Quality-Berechnung
                            pass
                        
                    except Exception as e:
                        error_msg = f"Error calculating quality for match {match.id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                return {"synced": synced_count, "errors": errors}
                
        except Exception as e:
            logger.error(f"Quality analysis update failed: {str(e)}")
            return {"synced": 0, "errors": [str(e)]}
        """Synchronisiert Vorhersagen für kommende Spiele"""
        try:
            synced_count = 0
            errors = []
            
            with DatabaseService() as db:
                # Hole alle nicht-abgeschlossenen Matches
                unfinished_matches = db.session.query(db.session.query(
                    DatabaseService().session.query(DatabaseService().session.query().filter()
                )).all()  # Hier muss die Query noch angepasst werden
                
                # TODO: Implementiere Prediction Sync für unfinished matches
                # Für jedes Match: Berechne Prediction und speichere in DB
                
                return {"synced": synced_count, "errors": errors}
                
        except Exception as e:
            logger.error(f"Predictions sync failed: {str(e)}")
            return {"synced": 0, "errors": [str(e)]}
    
    async def update_quality_analysis(self) -> Dict[str, Any]:
        """Update Qualitäts-Analyse für neue abgeschlossene Spiele"""
        try:
            synced_count = 0
            errors = []
            
            with DatabaseService() as db:
                # Hole abgeschlossene Matches ohne Quality-Analyse
                finished_matches = db.get_matches_for_quality_analysis()
                
                for match in finished_matches:
                    try:
                        # Prüfe ob Quality-Analyse bereits existiert
                        existing_quality = db.session.query(db.session.query(
                            DatabaseService().session.query().filter()
                        )).first()  # Hier muss die Query noch angepasst werden
                        
                        if not existing_quality:
                            # Berechne Quality für dieses Match
                            # TODO: Implementiere Quality-Berechnung
                            pass
                        
                    except Exception as e:
                        error_msg = f"Error calculating quality for match {match.id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                return {"synced": synced_count, "errors": errors}
                
        except Exception as e:
            logger.error(f"Quality analysis update failed: {str(e)}")
            return {"synced": 0, "errors": [str(e)]}
    
    def _convert_api_match_to_dict(self, api_match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Konvertiert API Match-Daten zu unserem Dict-Format"""
        try:
            # Extract Team Data
            team1 = api_match.get('team1', {})
            team2 = api_match.get('team2', {})
            
            if not team1 or not team2:
                logger.warning(f"Missing team data for match {api_match.get('matchID')}")
                return None
            
            # Extract Match Results
            match_results = api_match.get('matchResults', [])
            is_finished = api_match.get('matchIsFinished', False)
            
            home_goals = None
            away_goals = None
            
            if is_finished and match_results:
                # Nehme letztes (finales) Ergebnis
                final_result = match_results[-1]
                home_goals = final_result.get('pointsTeam1')
                away_goals = final_result.get('pointsTeam2')
            
            return {
                'id': api_match.get('matchID'),
                'home_team': {
                    'id': team1.get('teamId', team1.get('id')),
                    'name': team1.get('teamName', team1.get('name', '')),
                    'short_name': team1.get('shortName', team1.get('teamName', '')[:3]),
                    'logo_url': team1.get('teamIconUrl', team1.get('logo_url'))
                },
                'away_team': {
                    'id': team2.get('teamId', team2.get('id')),
                    'name': team2.get('teamName', team2.get('name', '')),
                    'short_name': team2.get('shortName', team2.get('teamName', '')[:3]),
                    'logo_url': team2.get('teamIconUrl', team2.get('logo_url'))
                },
                'date': api_match.get('matchDateTime', api_match.get('date', '')),
                'matchday': api_match.get('group', {}).get('groupOrderID', 1),
                'season': f"{self.league.upper()} {self.season}",
                'is_finished': is_finished,
                'home_goals': home_goals,
                'away_goals': away_goals
            }
            
        except Exception as e:
            logger.error(f"Error converting match data: {str(e)}")
            return None
    
    async def quick_sync(self) -> Dict[str, Any]:
        """Schnelle Synchronisation - nur neue/geänderte Daten"""
        logger.info("Starting quick sync...")
        
        # Prüfe nur abgeschlossene Spiele und neue Daten
        sync_results = {
            "type": "quick_sync",
            "started_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Sync nur neue finished matches
            matches_result = await self.sync_matches(force_full_sync=False)
            sync_results["matches"] = matches_result
            
            # Update nur neue Quality-Analysen
            quality_result = await self.update_quality_analysis()
            sync_results["quality"] = quality_result
            
            sync_results["completed_at"] = datetime.utcnow().isoformat()
            sync_results["success"] = True
            
        except Exception as e:
            logger.error(f"Quick sync failed: {str(e)}")
            sync_results["error"] = str(e)
            sync_results["success"] = False
        
        return sync_results