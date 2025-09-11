import asyncio
import sys
import logging
import json
from app.services.openliga_client_debug import OpenLigaDBClient

# Konfiguriere das Logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

logger = logging.getLogger("team_id_test")

async def list_teams():
    """
    Ermittelt alle Teams und ihre IDs aus den Spieldaten
    """
    try:
        logger.info("=== Ermittle alle Team-IDs in der API ===")

        # Hole alle Spiele und extrahiere die Teams
        async with OpenLigaDBClient() as client:
            matches = await client.get_matches_by_league_season()
            
            if not matches:
                logger.error("Keine Spiele gefunden!")
                return
            
            teams = {}
            
            # Extrahiere alle Teams aus den Spielen
            for match in matches:
                home_team = match.get('team1', {})
                away_team = match.get('team2', {})
                
                if home_team and 'teamId' in home_team:
                    team_id = home_team['teamId']
                    team_name = home_team.get('teamName', 'Unbekannt')
                    teams[team_id] = team_name
                
                if away_team and 'teamId' in away_team:
                    team_id = away_team['teamId']
                    team_name = away_team.get('teamName', 'Unbekannt')
                    teams[team_id] = team_name
            
            # Sortiere nach Team-ID
            sorted_teams = {k: teams[k] for k in sorted(teams.keys())}
            
            # Gib alle Teams aus
            logger.info(f"Gefundene Teams: {len(sorted_teams)}")
            for team_id, team_name in sorted_teams.items():
                logger.info(f"Team-ID: {team_id}, Name: {team_name}")
            
            # Speichere als JSON für spätere Verwendung
            with open('teams.json', 'w') as f:
                json.dump(sorted_teams, f, indent=2)
                
            logger.info("Teams wurden in teams.json gespeichert")
            
    except Exception as e:
        logger.error(f"Fehler bei der Ermittlung der Team-IDs: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(list_teams())
