import httpx
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OpenLigaDBClient:
    """
    Client für die OpenLigaDB API, um Bundesliga-Daten abzurufen
    """
    BASE_URL = "https://api.openligadb.de/getmatchdata"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()
    
    async def get_matches_by_league_season(self, league: str = "bl1", season: str = "2025") -> List[Dict[str, Any]]:
        """
        Holt alle Spiele einer Liga in einer Saison
        
        Args:
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            season: Saison (z.B. "2025" für 2025/2026)
            
        Returns:
            Liste von Spielen
        """
        url = f"{self.BASE_URL}/{league}/{season}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Fehler beim Abrufen der Spiele: {str(e)}")
            return []
    
    async def get_matches_by_matchday(self, league: str = "bl1", season: str = "2025", matchday: int = 1) -> List[Dict[str, Any]]:
        """
        Holt alle Spiele eines Spieltags
        
        Args:
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            season: Saison (z.B. "2025" für 2025/2026)
            matchday: Spieltag (1-34)
            
        Returns:
            Liste von Spielen
        """
        url = f"{self.BASE_URL}/{league}/{season}/{matchday}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Fehler beim Abrufen der Spiele für Spieltag {matchday}: {str(e)}")
            return []
    
    async def get_next_matchday(self, league: str = "bl1", season: str = "2025") -> List[Dict[str, Any]]:
        """
        Bestimmt den nächsten Spieltag und holt dessen Spiele
        
        Args:
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            season: Saison (z.B. "2025" für 2025/2026)
            
        Returns:
            Liste von Spielen des nächsten Spieltags
        """
        # Da wir wissen, dass der nächste Spieltag der dritte ist, rufen wir diesen direkt ab
        next_matchday = 3
        logger.info(f"Abrufen des Spieltags {next_matchday} für die Saison {season}")
        return await self.get_matches_by_matchday(league, season, next_matchday)
    
    async def get_team_matches(self, team_id: int, league: str = "bl1", season: str = "2025") -> List[Dict[str, Any]]:
        """
        Holt alle Spiele eines Teams
        
        Args:
            team_id: Team-ID
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            season: Saison (z.B. "2025" für 2025/2026)
            
        Returns:
            Liste von Spielen des Teams
        """
        all_matches = await self.get_matches_by_league_season(league, season)
        
        # Filtere nach Team-ID
        team_matches = [
            match for match in all_matches 
            if match.get('team1', {}).get('teamId') == team_id or match.get('team2', {}).get('teamId') == team_id
        ]
        
        # Sortiere nach Datum
        team_matches.sort(key=lambda m: datetime.fromisoformat(m.get('matchDateTime', '').replace('Z', '+00:00')))
        
        return team_matches
    
    async def get_past_matches(self, team_id: int, league: str = "bl1", season: str = "2025") -> List[Dict[str, Any]]:
        """
        Holt alle vergangenen Spiele eines Teams
        
        Args:
            team_id: Team-ID
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            season: Saison (z.B. "2025" für 2025/2026)
            
        Returns:
            Liste aller vergangenen Spiele des Teams
        """
        team_matches = await self.get_team_matches(team_id, league, season)
        
        # Aktuelles Datum
        now = datetime.now()
        
        # Filtere nach vergangenen Spielen
        past_matches = [
            match for match in team_matches 
            if datetime.fromisoformat(match.get('matchDateTime', '').replace('Z', '+00:00')) < now
        ]
        
        # Sortiere nach Datum (älteste zuerst)
        past_matches.sort(
            key=lambda m: datetime.fromisoformat(m.get('matchDateTime', '').replace('Z', '+00:00'))
        )
        
        return past_matches
    
    async def get_last_n_matches(self, team_id: int, n: int = 6, league: str = "bl1", season: str = "2025") -> List[Dict[str, Any]]:
        """
        Holt die letzten n Spiele eines Teams
        
        Args:
            team_id: Team-ID
            n: Anzahl der letzten Spiele (wird als Obergrenze verwendet)
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            season: Saison (z.B. "2025" für 2025/2026)
            
        Returns:
            Liste der letzten Spiele des Teams (maximal n)
        """
        team_matches = await self.get_team_matches(team_id, league, season)
        
        # Aktuelles Datum
        now = datetime.now()
        
        # Filtere nach vergangenen Spielen
        past_matches = [
            match for match in team_matches 
            if datetime.fromisoformat(match.get('matchDateTime', '').replace('Z', '+00:00')) < now
        ]
        
        # Wenn keine vergangenen Spiele gefunden wurden, gebe leere Liste zurück
        if not past_matches:
            logger.warning(f"Keine vergangenen Spiele für Team-ID {team_id} gefunden.")
            return []
        
        # Sortiere nach Datum (neueste zuerst) und nimm maximal n Spiele
        past_matches.sort(
            key=lambda m: datetime.fromisoformat(m.get('matchDateTime', '').replace('Z', '+00:00')), 
            reverse=True
        )
        
        # Nimm die letzten n Spiele oder alle, wenn weniger als n vorhanden sind
        return past_matches[:n] if len(past_matches) > n else past_matches
        
    async def get_matches_across_seasons(self, team_id: int, n: int = 14, league: str = "bl1", current_season: str = "2025", previous_season: str = "2024") -> List[Dict[str, Any]]:
        """
        Holt Spiele eines Teams über zwei Saisons hinweg
        
        Args:
            team_id: Team-ID
            n: Anzahl der Spiele, die zurückgegeben werden sollen
            league: Ligakürzel (bl1 = 1. Bundesliga, bl2 = 2. Bundesliga)
            current_season: Aktuelle Saison (z.B. "2025" für 2025/2026)
            previous_season: Vorherige Saison (z.B. "2024" für 2024/2025)
            
        Returns:
            Liste der Spiele des Teams aus beiden Saisons (maximal n)
        """
        # Hole Spiele aus aktueller Saison
        current_matches = await self.get_team_matches(team_id, league, current_season)
        
        # Hole Spiele aus vorheriger Saison
        previous_matches = await self.get_team_matches(team_id, league, previous_season)
        
        # Kombiniere die Spiele
        all_matches = current_matches + previous_matches
        
        # Aktuelles Datum
        now = datetime.now()
        
        # Filtere nach vergangenen Spielen
        past_matches = [
            match for match in all_matches 
            if datetime.fromisoformat(match.get('matchDateTime', '').replace('Z', '+00:00')) < now
        ]
        
        # Sortiere nach Datum (neueste zuerst)
        past_matches.sort(
            key=lambda m: datetime.fromisoformat(m.get('matchDateTime', '').replace('Z', '+00:00')), 
            reverse=True
        )
        
        # Nimm die letzten n Spiele oder alle, wenn weniger als n vorhanden sind
        return past_matches[:n] if len(past_matches) > n else past_matches
