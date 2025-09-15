"""
Database Service für CRUD-Operationen und Synchronisation
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.database.models import Team, Match, Prediction, PredictionQuality, SyncStatus, HitType
from app.database.config import get_database_session, db_config
from app.models.schemas import Match as MatchSchema, Team as TeamSchema

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = db_config.get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            db_config.close_session(self.session)
    
    # ========== TEAM OPERATIONS ==========
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Hole Team nach ID"""
        return self.session.query(Team).filter(Team.id == team_id).first()
    
    def get_or_create_team(self, team_data: Dict[str, Any]) -> Team:
        """Hole oder erstelle Team"""
        team = self.session.query(Team).filter(Team.id == team_data['id']).first()
        
        if not team:
            team = Team(
                id=team_data['id'],
                name=team_data['name'],
                short_name=team_data.get('short_name', team_data['name'][:3]),
                logo_url=team_data.get('logo_url')
            )
            self.session.add(team)
            logger.info(f"Created new team: {team.name}")
        else:
            # Update falls sich Daten geändert haben
            updated = False
            if team.name != team_data['name']:
                team.name = team_data['name']
                updated = True
            if team_data.get('short_name') and team.short_name != team_data['short_name']:
                team.short_name = team_data['short_name']
                updated = True
            if team_data.get('logo_url') and team.logo_url != team_data['logo_url']:
                team.logo_url = team_data['logo_url']
                updated = True
            
            if updated:
                team.updated_at = datetime.utcnow()
                logger.info(f"Updated team: {team.name}")
        
        return team
    
    def get_all_teams(self) -> List[Team]:
        """Hole alle Teams"""
        return self.session.query(Team).order_by(Team.name).all()
    
    # ========== MATCH OPERATIONS ==========
    
    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        """Hole Match nach ID"""
        return self.session.query(Match).filter(Match.id == match_id).first()
    
    def get_or_create_match(self, match_data: Dict[str, Any]) -> Match:
        """Hole oder erstelle Match"""
        match = self.session.query(Match).filter(Match.id == match_data['id']).first()
        
        if not match:
            # Stelle sicher, dass Teams existieren
            home_team = self.get_or_create_team(match_data['home_team'])
            away_team = self.get_or_create_team(match_data['away_team'])
            
            match = Match(
                id=match_data['id'],
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                date=datetime.fromisoformat(match_data['date'].replace('Z', '+00:00')),
                matchday=match_data['matchday'],
                season=match_data['season'],
                is_finished=match_data.get('is_finished', False)
            )
            
            # Ergebnis falls vorhanden
            if match_data.get('home_goals') is not None:
                match.home_goals = match_data['home_goals']
            if match_data.get('away_goals') is not None:
                match.away_goals = match_data['away_goals']
            
            self.session.add(match)
            logger.info(f"Created new match: {home_team.short_name} vs {away_team.short_name}")
        else:
            # Update falls sich Daten geändert haben
            updated = False
            
            if match_data.get('is_finished') and not match.is_finished:
                match.is_finished = True
                updated = True
            
            if match_data.get('home_goals') is not None and match.home_goals != match_data['home_goals']:
                match.home_goals = match_data['home_goals']
                updated = True
            
            if match_data.get('away_goals') is not None and match.away_goals != match_data['away_goals']:
                match.away_goals = match_data['away_goals']
                updated = True
            
            if updated:
                match.updated_at = datetime.utcnow()
                match.last_synced = datetime.utcnow()
                logger.info(f"Updated match: {match.id}")
        
        return match
    
    def get_matches_by_matchday(self, matchday: int, season: str = None) -> List[Match]:
        """Hole Matches nach Spieltag"""
        query = self.session.query(Match).filter(Match.matchday == matchday)
        if season:
            query = query.filter(Match.season == season)
        return query.order_by(Match.date).all()
    
    def get_finished_matches(self, limit: int = None) -> List[Match]:
        """Hole abgeschlossene Matches"""
        query = self.session.query(Match).filter(Match.is_finished == True)
        if limit:
            query = query.limit(limit)
        return query.order_by(desc(Match.date)).all()
    
    def get_matches_for_quality_analysis(self, max_matchday: int = 3) -> List[Match]:
        """Hole Matches für Qualitätsanalyse (abgeschlossen, bis Spieltag X)"""
        return self.session.query(Match).filter(
            and_(
                Match.is_finished == True,
                Match.matchday <= max_matchday,
                Match.home_goals.isnot(None),
                Match.away_goals.isnot(None)
            )
        ).order_by(Match.matchday, Match.date).all()
    
    # ========== PREDICTION OPERATIONS ==========
    
    def save_prediction(self, match_id: int, prediction_data: Dict[str, Any]) -> Prediction:
        """Speichere oder update Vorhersage"""
        prediction = self.session.query(Prediction).filter(Prediction.match_id == match_id).first()
        
        if not prediction:
            prediction = Prediction(match_id=match_id)
            self.session.add(prediction)
        
        # Update Prediction Data
        prediction.home_win_prob = prediction_data.get('home_win_prob', 0.0)
        prediction.draw_prob = prediction_data.get('draw_prob', 0.0)
        prediction.away_win_prob = prediction_data.get('away_win_prob', 0.0)
        prediction.predicted_score = prediction_data.get('predicted_score', '')
        prediction.predicted_home_goals = prediction_data.get('predicted_home_goals')
        prediction.predicted_away_goals = prediction_data.get('predicted_away_goals')
        
        # Form Factors
        if 'form_factors' in prediction_data:
            ff = prediction_data['form_factors']
            prediction.home_form = ff.get('home_form')
            prediction.away_form = ff.get('away_form')
            prediction.home_xg_last_6 = ff.get('home_xg_last_6')
            prediction.away_xg_last_6 = ff.get('away_xg_last_6')
        
        prediction.calculated_at = datetime.utcnow()
        
        return prediction
    
    def get_predictions_by_matchday(self, matchday: int) -> List[Prediction]:
        """Hole Vorhersagen nach Spieltag"""
        return self.session.query(Prediction).join(Match).filter(
            Match.matchday == matchday
        ).all()
    
    # ========== PREDICTION QUALITY OPERATIONS ==========
    
    def save_prediction_quality(self, match_id: int, quality_data: Dict[str, Any]) -> PredictionQuality:
        """Speichere Qualitäts-Analyse"""
        quality = self.session.query(PredictionQuality).filter(
            PredictionQuality.match_id == match_id
        ).first()
        
        if not quality:
            quality = PredictionQuality(match_id=match_id)
            self.session.add(quality)
        
        # Update Quality Data
        quality.predicted_score = quality_data['predicted_score']
        quality.actual_score = quality_data['actual_score']
        quality.predicted_home_win_prob = quality_data.get('predicted_home_win_prob')
        quality.predicted_draw_prob = quality_data.get('predicted_draw_prob')
        quality.predicted_away_win_prob = quality_data.get('predicted_away_win_prob')
        quality.hit_type = HitType(quality_data['hit_type'])
        quality.tendency_correct = quality_data['tendency_correct']
        quality.exact_score_correct = quality_data['exact_score_correct']
        quality.quality_score = quality_data.get('quality_score', 0.0)
        quality.calculated_at = datetime.utcnow()
        
        return quality
    
    def get_all_prediction_quality(self) -> List[PredictionQuality]:
        """Hole alle Qualitäts-Analysen"""
        return self.session.query(PredictionQuality).join(Match).order_by(
            Match.matchday, Match.date
        ).all()
    
    def get_quality_stats(self) -> Dict[str, Any]:
        """Berechne Qualitäts-Statistiken aus der DB"""
        total = self.session.query(PredictionQuality).count()
        
        if total == 0:
            return {
                "total_predictions": 0,
                "exact_matches": 0,
                "tendency_matches": 0,
                "misses": 0,
                "exact_match_rate": 0.0,
                "tendency_match_rate": 0.0,
                "overall_accuracy": 0.0,
                "quality_score": 0.0
            }
        
        exact_matches = self.session.query(PredictionQuality).filter(
            PredictionQuality.hit_type == HitType.exact_match
        ).count()
        
        tendency_matches = self.session.query(PredictionQuality).filter(
            PredictionQuality.hit_type == HitType.tendency_match
        ).count()
        
        misses = self.session.query(PredictionQuality).filter(
            PredictionQuality.hit_type == HitType.miss
        ).count()
        
        avg_quality_score = self.session.query(func.avg(PredictionQuality.quality_score)).scalar() or 0.0
        
        return {
            "total_predictions": total,
            "exact_matches": exact_matches,
            "tendency_matches": tendency_matches,
            "misses": misses,
            "exact_match_rate": round(exact_matches / total, 3),
            "tendency_match_rate": round(tendency_matches / total, 3),
            "overall_accuracy": round((exact_matches + tendency_matches) / total, 3),
            "quality_score": round(avg_quality_score, 3)
        }
    
    # ========== SYNC STATUS OPERATIONS ==========
    
    def update_sync_status(self, entity_type: str, success: bool = True, 
                          message: str = None, records_count: int = 0):
        """Update Synchronisation Status"""
        sync_status = self.session.query(SyncStatus).filter(
            SyncStatus.entity_type == entity_type
        ).first()
        
        if not sync_status:
            sync_status = SyncStatus(entity_type=entity_type)
            self.session.add(sync_status)
        
        sync_status.last_sync = datetime.utcnow()
        sync_status.last_sync_success = success
        sync_status.sync_message = message
        sync_status.records_synced = records_count
        
        return sync_status
    
    def get_sync_status(self, entity_type: str = None) -> List[SyncStatus]:
        """Hole Sync Status"""
        query = self.session.query(SyncStatus)
        if entity_type:
            query = query.filter(SyncStatus.entity_type == entity_type)
        return query.order_by(desc(SyncStatus.last_sync)).all()
    
    # ========== UTILITY METHODS ==========
    
    def get_current_season(self) -> Optional[str]:
        """Hole aktuelle Saison aus der DB"""
        result = self.session.query(Match.season).distinct().order_by(desc(Match.season)).first()
        return result[0] if result else None
    
    def get_latest_matchday(self) -> Optional[int]:
        """Hole höchsten Spieltag aus der DB"""
        result = self.session.query(func.max(Match.matchday)).scalar()
        return result
    
    def get_or_create_prediction(self, prediction_data: Dict[str, Any]) -> Prediction:
        """Erstelle oder hole eine Prediction"""
        try:
            # Suche existierende Prediction
            existing = self.session.query(Prediction).filter(
                Prediction.match_id == prediction_data['match_id']
            ).first()
            
            if existing:
                # Update existierende Prediction
                for key, value in prediction_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                return existing
            else:
                # Erstelle neue Prediction
                prediction = Prediction(**prediction_data)
                self.session.add(prediction)
                self.session.flush()  # Um die ID zu bekommen
                return prediction
                
        except Exception as e:
            logger.error(f"Error creating/updating prediction: {str(e)}")
            self.session.rollback()
            raise
    
    def get_or_create_prediction_quality(self, quality_data: Dict[str, Any]) -> PredictionQuality:
        """Erstelle oder hole eine PredictionQuality"""
        try:
            # Suche existierende PredictionQuality
            existing = self.session.query(PredictionQuality).filter(
                PredictionQuality.match_id == quality_data['match_id']
            ).first()
            
            if existing:
                # Update existierende Quality
                for key, value in quality_data.items():
                    if hasattr(existing, key):
                        if key == 'hit_type' and isinstance(value, str):
                            # Convert string to HitType enum
                            if value == 'exact_match':
                                value = HitType.exact_match
                            elif value == 'tendency_match':
                                value = HitType.tendency_match
                            else:
                                value = HitType.miss
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                return existing
            else:
                # Convert hit_type string to enum
                if 'hit_type' in quality_data and isinstance(quality_data['hit_type'], str):
                    hit_type_str = quality_data['hit_type']
                    if hit_type_str == 'exact_match':
                        quality_data['hit_type'] = HitType.exact_match
                    elif hit_type_str == 'tendency_match':
                        quality_data['hit_type'] = HitType.tendency_match
                    else:
                        quality_data['hit_type'] = HitType.miss
                
                # Erstelle neue PredictionQuality
                quality = PredictionQuality(**quality_data)
                self.session.add(quality)
                self.session.flush()  # Um die ID zu bekommen
                return quality
                
        except Exception as e:
            logger.error(f"Error creating/updating prediction quality: {str(e)}")
            self.session.rollback()
            raise
    
    def get_database_stats(self) -> Dict[str, int]:
        """Hole Database-Statistiken"""
        return {
            "teams": self.session.query(Team).count(),
            "matches": self.session.query(Match).count(),
            "finished_matches": self.session.query(Match).filter(Match.is_finished == True).count(),
            "predictions": self.session.query(Prediction).count(),
            "prediction_quality": self.session.query(PredictionQuality).count()
        }