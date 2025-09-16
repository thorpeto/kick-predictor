"""
Synchronization service for API data to database
Handles the conversion and storage of API data into database models
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

from app.database.database_service import DatabaseService
from app.database.models import Team, Match, Prediction, PredictionQuality, SyncStatus
from app.services.data_service import DataService
from app.services.prediction_service import PredictionService
from app.models.schemas import MatchResult, MatchdayInfo, PredictionData

logger = logging.getLogger(__name__)

class SyncService:
    """Service for synchronizing API data to database"""
    
    def __init__(self):
        self.data_service = DataService()
        self.prediction_service = PredictionService()
    
    async def sync_all_data(self, season: str = "2025", league: str = "bl1") -> Dict[str, Any]:
        """
        Vollständige Synchronisation aller Daten
        Returns sync statistics
        """
        logger.info(f"Starting full data sync for {league} {season}")
        
        stats = {
            "teams_synced": 0,
            "matches_synced": 0,
            "predictions_synced": 0,
            "quality_entries_synced": 0,
            "errors": [],
            "start_time": datetime.now(),
            "status": "running"
        }
        
        try:
            # 1. Sync teams first
            teams_result = await self.sync_teams(league, season)
            stats["teams_synced"] = teams_result["count"]
            if teams_result["errors"]:
                stats["errors"].extend(teams_result["errors"])
            
            # 2. Sync matches
            matches_result = await self.sync_matches(league, season)
            stats["matches_synced"] = matches_result["count"]
            if matches_result["errors"]:
                stats["errors"].extend(matches_result["errors"])
            
            # 3. Sync predictions for current matchday
            predictions_result = await self.sync_current_predictions(league, season)
            stats["predictions_synced"] = predictions_result["count"]
            if predictions_result["errors"]:
                stats["errors"].extend(predictions_result["errors"])
            
            # 4. Sync prediction quality
            quality_result = await self.sync_prediction_quality(league, season)
            stats["quality_entries_synced"] = quality_result["count"]
            if quality_result["errors"]:
                stats["errors"].extend(quality_result["errors"])
            
            stats["status"] = "completed"
            stats["end_time"] = datetime.now()
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
            
            # Update sync status in database
            await self._update_sync_status("full_sync", stats)
            
            logger.info(f"Full sync completed: {stats}")
            return stats
            
        except Exception as e:
            stats["status"] = "failed"
            stats["error"] = str(e)
            stats["end_time"] = datetime.now()
            logger.error(f"Full sync failed: {e}")
            await self._update_sync_status("full_sync", stats)
            return stats
    
    async def sync_teams(self, league: str = "bl1", season: str = "2025") -> Dict[str, Any]:
        """Synchronize teams from API to database"""
        logger.info(f"Syncing teams for {league} {season}")
        
        result = {"count": 0, "errors": []}
        
        try:
            # Get teams from API
            teams_data = await self.data_service.get_teams()
            
            with DatabaseService() as db:
                for team_data in teams_data:
                    try:
                        # Check if team exists
                        existing_team = db.session.query(Team).filter_by(
                            external_id=team_data["id"]
                        ).first()
                        
                        if existing_team:
                            # Update existing team
                            existing_team.name = team_data["name"]
                            existing_team.short_name = team_data.get("short_name", team_data["name"][:3])
                            existing_team.logo_url = team_data.get("icon", "")
                            existing_team.updated_at = datetime.now()
                        else:
                            # Create new team
                            new_team = Team(
                                external_id=team_data["id"],
                                name=team_data["name"],
                                short_name=team_data.get("short_name", team_data["name"][:3]),
                                logo_url=team_data.get("icon", ""),
                                league=league,
                                season=season,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db.session.add(new_team)
                        
                        result["count"] += 1
                        
                    except Exception as e:
                        error_msg = f"Error syncing team {team_data.get('name', 'unknown')}: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                
                db.session.commit()
                logger.info(f"Successfully synced {result['count']} teams")
                
        except Exception as e:
            error_msg = f"Error syncing teams: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def sync_matches(self, league: str = "bl1", season: str = "2025") -> Dict[str, Any]:
        """Synchronize matches from API to database"""
        logger.info(f"Syncing matches for {league} {season}")
        
        result = {"count": 0, "errors": []}
        
        try:
            # Get current matchday info
            matchday_info = await self.data_service.get_current_matchday_info()
            current_matchday = matchday_info.current_matchday
            
            # Sync multiple matchdays (current and previous for results)
            matchdays_to_sync = range(max(1, current_matchday - 5), current_matchday + 3)
            
            with DatabaseService() as db:
                for matchday in matchdays_to_sync:
                    try:
                        matches_data = await self.data_service.get_matches_by_matchday(matchday)
                        
                        for match_data in matches_data:
                            try:
                                # Get team IDs from database
                                home_team = db.session.query(Team).filter_by(
                                    external_id=match_data.home_team["id"]
                                ).first()
                                away_team = db.session.query(Team).filter_by(
                                    external_id=match_data.away_team["id"]
                                ).first()
                                
                                if not home_team or not away_team:
                                    logger.warning(f"Teams not found for match {match_data.match_id}")
                                    continue
                                
                                # Check if match exists
                                existing_match = db.session.query(Match).filter_by(
                                    external_id=match_data.match_id
                                ).first()
                                
                                if existing_match:
                                    # Update existing match
                                    existing_match.home_goals = match_data.home_goals
                                    existing_match.away_goals = match_data.away_goals
                                    existing_match.is_finished = match_data.is_finished
                                    existing_match.updated_at = datetime.now()
                                else:
                                    # Create new match
                                    new_match = Match(
                                        external_id=match_data.match_id,
                                        home_team_id=home_team.id,
                                        away_team_id=away_team.id,
                                        home_goals=match_data.home_goals,
                                        away_goals=match_data.away_goals,
                                        date=match_data.date,
                                        matchday=match_data.matchday,
                                        season=season,
                                        league=league,
                                        is_finished=match_data.is_finished,
                                        created_at=datetime.now(),
                                        updated_at=datetime.now()
                                    )
                                    db.session.add(new_match)
                                
                                result["count"] += 1
                                
                            except Exception as e:
                                error_msg = f"Error syncing match {match_data.match_id}: {str(e)}"
                                logger.error(error_msg)
                                result["errors"].append(error_msg)
                    
                    except Exception as e:
                        error_msg = f"Error syncing matchday {matchday}: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                
                db.session.commit()
                logger.info(f"Successfully synced {result['count']} matches")
                
        except Exception as e:
            error_msg = f"Error syncing matches: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def sync_current_predictions(self, league: str = "bl1", season: str = "2025") -> Dict[str, Any]:
        """Synchronize current predictions to database"""
        logger.info(f"Syncing current predictions for {league} {season}")
        
        result = {"count": 0, "errors": []}
        
        try:
            # Get current matchday info
            matchday_info = await self.data_service.get_current_matchday_info()
            current_matchday = matchday_info.current_matchday
            
            # Get predictions for current matchday
            predictions_data = await self.data_service.get_predictions(current_matchday)
            
            with DatabaseService() as db:
                for pred_data in predictions_data:
                    try:
                        # Get match from database
                        match = db.session.query(Match).filter_by(
                            external_id=pred_data["match"]["match_id"]
                        ).first()
                        
                        if not match:
                            logger.warning(f"Match not found for prediction: {pred_data['match']['match_id']}")
                            continue
                        
                        # Check if prediction exists
                        existing_pred = db.session.query(Prediction).filter_by(
                            match_id=match.id
                        ).first()
                        
                        prediction_obj = pred_data["prediction"]
                        
                        if existing_pred:
                            # Update existing prediction
                            existing_pred.predicted_home_goals = prediction_obj["home_goals"]
                            existing_pred.predicted_away_goals = prediction_obj["away_goals"]
                            existing_pred.home_win_prob = prediction_obj["probabilities"]["home_win"]
                            existing_pred.draw_prob = prediction_obj["probabilities"]["draw"]
                            existing_pred.away_win_prob = prediction_obj["probabilities"]["away_win"]
                            existing_pred.confidence = prediction_obj["confidence"]
                            existing_pred.updated_at = datetime.now()
                        else:
                            # Create new prediction
                            new_pred = Prediction(
                                match_id=match.id,
                                predicted_home_goals=prediction_obj["home_goals"],
                                predicted_away_goals=prediction_obj["away_goals"],
                                home_win_prob=prediction_obj["probabilities"]["home_win"],
                                draw_prob=prediction_obj["probabilities"]["draw"],
                                away_win_prob=prediction_obj["probabilities"]["away_win"],
                                confidence=prediction_obj["confidence"],
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db.session.add(new_pred)
                        
                        result["count"] += 1
                        
                    except Exception as e:
                        error_msg = f"Error syncing prediction for match {pred_data.get('match', {}).get('match_id', 'unknown')}: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                
                db.session.commit()
                logger.info(f"Successfully synced {result['count']} predictions")
                
        except Exception as e:
            error_msg = f"Error syncing predictions: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def sync_prediction_quality(self, league: str = "bl1", season: str = "2025") -> Dict[str, Any]:
        """Synchronize prediction quality data to database"""
        logger.info(f"Syncing prediction quality for {league} {season}")
        
        result = {"count": 0, "errors": []}
        
        try:
            # Get quality data from API
            quality_data = await self.data_service.get_prediction_quality()
            
            if not quality_data or "entries" not in quality_data:
                logger.warning("No quality data received from API")
                return result
            
            with DatabaseService() as db:
                for entry in quality_data["entries"]:
                    try:
                        # Get match and prediction from database
                        match = db.session.query(Match).filter_by(
                            external_id=entry["match"]["match_id"]
                        ).first()
                        
                        if not match:
                            logger.warning(f"Match not found for quality entry: {entry['match']['match_id']}")
                            continue
                        
                        prediction = db.session.query(Prediction).filter_by(
                            match_id=match.id
                        ).first()
                        
                        if not prediction:
                            logger.warning(f"Prediction not found for match: {match.id}")
                            continue
                        
                        # Check if quality entry exists
                        existing_quality = db.session.query(PredictionQuality).filter_by(
                            prediction_id=prediction.id
                        ).first()
                        
                        # Determine hit type
                        from app.database.models import HitType
                        hit_type = None
                        if entry.get("exact_score_correct"):
                            hit_type = HitType.EXACT_MATCH
                        elif entry.get("tendency_correct"):
                            hit_type = HitType.TENDENCY_MATCH
                        else:
                            hit_type = HitType.MISS
                        
                        if existing_quality:
                            # Update existing quality entry
                            existing_quality.actual_score = entry.get("actual_score", "")
                            existing_quality.hit_type = hit_type
                            existing_quality.tendency_correct = entry.get("tendency_correct", False)
                            existing_quality.exact_score_correct = entry.get("exact_score_correct", False)
                            existing_quality.updated_at = datetime.now()
                        else:
                            # Create new quality entry
                            new_quality = PredictionQuality(
                                prediction_id=prediction.id,
                                actual_score=entry.get("actual_score", ""),
                                hit_type=hit_type,
                                tendency_correct=entry.get("tendency_correct", False),
                                exact_score_correct=entry.get("exact_score_correct", False),
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db.session.add(new_quality)
                        
                        result["count"] += 1
                        
                    except Exception as e:
                        error_msg = f"Error syncing quality entry: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                
                db.session.commit()
                logger.info(f"Successfully synced {result['count']} quality entries")
                
        except Exception as e:
            error_msg = f"Error syncing prediction quality: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    async def _update_sync_status(self, sync_type: str, stats: Dict[str, Any]) -> None:
        """Update sync status in database"""
        try:
            with DatabaseService() as db:
                sync_status = SyncStatus(
                    sync_type=sync_type,
                    status=stats["status"],
                    items_processed=stats.get("teams_synced", 0) + stats.get("matches_synced", 0) + 
                                   stats.get("predictions_synced", 0) + stats.get("quality_entries_synced", 0),
                    error_count=len(stats.get("errors", [])),
                    error_details="; ".join(stats.get("errors", [])) if stats.get("errors") else None,
                    duration_seconds=stats.get("duration", 0),
                    created_at=datetime.now()
                )
                db.session.add(sync_status)
                db.session.commit()
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        try:
            with DatabaseService() as db:
                stats = db.get_database_stats()
                sync_status = db.get_sync_status()
                
                return {
                    "database_stats": stats,
                    "sync_status": sync_status,
                    "last_sync": sync_status.get("last_full_sync") if sync_status else None
                }
        except Exception as e:
            logger.error(f"Error getting sync statistics: {e}")
            return {"error": str(e)}