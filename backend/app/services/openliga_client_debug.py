import httpx
from typing import Dict, List, Optional, Any
import logging
import sys
from datetime import datetime, timedelta
import traceback

# Konfiguriere das Logging für detailliertere Ausgaben
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

logger = logging.getLogger("openliga_client_debug")

class OpenLigaDBClient:
    """
    Client für die OpenLigaDB API, um Bundesliga-Daten abzurufen
    """
    BASE_URL = "https://api.openligadb.de/getmatchdata"
    
    def __init__(self):
        # Reduziertes Timeout, um Hängen zu vermeiden
        self.client = httpx.AsyncClient(timeout=5.0)
        logger.debug("OpenLigaDBClient initialisiert mit Timeout von 5 Sekunden")
    
    async def __aenter__(self):
        logger.debug("OpenLigaDBClient Context Manager gestartet")
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        logger.debug("OpenLigaDBClient Context Manager wird beendet")
        await self.client.aclose()
        logger.debug("Client geschlossen")
    
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
        logger.debug(f"API-Anfrage: {url}")
        try:
            logger.debug("Sende Anfrage...")
            response = await self.client.get(url)
            logger.debug(f"Antwort erhalten: Status {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Anzahl der abgerufenen Spiele: {len(data)}")
            return data
        except httpx.HTTPError as e:
            logger.error(f"HTTP-Fehler beim Abrufen der Spiele: {str(e)}")
            # Stack Trace ausgeben
            logger.error(traceback.format_exc())
            return []
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Abrufen der Spiele: {str(e)}")
            logger.error(traceback.format_exc())
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
        logger.debug(f"API-Anfrage: {url}")
        try:
            logger.debug("Sende Anfrage...")
            response = await self.client.get(url)
            logger.debug(f"Antwort erhalten: Status {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Anzahl der abgerufenen Spiele: {len(data)}")
            return data
        except httpx.HTTPError as e:
            logger.error(f"HTTP-Fehler beim Abrufen der Spiele für Spieltag {matchday}: {str(e)}")
            logger.error(traceback.format_exc())
            return []
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Abrufen der Spiele für Spieltag {matchday}: {str(e)}")
            logger.error(traceback.format_exc())
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
        logger.debug(f"Rufe Spiele für Team {team_id} ab...")
        all_matches = await self.get_matches_by_league_season(league, season)
        
        # Filtere nach Team-ID
        team_matches = [
            match for match in all_matches 
            if match.get('team1', {}).get('teamId') == team_id or match.get('team2', {}).get('teamId') == team_id
        ]
        
        logger.debug(f"Gefundene Spiele für Team {team_id}: {len(team_matches)}")
        
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
        logger.debug(f"Rufe vergangene Spiele für Team {team_id} ab...")
        team_matches = await self.get_team_matches(team_id, league, season)
        
        # Aktuelles Datum
        now = datetime.now()
        logger.debug(f"Aktuelles Datum: {now}")
        
        # Filtere nach vergangenen Spielen
        past_matches = [
            match for match in team_matches 
            if datetime.fromisoformat(match.get('matchDateTime', '').replace('Z', '+00:00')) < now
        ]
        
        logger.debug(f"Vergangene Spiele für Team {team_id}: {len(past_matches)}")
        
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
        logger.debug(f"Rufe die letzten {n} Spiele für Team {team_id} ab...")
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
        result = past_matches[:n] if len(past_matches) > n else past_matches
        logger.debug(f"Zurückgegebene Spiele: {len(result)}")
        return result
