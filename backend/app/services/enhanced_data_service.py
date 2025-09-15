"""
Enhanced DataService mit SQLite Database Integration
Ersetzt den ursprünglichen DataService für deutlich bessere Performance
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from app.models.schemas import (
    MatchResult, Team, TableEntry, MatchdayInfo, Match, Prediction
)
from app.interfaces.data_interface import DataServiceInterface

logger = logging.getLogger(__name__)

class EnhancedDataService(DataServiceInterface):
    def __init__(self):
        self.league = "bl1"
        self.season = "2025"
        
        # Cache für Performance (kurzzeitig)
        self._table_cache: Optional[List[TableEntry]] = None
        self._table_cache_expiry: Optional[datetime] = None
        self._quality_cache: Optional[Dict] = None
        self._quality_cache_expiry: Optional[datetime] = None
        self._matchday_info_cache: Optional[MatchdayInfo] = None
        self._matchday_info_cache_expiry: Optional[datetime] = None
        
        # Prediction cache like original DataService
        self._predictions_cache: Dict[str, Dict] = {}
        self._cache_expiry: Dict[str, datetime] = {}
    
    async def get_current_table(self) -> List[TableEntry]:
        """
        Hole aktuelle Tabelle - für jetzt fallback zur API
        """
        # Cache check
        if self._is_table_cache_valid():
            logger.info("Table Cache Hit")
            return self._table_cache or []
        
        # Fallback zur Original-API-Implementierung
        return await self._fallback_to_api_table()
    
    async def get_prediction_quality(self) -> Dict:
        """
        Hole Prediction Quality aus der Datenbank, mit API-Fallback
        """
        # Cache check
        if self._is_quality_cache_valid():
            logger.info("Quality Cache Hit")
            return self._quality_cache or {}
        
        try:
            # Versuche zuerst Daten aus der Datenbank zu holen
            from app.database.database_service import DatabaseService
            from app.database.models import PredictionQuality, Prediction, Match, Team
            from sqlalchemy.orm import aliased
            
            with DatabaseService() as db:
                # Aliases für Teams
                home_team = aliased(Team)
                away_team = aliased(Team)
                
                # Hole alle PredictionQuality-Einträge mit zugehörigen Daten
                quality_entries = db.session.query(
                    PredictionQuality, Prediction, Match, home_team, away_team
                ).join(
                    Match, PredictionQuality.match_id == Match.id
                ).join(
                    Prediction, Prediction.match_id == Match.id
                ).join(
                    home_team, Match.home_team_id == home_team.id
                ).join(
                    away_team, Match.away_team_id == away_team.id
                ).all()
                
                # Wenn Daten in der Datenbank vorhanden sind
                if quality_entries:
                    entries = []
                    stats = {
                        "total_predictions": 0,
                        "exact_matches": 0,
                        "tendency_matches": 0,
                        "misses": 0
                    }
                    
                    for quality, prediction, match, home_team_obj, away_team_obj in quality_entries:
                        entry = {
                            "match": {
                                "id": match.id,
                                "home_team": {
                                    "id": home_team_obj.id,
                                    "name": home_team_obj.name,
                                    "short_name": home_team_obj.short_name,
                                    "logo_url": home_team_obj.logo_url
                                },
                                "away_team": {
                                    "id": away_team_obj.id,
                                    "name": away_team_obj.name,
                                    "short_name": away_team_obj.short_name,
                                    "logo_url": away_team_obj.logo_url
                                },
                                "date": match.date.isoformat() if match.date else None,
                                "matchday": match.matchday,
                                "season": match.season
                            },
                            "predicted_score": f"{prediction.predicted_home_goals}:{prediction.predicted_away_goals}",
                            "actual_score": quality.actual_score,
                            "predicted_home_win_prob": prediction.home_win_prob,
                            "predicted_draw_prob": prediction.draw_prob,
                            "predicted_away_win_prob": prediction.away_win_prob,
                            "hit_type": quality.hit_type.value if quality.hit_type else "miss",
                            "tendency_correct": quality.tendency_correct,
                            "exact_score_correct": quality.exact_score_correct
                        }
                        entries.append(entry)
                        
                        # Update statistics
                        stats["total_predictions"] += 1
                        if quality.hit_type and quality.hit_type.value == "exact_match":
                            stats["exact_matches"] += 1
                        elif quality.hit_type and quality.hit_type.value == "tendency_match":
                            stats["tendency_matches"] += 1
                        else:
                            stats["misses"] += 1
                    
                    # Calculate rates
                    total = stats["total_predictions"]
                    if total > 0:
                        stats["exact_match_rate"] = stats["exact_matches"] / total
                        stats["tendency_match_rate"] = stats["tendency_matches"] / total
                        stats["overall_accuracy"] = (stats["exact_matches"] + stats["tendency_matches"]) / total
                        stats["quality_score"] = (stats["exact_matches"] * 1.0 + stats["tendency_matches"] * 0.5) / total
                    else:
                        stats["exact_match_rate"] = 0.0
                        stats["tendency_match_rate"] = 0.0
                        stats["overall_accuracy"] = 0.0
                        stats["quality_score"] = 0.0
                    
                    result = {
                        "entries": entries,
                        "stats": stats,
                        "processed_matches": len(entries),
                        "cached_at": datetime.now().isoformat(),
                        "source": "database"
                    }
                    
                    # Cache das Ergebnis
                    self._quality_cache = result
                    self._quality_cache_expiry = datetime.now() + timedelta(minutes=15)
                    
                    logger.info(f"Loaded prediction quality from database: {len(entries)} entries")
                    return result
                
        except Exception as db_error:
            logger.warning(f"Database query failed, falling back to API: {str(db_error)}")
        
        # Fallback zur Original-API-Implementierung
        logger.info("Falling back to API for prediction quality")
        result = await self._fallback_to_api_quality()
        if isinstance(result, dict):
            result["source"] = "api_fallback"
        return result
    
    async def get_current_matchday_info(self) -> MatchdayInfo:
        """
        Hole Spieltag-Info - für jetzt fallback zur API
        """
        # Cache check
        if self._is_matchday_info_cache_valid():
            return self._matchday_info_cache or MatchdayInfo(current_matchday=1, next_matchday=2, predictions_available_until=3, season="2025")
        
        # Fallback zur Original-API-Implementierung
        return await self._fallback_to_api_matchday_info()
    
    async def get_team_form(self, team_id: int) -> float:
        """Get team form - fallback to API"""
        return await self._fallback_to_api_team_form(team_id)
    
    async def get_team_matches(self, team_id: int) -> List[MatchResult]:
        """Get team matches - fallback to API"""
        return await self._fallback_to_api_team_matches(team_id)
    
    # Additional methods for PredictionService compatibility
    async def get_last_n_matches(self, team_id: int, n: int = 14) -> List[MatchResult]:
        """Hole die letzten n Spiele"""
        return await self._fallback_to_api_last_n_matches(team_id, n)
    
    async def get_matches_by_matchday(self, matchday: int) -> List[Match]:
        """Hole Spiele für einen Spieltag"""
        return await self._fallback_to_api_matches_by_matchday(matchday)
    
    def _get_cached_predictions(self, matchday: int) -> Optional[List[Prediction]]:
        """Hole gecachte Predictions"""
        cache_key = f"matchday_{matchday}"
        if cache_key in self._predictions_cache:
            if cache_key in self._cache_expiry:
                if datetime.now() < self._cache_expiry[cache_key]:
                    logger.info(f"Cache hit for matchday {matchday}")
                    return self._predictions_cache[cache_key].get('predictions')
                else:
                    # Cache expired
                    del self._predictions_cache[cache_key]
                    del self._cache_expiry[cache_key]
        return None
    
    def _cache_predictions(self, matchday: int, predictions: List[Prediction]) -> None:
        """Cache Predictions"""
        cache_key = f"matchday_{matchday}"
        self._predictions_cache[cache_key] = {
            'predictions': predictions,
            'cached_at': datetime.now()
        }
        # Cache für 30 Minuten
        self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=30)
        logger.info(f"Cached predictions for matchday {matchday}")
    
    # ========== CACHE MANAGEMENT ==========
    
    def _is_table_cache_valid(self) -> bool:
        if not self._table_cache or not self._table_cache_expiry:
            return False
        return datetime.now() < self._table_cache_expiry
    
    def _cache_table_data(self, data: List[TableEntry]) -> None:
        self._table_cache = data
        self._table_cache_expiry = datetime.now() + timedelta(hours=1)  # 1 Stunde Cache
    
    def _is_quality_cache_valid(self) -> bool:
        if not self._quality_cache or not self._quality_cache_expiry:
            return False
        return datetime.now() < self._quality_cache_expiry
    
    def _cache_quality_data(self, data: Dict) -> None:
        self._quality_cache = data
        self._quality_cache_expiry = datetime.now() + timedelta(hours=6)  # 6 Stunden Cache
    
    def _is_matchday_info_cache_valid(self) -> bool:
        if not self._matchday_info_cache or not self._matchday_info_cache_expiry:
            return False
        return datetime.now() < self._matchday_info_cache_expiry
    
    def _cache_matchday_info(self, data: MatchdayInfo) -> None:
        self._matchday_info_cache = data
        self._matchday_info_cache_expiry = datetime.now() + timedelta(minutes=30)  # 30 Min Cache
    
    # ========== FALLBACK METHODS ==========
    
    async def _fallback_to_api_table(self) -> List[TableEntry]:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        # Umgehung der Interface-Implementierung durch direkte Instanziierung
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_current_table()
    
    async def _fallback_to_api_quality(self) -> Dict:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_prediction_quality()
    
    async def _fallback_to_api_matchday_info(self) -> MatchdayInfo:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_current_matchday_info()
    
    async def _fallback_to_api_team_form(self, team_id: int) -> float:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_team_form(team_id)
    
    async def _fallback_to_api_team_matches(self, team_id: int) -> List[MatchResult]:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_team_matches(team_id)
    
    async def _fallback_to_api_last_n_matches(self, team_id: int, n: int = 14) -> List[MatchResult]:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_last_n_matches(team_id, n)
    
    async def _fallback_to_api_matches_by_matchday(self, matchday: int) -> List[Match]:
        """Fallback zur Original-API-Implementierung"""
        from app.services.data_service import DataService as OriginalDataService
        original_service = OriginalDataService.__new__(OriginalDataService)
        original_service.__dict__.update({
            'league': 'bl1',
            'season': '2025',
            '_predictions_cache': {},
            '_cache_expiry': {},
            '_cache_expiry': {},
            '_quality_cache': None,
            '_quality_cache_expiry': None
        })
        return await original_service.get_matches_by_matchday(matchday)