"""
Interface für DataService Kompatibilität
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.models.schemas import (
    TableEntry, MatchdayInfo, MatchResult, Match, Prediction
)

class DataServiceInterface(ABC):
    """Interface für alle DataService Implementierungen"""
    
    @abstractmethod
    async def get_current_table(self) -> List[TableEntry]:
        """Hole aktuelle Tabelle"""
        pass
    
    @abstractmethod
    async def get_team_form(self, team_id: int) -> float:
        """Hole Team-Form"""
        pass
    
    @abstractmethod
    async def get_team_matches(self, team_id: int) -> List[MatchResult]:
        """Hole Team-Matches"""
        pass
    
    @abstractmethod
    async def get_prediction_quality(self) -> Dict:
        """Hole Prediction Quality"""
        pass
    
    @abstractmethod
    async def get_current_matchday_info(self) -> MatchdayInfo:
        """Hole Spieltag-Info"""
        pass
    
    # Additional methods needed by PredictionService
    async def get_last_n_matches(self, team_id: int, n: int = 14) -> List[MatchResult]:
        """Hole die letzten n Spiele - optional implementation"""
        return []
    
    async def get_matches_by_matchday(self, matchday: int) -> List[Match]:
        """Hole Spiele für einen Spieltag - optional implementation"""
        return []
    
    def _get_cached_predictions(self, matchday: int) -> Optional[List[Prediction]]:
        """Hole gecachte Predictions - optional implementation"""
        return None
    
    def _cache_predictions(self, matchday: int, predictions: List[Prediction]) -> None:
        """Cache Predictions - optional implementation"""
        pass