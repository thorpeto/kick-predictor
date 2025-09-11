import asyncio
import sys
import logging
from app.services.openliga_client_debug import OpenLigaDBClient

# Konfiguriere das Logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

logger = logging.getLogger("api_test")

async def test_api_endpoints():
    """
    Test der API-Endpunkte zum Abrufen von Spieldaten
    """
    try:
        logger.info("=== Start der API-Tests ===")

        # Test: nächster Spieltag
        logger.info("Test 1: Nächster Spieltag")
        async with OpenLigaDBClient() as client:
            matches = await client.get_next_matchday()
            logger.info(f"Anzahl der Spiele am nächsten Spieltag: {len(matches)}")
        
        # Test: Spiele eines Teams
        team_id = 1  # FC Bayern München
        logger.info(f"Test 2: Alle Spiele von Team {team_id}")
        async with OpenLigaDBClient() as client:
            matches = await client.get_team_matches(team_id)
            logger.info(f"Anzahl der Spiele für Team {team_id}: {len(matches)}")
        
        # Test: Vergangene Spiele eines Teams
        logger.info(f"Test 3: Vergangene Spiele von Team {team_id}")
        async with OpenLigaDBClient() as client:
            matches = await client.get_past_matches(team_id)
            logger.info(f"Anzahl der vergangenen Spiele für Team {team_id}: {len(matches)}")
        
        # Test: Letzte 6 Spiele eines Teams
        logger.info(f"Test 4: Letzte 6 Spiele von Team {team_id}")
        async with OpenLigaDBClient() as client:
            matches = await client.get_last_n_matches(team_id, 6)
            logger.info(f"Anzahl der letzten Spiele für Team {team_id}: {len(matches)}")
        
        logger.info("=== API-Tests erfolgreich abgeschlossen ===")
    except Exception as e:
        logger.error(f"Fehler bei den API-Tests: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
