import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models.schemas import Match, MatchResult, Prediction, FormFactor, Team, TableEntry
from app.services.openliga_client import OpenLigaDBClient
from app.services.data_converter import DataConverter
import logging

logger = logging.getLogger(__name__)

class DataService:
    """
    Service zum Laden und Verarbeiten der Bundesliga-Daten
    """
    
    def __init__(self):
        # Initialisierung des OpenLigaDB-Clients
        self.league = "bl1"  # 1. Bundesliga
        self.season = "2025"  # Saison 2025/2026
    
    async def get_team_matches(self, team_id: int) -> List[MatchResult]:
        """
        Holt alle vergangenen Spiele eines Teams
        """
        try:
            async with OpenLigaDBClient() as client:
                # Hole alle Spiele des Teams
                matches_data = await client.get_past_matches(team_id, self.league, self.season)
                
                # Konvertiere die Daten in unser Modell
                results = []
                for match_data in matches_data:
                    match_result = DataConverter.convert_match_result(match_data)
                    if match_result:
                        results.append(match_result)
                
                return results
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Spiele für Team {team_id}: {str(e)}")
            return []
    
    async def get_last_n_matches(self, team_id: int, n: int = 14) -> List[MatchResult]:
        """
        Holt die letzten n Spiele eines Teams über die aktuelle und vorherige Saison
        """
        try:
            async with OpenLigaDBClient() as client:
                # Hole die letzten n Spiele des Teams über beide Saisons
                matches_data = await client.get_matches_across_seasons(
                    team_id, 
                    n=n, 
                    league=self.league, 
                    current_season=self.season, 
                    previous_season="2024"  # Vorherige Saison 2024/2025
                )
                
                # Konvertiere die Daten in unser Modell
                results = []
                for match_data in matches_data:
                    match_result = DataConverter.convert_match_result(match_data)
                    if match_result:
                        results.append(match_result)
                
                return results
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der letzten Spiele: {str(e)}")
            return []
    
    async def get_next_matchday(self) -> List[Match]:
        """
        Holt die Spiele des nächsten Spieltags
        """
        try:
            async with OpenLigaDBClient() as client:
                # Hole den nächsten Spieltag
                matchday_data = await client.get_next_matchday(self.league, self.season)
                
                # Konvertiere die Daten in unser Modell
                matches = []
                for match_data in matchday_data:
                    match = DataConverter.convert_match(match_data)
                    matches.append(match)
                
                return matches
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des nächsten Spieltags: {str(e)}")
            
            # Fallback auf Mock-Daten, falls API-Aufruf fehlschlägt
            today = datetime.now()
            next_matchday = 7
            
            bayern = Team(id=1, name="FC Bayern München", short_name="FCB")
            dortmund = Team(id=2, name="Borussia Dortmund", short_name="BVB")
            leipzig = Team(id=3, name="RB Leipzig", short_name="RBL")
            leverkusen = Team(id=4, name="Bayer Leverkusen", short_name="B04")
            
            matches = [
                Match(
                    id=1001,
                    home_team=bayern,
                    away_team=dortmund,
                    date=today + timedelta(days=2),
                    matchday=next_matchday,
                    season="2025/2026"
                ),
                Match(
                    id=1002,
                    home_team=leipzig,
                    away_team=leverkusen,
                    date=today + timedelta(days=2, hours=3),
                    matchday=next_matchday,
                    season="2025/2026"
                ),
            ]
            
            return matches
    
    async def get_team_form(self, team_id: int) -> float:
        """
        Berechnet die aktuelle Form eines Teams basierend auf den letzten Spielen
        """
        try:
            # Hole die letzten 14 Spiele des Teams (oder weniger, wenn nicht so viele verfügbar sind)
            last_matches = await self.get_last_n_matches(team_id, 14)
            
            if not last_matches:
                logger.info(f"Keine Spiele für Team-ID {team_id} gefunden. Verwende neutrale Form (0.5).")
                return 0.5  # Neutrale Form, wenn keine Spiele verfügbar sind
            
            # Punktesystem: Sieg = 3, Unentschieden = 1, Niederlage = 0
            total_points = 0
            max_points = len(last_matches) * 3  # Maximale Punktzahl (alle Spiele gewonnen)
            
            for match in last_matches:
                is_home = match.match.home_team.id == team_id
                
                if is_home:
                    if match.home_goals > match.away_goals:
                        total_points += 3  # Heimsieg
                    elif match.home_goals == match.away_goals:
                        total_points += 1  # Unentschieden
                else:
                    if match.away_goals > match.home_goals:
                        total_points += 3  # Auswärtssieg
                    elif match.away_goals == match.home_goals:
                        total_points += 1  # Unentschieden
            
            # Berechne die Form als Verhältnis der erzielten Punkte zur maximalen Punktzahl
            form = total_points / max_points if max_points > 0 else 0.5
            
            logger.info(f"Team-ID {team_id}: Form berechnet aus {len(last_matches)} Spielen: {form:.2f}")
            return form
        except Exception as e:
            logger.error(f"Fehler bei der Formberechnung für Team-ID {team_id}: {str(e)}")
            return 0.5  # Verwende neutrale Form statt Zufallswert

    async def get_current_table(self) -> List[TableEntry]:
        """
        Berechnet die aktuelle Bundesliga-Tabelle basierend auf den Spielergebnissen
        """
        try:
            async with OpenLigaDBClient() as client:
                # Hole alle Spiele der aktuellen Saison
                all_matches = await client.get_matches_by_league_season(self.league, self.season)
                
                # Dictionary für Team-Statistiken
                team_stats = {}
                teams_dict = {}
                
                # Verarbeite alle beendeten Spiele
                for match_data in all_matches:
                    if not match_data.get('matchIsFinished', False):
                        continue
                    
                    home_team_data = match_data.get('team1', {})
                    away_team_data = match_data.get('team2', {})
                    
                    home_team_id = home_team_data.get('teamId')
                    away_team_id = away_team_data.get('teamId')
                    
                    # Teams zu Dictionary hinzufügen
                    if home_team_id not in teams_dict:
                        teams_dict[home_team_id] = DataConverter.convert_team(home_team_data)
                    if away_team_id not in teams_dict:
                        teams_dict[away_team_id] = DataConverter.convert_team(away_team_data)
                    
                    # Initialisiere Team-Statistiken falls nicht vorhanden
                    for team_id in [home_team_id, away_team_id]:
                        if team_id not in team_stats:
                            team_stats[team_id] = {
                                'matches_played': 0,
                                'wins': 0,
                                'draws': 0,
                                'losses': 0,
                                'goals_for': 0,
                                'goals_against': 0,
                                'points': 0
                            }
                    
                    # Ergebnis extrahieren
                    results = match_data.get('matchResults', [])
                    final_result = next((r for r in results if r.get('resultTypeID') == 2), None)
                    
                    if not final_result:
                        continue
                    
                    home_goals = final_result.get('pointsTeam1', 0)
                    away_goals = final_result.get('pointsTeam2', 0)
                    
                    # Statistiken aktualisieren
                    team_stats[home_team_id]['matches_played'] += 1
                    team_stats[away_team_id]['matches_played'] += 1
                    
                    team_stats[home_team_id]['goals_for'] += home_goals
                    team_stats[home_team_id]['goals_against'] += away_goals
                    team_stats[away_team_id]['goals_for'] += away_goals
                    team_stats[away_team_id]['goals_against'] += home_goals
                    
                    # Punkte vergeben
                    if home_goals > away_goals:  # Heimsieg
                        team_stats[home_team_id]['wins'] += 1
                        team_stats[home_team_id]['points'] += 3
                        team_stats[away_team_id]['losses'] += 1
                    elif home_goals < away_goals:  # Auswärtssieg
                        team_stats[away_team_id]['wins'] += 1
                        team_stats[away_team_id]['points'] += 3
                        team_stats[home_team_id]['losses'] += 1
                    else:  # Unentschieden
                        team_stats[home_team_id]['draws'] += 1
                        team_stats[home_team_id]['points'] += 1
                        team_stats[away_team_id]['draws'] += 1
                        team_stats[away_team_id]['points'] += 1
                
                # Erstelle Tabelleneintrage
                table_entries = []
                for team_id, stats in team_stats.items():
                    if team_id in teams_dict:
                        goal_difference = stats['goals_for'] - stats['goals_against']
                        
                        entry = TableEntry(
                            position=0,  # Wird später sortiert
                            team=teams_dict[team_id],
                            matches_played=stats['matches_played'],
                            wins=stats['wins'],
                            draws=stats['draws'],
                            losses=stats['losses'],
                            goals_for=stats['goals_for'],
                            goals_against=stats['goals_against'],
                            goal_difference=goal_difference,
                            points=stats['points']
                        )
                        table_entries.append(entry)
                
                # Sortiere nach Punkten, dann nach Tordifferenz, dann nach erzielten Toren
                table_entries.sort(key=lambda x: (-x.points, -x.goal_difference, -x.goals_for))
                
                # Setze Positionen
                for i, entry in enumerate(table_entries):
                    entry.position = i + 1
                
                logger.info(f"Tabelle berechnet mit {len(table_entries)} Teams")
                return table_entries
                
        except Exception as e:
            logger.error(f"Fehler beim Berechnen der Tabelle: {str(e)}")
            return []
