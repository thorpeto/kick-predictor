from datetime import datetime
from typing import Dict, List, Any, Optional
from app.models.schemas import Match, Team, MatchResult

class DataConverter:
    """
    Konvertiert OpenLigaDB-Daten in unser Datenmodell
    """
    
    @staticmethod
    def convert_team(team_data: Dict[str, Any]) -> Team:
        """
        Konvertiert Team-Daten von OpenLigaDB in unser Team-Modell
        """
        return Team(
            id=team_data.get('teamId', 0),
            name=team_data.get('teamName', ''),
            short_name=team_data.get('shortName', ''),
            logo_url=team_data.get('teamIconUrl', None)
        )
    
    @staticmethod
    def convert_match(match_data: Dict[str, Any]) -> Match:
        """
        Konvertiert Spiel-Daten von OpenLigaDB in unser Match-Modell
        """
        match_datetime = match_data.get('matchDateTime', '')
        date = datetime.fromisoformat(match_datetime.replace('Z', '+00:00')) if match_datetime else datetime.now()
        
        return Match(
            id=match_data.get('matchID', 0),
            home_team=DataConverter.convert_team(match_data.get('team1', {})),
            away_team=DataConverter.convert_team(match_data.get('team2', {})),
            date=date,
            matchday=match_data.get('matchday', 0),
            season=match_data.get('leagueName', '')
        )
    
    @staticmethod
    def convert_match_result(match_data: Dict[str, Any]) -> Optional[MatchResult]:
        """
        Konvertiert Spiel-Daten mit Ergebnis von OpenLigaDB in unser MatchResult-Modell
        """
        # Prüfe, ob das Spiel bereits beendet ist
        if not match_data.get('matchIsFinished', False):
            return None
            
        match = DataConverter.convert_match(match_data)
        
        # Ergebnisse
        results = match_data.get('matchResults', [])
        final_result = next((r for r in results if r.get('resultTypeID') == 2), None)
        
        if not final_result:
            return None
            
        # In der OpenLigaDB API sind keine xG und Ballbesitz-Daten verfügbar
        # Wir müssten diese aus einer anderen Quelle beziehen oder schätzen
        # Für dieses Beispiel verwenden wir Platzhalter-Werte
        estimated_home_xg = final_result.get('pointsTeam1', 0) * 1.2  # Einfache Schätzung
        estimated_away_xg = final_result.get('pointsTeam2', 0) * 1.2
        
        return MatchResult(
            match=match,
            home_goals=final_result.get('pointsTeam1', 0),
            away_goals=final_result.get('pointsTeam2', 0),
            home_xg=estimated_home_xg,
            away_xg=estimated_away_xg,
            home_possession=55.0,  # Platzhalter
            away_possession=45.0   # Platzhalter
        )
