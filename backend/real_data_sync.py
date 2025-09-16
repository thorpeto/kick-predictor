"""
Vollständige Synchronisation mit echten Bundesliga-Daten
Saison 2024/25 (Parameter "2025") - aktuelle Saison mit 3 gespielten Spieltagen
Saison 2023/24 (Parameter "2024") - vorherige Saison für historische Daten
"""
import sqlite3
import asyncio
import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataSync:
    def __init__(self, db_path: str = "/workspaces/kick-predictor/backend/kick_predictor_final.db"):
        self.db_path = db_path
        self.api_base = "https://api.openligadb.de/getmatchdata"
        
    def get_db_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Erstelle erweiterte Datenbank-Struktur für echte Daten"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Erweiterte Teams-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams_real (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                short_name TEXT NOT NULL,
                icon_url TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Erweiterte Matches-Tabelle mit echten Daten
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches_real (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER UNIQUE NOT NULL,
                season TEXT NOT NULL,
                matchday INTEGER NOT NULL,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                home_team_name TEXT NOT NULL,
                away_team_name TEXT NOT NULL,
                match_date TEXT NOT NULL,
                is_finished BOOLEAN NOT NULL,
                home_goals INTEGER,
                away_goals INTEGER,
                home_goals_ht INTEGER,
                away_goals_ht INTEGER,
                goals_json TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabelle für aktuelle Spieltag-Info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS season_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season TEXT NOT NULL,
                current_matchday INTEGER NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Datenbank-Struktur initialisiert")

    async def fetch_teams_from_season(self, season: str = "2025") -> List[Dict]:
        """Hole Teams aus einer Saison"""
        url = f"{self.api_base}/bl1/{season}/1"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                matches_data = response.json()
                
                teams = {}
                for match in matches_data:
                    # Team 1
                    team1 = match.get('team1', {})
                    if team1.get('teamId'):
                        teams[team1['teamId']] = {
                            'teamId': team1['teamId'],
                            'name': team1['teamName'],
                            'shortName': team1['shortName'],
                            'iconUrl': team1.get('teamIconUrl', '')
                        }
                    
                    # Team 2
                    team2 = match.get('team2', {})
                    if team2.get('teamId'):
                        teams[team2['teamId']] = {
                            'teamId': team2['teamId'],
                            'name': team2['teamName'],
                            'shortName': team2['shortName'],
                            'iconUrl': team2.get('teamIconUrl', '')
                        }
                
                return list(teams.values())
                
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Teams für Saison {season}: {e}")
                return []

    async def fetch_matches_from_season(self, season: str = "2025", max_matchday: Optional[int] = None) -> List[Dict]:
        """Hole alle Matches einer Saison bis zu einem bestimmten Spieltag"""
        all_matches = []
        
        # Für aktuelle Saison: Spieltage 1-4 (3 gespielt + 1 kommend)
        if season == "2025":
            matchdays = range(1, 5)  # Spieltage 1, 2, 3, 4
        else:
            # Für vorherige Saison: nur die letzten 11 Spieltage (24-34)
            matchdays = range(24, 35)  # Spieltage 24-34 (11 Spieltage)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for matchday in matchdays:
                url = f"{self.api_base}/bl1/{season}/{matchday}"
                try:
                    logger.info(f"Lade Spieltag {matchday} der Saison {season}...")
                    response = await client.get(url)
                    response.raise_for_status()
                    matches = response.json()
                    
                    for match in matches:
                        match_data = {
                            'matchId': match.get('matchID'),
                            'season': season,
                            'matchday': matchday,
                            'homeTeamId': match.get('team1', {}).get('teamId'),
                            'awayTeamId': match.get('team2', {}).get('teamId'),
                            'homeTeamName': match.get('team1', {}).get('teamName'),
                            'awayTeamName': match.get('team2', {}).get('teamName'),
                            'matchDate': match.get('matchDateTime'),
                            'isFinished': match.get('matchIsFinished', False),
                            'goals': match.get('goals', [])
                        }
                        
                        # Extrahiere Tore falls Spiel beendet
                        if match_data['isFinished'] and match.get('matchResults'):
                            final_result = None
                            ht_result = None
                            
                            for result in match.get('matchResults', []):
                                if result.get('resultTypeID') == 2:  # Endergebnis
                                    final_result = result
                                elif result.get('resultTypeID') == 1:  # Halbzeitergebnis
                                    ht_result = result
                            
                            if final_result:
                                match_data['homeGoals'] = final_result.get('pointsTeam1', 0)
                                match_data['awayGoals'] = final_result.get('pointsTeam2', 0)
                            
                            if ht_result:
                                match_data['homeGoalsHT'] = ht_result.get('pointsTeam1', 0)
                                match_data['awayGoalsHT'] = ht_result.get('pointsTeam2', 0)
                        
                        all_matches.append(match_data)
                    
                    # Kleine Pause zwischen Requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Fehler beim Abrufen von Spieltag {matchday}, Saison {season}: {e}")
                    continue
        
        logger.info(f"Insgesamt {len(all_matches)} Matches aus Saison {season} geladen")
        return all_matches

    def save_teams_to_db(self, teams: List[Dict]):
        """Speichere Teams in Datenbank"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        for team in teams:
            cursor.execute("""
                INSERT OR REPLACE INTO teams_real 
                (team_id, name, short_name, icon_url, synced_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                team['teamId'],
                team['name'],
                team['shortName'],
                team.get('iconUrl', '')
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"{len(teams)} Teams in Datenbank gespeichert")

    def save_matches_to_db(self, matches: List[Dict]):
        """Speichere Matches in Datenbank"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        saved_count = 0
        for match in matches:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO matches_real 
                    (match_id, season, matchday, home_team_id, away_team_id, 
                     home_team_name, away_team_name, match_date, is_finished,
                     home_goals, away_goals, home_goals_ht, away_goals_ht, goals_json, synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    match['matchId'],
                    match['season'],
                    match['matchday'],
                    match['homeTeamId'],
                    match['awayTeamId'],
                    match['homeTeamName'],
                    match['awayTeamName'],
                    match['matchDate'],
                    match['isFinished'],
                    match.get('homeGoals'),
                    match.get('awayGoals'),
                    match.get('homeGoalsHT'),
                    match.get('awayGoalsHT'),
                    json.dumps(match.get('goals', []))
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Fehler beim Speichern von Match {match.get('matchId')}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"{saved_count} Matches in Datenbank gespeichert")

    def update_season_info(self):
        """Aktualisiere Saison-Informationen"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Bestimme aktuellen Spieltag basierend auf gespielten Matches
        cursor.execute("""
            SELECT MAX(matchday) 
            FROM matches_real 
            WHERE season = '2025' AND is_finished = 1
        """)
        result = cursor.fetchone()
        current_matchday = result[0] if result and result[0] else 3
        
        # Da wir 3 Spieltage gespielt haben, ist der nächste Spieltag der 4.
        next_matchday = current_matchday + 1
        
        cursor.execute("""
            INSERT OR REPLACE INTO season_info 
            (id, season, current_matchday, last_updated)
            VALUES (1, '2025', ?, CURRENT_TIMESTAMP)
        """, (next_matchday,))
        
        conn.commit()
        conn.close()
        logger.info(f"Aktueller Spieltag: {next_matchday} (basierend auf {current_matchday} gespielten Spieltagen)")

    async def sync_all_real_data(self):
        """Vollständige Synchronisation aller echten Daten"""
        logger.info("🚀 Starte vollständige Synchronisation mit echten Bundesliga-Daten...")
        
        # 1. Datenbank initialisieren
        self.init_database()
        
        # 2. Teams aus aktueller Saison holen
        logger.info("📋 Lade Teams der Saison 2024/25...")
        teams = await self.fetch_teams_from_season("2025")
        if teams:
            self.save_teams_to_db(teams)
        
        # 3. Matches aus aktueller Saison (Spieltage 1-4: 3 gespielt + 1 kommend)
        logger.info("⚽ Lade Matches der aktuellen Saison 2024/25 (Spieltage 1-4)...")
        current_matches = await self.fetch_matches_from_season("2025")
        if current_matches:
            self.save_matches_to_db(current_matches)
        
        # 4. Matches aus vorheriger Saison (nur die letzten 11 Spieltage für Form-Berechnung)
        logger.info("📅 Lade die letzten 11 Spieltage der Saison 2023/24 (Spieltage 24-34)...")
        previous_matches = await self.fetch_matches_from_season("2024")
        if previous_matches:
            self.save_matches_to_db(previous_matches)
        
        # 5. Saison-Info aktualisieren
        self.update_season_info()
        
        # 6. Statistiken
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM teams_real")
        teams_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2025'")
        current_matches_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2024'")
        previous_matches_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2025' AND is_finished = 1")
        finished_matches_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info("✅ Synchronisation abgeschlossen!")
        logger.info(f"📊 Statistiken:")
        logger.info(f"   - Teams: {teams_count}")
        logger.info(f"   - Matches 2024/25: {current_matches_count}")
        logger.info(f"   - Matches 2023/24: {previous_matches_count}")
        logger.info(f"   - Beendete Matches 2024/25: {finished_matches_count}")
        
        return {
            'teams': teams_count,
            'current_season_matches': current_matches_count,
            'previous_season_matches': previous_matches_count,
            'finished_matches': finished_matches_count
        }

async def main():
    """Führe die vollständige Synchronisation aus"""
    sync = RealDataSync()
    result = await sync.sync_all_real_data()
    print("🎉 Synchronisation erfolgreich!")
    print(f"Ergebnis: {result}")

if __name__ == "__main__":
    asyncio.run(main())