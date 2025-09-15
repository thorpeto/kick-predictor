import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models.schemas import Match, MatchResult, Prediction, FormFactor, Team, TableEntry, MatchdayInfo, PredictionQualityEntry, PredictionQualityStats, HitType
from app.services.openliga_client import OpenLigaDBClient
from app.services.data_converter import DataConverter
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

class DataService:
    """
    Service zum Laden und Verarbeiten der Bundesliga-Daten
    """
    
    def __init__(self):
        # Initialisierung des OpenLigaDB-Clients
        self.league = "bl1"  # 1. Bundesliga
        self.season = "2025"  # Saison 2025/2026
        # Cache für Vorhersagen (in-memory)
        self._predictions_cache: Dict[str, Dict] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        # Cache für Qualitätsdaten
        self._quality_cache: Optional[Dict] = None
        self._quality_cache_expiry: Optional[datetime] = None
    
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
    
    async def get_matches_by_matchday(self, matchday: int) -> List[Match]:
        """
        Holt alle Spiele eines bestimmten Spieltags
        """
        try:
            async with OpenLigaDBClient() as client:
                # Hole Spiele für den spezifischen Spieltag
                matches_data = await client.get_matches_by_matchday(self.league, self.season, matchday)
                
                # Konvertiere die Daten in unser Modell
                matches = []
                for match_data in matches_data:
                    match = DataConverter.convert_match(match_data)
                    if match:
                        matches.append(match)
                
                logger.info(f"Gefunden {len(matches)} Spiele für Spieltag {matchday}")
                return matches
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Spiele für Spieltag {matchday}: {str(e)}")
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

    async def get_current_matchday_info(self) -> MatchdayInfo:
        """
        Bestimmt den aktuellen Spieltag und bis zu welchem Spieltag Vorhersagen verfügbar sind
        """
        try:
            async with OpenLigaDBClient() as client:
                # Hole alle Spiele der aktuellen Saison
                all_matches = await client.get_matches_by_league_season(self.league, self.season)
                
                # Sortiere Spiele nach Spieltag und Datum
                sorted_matches = sorted(all_matches, key=lambda x: (x.get('matchday', 1), x.get('matchDateTime', '')))
                
                now = datetime.now()
                completed_matchdays = set()
                current_matchday = 4  # Spieltag 4 ist der aktuelle (da 1-3 bereits gespielt)
                
                # Analysiere alle Spiele um abgeschlossene Spieltage zu finden
                matchday_status = {}
                for match_data in sorted_matches:
                    try:
                        match_date_str = match_data.get('matchDateTime', '')
                        if match_date_str:
                            match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                        else:
                            continue
                            
                        matchday = match_data.get('matchday', 1)
                        is_finished = match_data.get('matchIsFinished', False)
                        
                        if matchday not in matchday_status:
                            matchday_status[matchday] = {'total': 0, 'finished': 0, 'latest_date': match_date}
                        
                        matchday_status[matchday]['total'] += 1
                        if is_finished:
                            matchday_status[matchday]['finished'] += 1
                        
                        # Aktualisiere das späteste Datum für diesen Spieltag
                        if match_date > matchday_status[matchday]['latest_date']:
                            matchday_status[matchday]['latest_date'] = match_date
                            
                    except Exception as e:
                        logger.warning(f"Fehler beim Parsen des Spiels: {e}")
                        continue
                
                # Bestimme den aktuellen Spieltag basierend auf vollständig abgeschlossenen Spieltagen
                for matchday in sorted(matchday_status.keys()):
                    status = matchday_status[matchday]
                    # Ein Spieltag gilt als abgeschlossen, wenn alle Spiele beendet sind
                    # oder wenn das späteste Spiel des Spieltags in der Vergangenheit liegt
                    is_complete = (status['finished'] == status['total']) or (status['latest_date'] < now - timedelta(days=1))
                    
                    if is_complete:
                        completed_matchdays.add(matchday)
                        current_matchday = max(current_matchday, matchday + 1)
                
                logger.info(f"Abgeschlossene Spieltage: {sorted(completed_matchdays)}")
                logger.info(f"Bestimmter aktueller Spieltag: {current_matchday}")
                
                # Nächster Spieltag
                next_matchday = min(current_matchday + 1, 34)
                
                # Vorhersagen sind bis zum übernächsten Spieltag verfügbar
                predictions_available_until = min(current_matchday + 2, 34)
                
                logger.info(f"Spieltag-Info: Aktuell={current_matchday}, Nächster={next_matchday}, Vorhersagen bis={predictions_available_until}")
                
                return MatchdayInfo(
                    current_matchday=current_matchday,
                    next_matchday=next_matchday,
                    predictions_available_until=predictions_available_until,
                    season=f"{self.season}/{int(self.season)+1}"
                )
                
        except Exception as e:
            logger.error(f"Fehler beim Bestimmen der Spieltag-Info: {str(e)}")
            # Fallback-Werte
            return MatchdayInfo(
                current_matchday=3,
                next_matchday=4,
                predictions_available_until=5,
                season=f"{self.season}/{int(self.season)+1}"
            )

    def _generate_cache_key(self, matchday: int) -> str:
        """
        Generiert einen Cache-Schlüssel für Vorhersagen eines Spieltags
        """
        return f"predictions_{self.league}_{self.season}_{matchday}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Prüft, ob der Cache-Eintrag noch gültig ist (1 Stunde Gültigkeit)
        """
        if cache_key not in self._cache_expiry:
            return False
        
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _get_cached_predictions(self, matchday: int) -> Optional[List[Prediction]]:
        """
        Holt Vorhersagen aus dem Cache
        """
        cache_key = self._generate_cache_key(matchday)
        
        if cache_key in self._predictions_cache and self._is_cache_valid(cache_key):
            logger.info(f"Cache-Hit für Spieltag {matchday}")
            cached_data = self._predictions_cache[cache_key]
            
            # Konvertiere zurück zu Prediction-Objekten
            predictions = []
            for pred_data in cached_data['predictions']:
                prediction = Prediction(**pred_data)
                predictions.append(prediction)
            
            return predictions
        
        return None
    
    def _cache_predictions(self, matchday: int, predictions: List[Prediction]) -> None:
        """
        Speichert Vorhersagen im Cache
        """
        cache_key = self._generate_cache_key(matchday)
        
        # Konvertiere Prediction-Objekte zu JSON-serialisierbaren Dicts
        serializable_predictions = []
        for prediction in predictions:
            pred_dict = prediction.dict()
            serializable_predictions.append(pred_dict)
        
        self._predictions_cache[cache_key] = {
            'predictions': serializable_predictions,
            'cached_at': datetime.now().isoformat()
        }
        
        # Cache für 1 Stunde gültig
        self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)
        
        logger.info(f"Vorhersagen für Spieltag {matchday} im Cache gespeichert")
    
    def clear_predictions_cache(self, matchday: Optional[int] = None) -> None:
        """
        Löscht den Vorhersagen-Cache (optional nur für einen bestimmten Spieltag)
        """
        if matchday:
            cache_key = self._generate_cache_key(matchday)
            if cache_key in self._predictions_cache:
                del self._predictions_cache[cache_key]
                del self._cache_expiry[cache_key]
                logger.info(f"Cache für Spieltag {matchday} gelöscht")
        else:
            self._predictions_cache.clear()
            self._cache_expiry.clear()
            logger.info("Gesamter Vorhersagen-Cache gelöscht")

    def _is_quality_cache_valid(self) -> bool:
        """Prüft, ob der Quality-Cache noch gültig ist (24 Stunden)"""
        if not self._quality_cache or not self._quality_cache_expiry:
            return False
        return datetime.now() < self._quality_cache_expiry
    
    def _cache_quality_data(self, data: Dict) -> None:
        """Speichert Quality-Daten im Cache für 24 Stunden"""
        self._quality_cache = data
        self._quality_cache_expiry = datetime.now() + timedelta(hours=24)
        logger.info("Quality-Daten im Cache gespeichert (24h gültig)")

    async def get_prediction_quality(self) -> Dict:
        """
        Analysiert die Qualität der Vorhersagen durch Vergleich mit realen Ergebnissen
        Nutzt Caching für bessere Performance
        """
        # Prüfe zunächst den Cache (24 Stunden gültig)
        if self._is_quality_cache_valid():
            logger.info("Cache-Hit für Qualitätsdaten")
            return self._quality_cache  # type: ignore
        
        try:
            logger.info("Lade neue Qualitätsdaten von der API...")
            async with OpenLigaDBClient() as client:
                # Hole alle Spiele der aktuellen Saison
                all_matches = await client.get_matches_by_league_season(self.league, self.season)
                
                quality_entries = []
                processed_matches = 0
                
                # Analysiere nur abgeschlossene Spiele der ersten 3 Spieltage
                for match_data in all_matches:
                    matchday = match_data.get('matchday', 1)
                    is_finished = match_data.get('matchIsFinished', False)
                    
                    # Nur abgeschlossene Spiele der ersten 3 Spieltage analysieren
                    if not is_finished or matchday > 3:
                        continue
                    
                    # Konvertiere Match-Daten
                    match = DataConverter.convert_match(match_data)
                    if not match:
                        continue
                    
                    # Simuliere eine Vorhersage für dieses Spiel (normalerweise würden wir gespeicherte Vorhersagen haben)
                    prediction = await self._simulate_prediction_for_match(match)
                    
                    # Extrahiere reales Ergebnis
                    match_results = match_data.get('matchResults', [])
                    if not match_results:
                        continue
                    
                    final_result = match_results[-1]  # Endergebnis
                    home_goals = final_result.get('pointsTeam1', 0)
                    away_goals = final_result.get('pointsTeam2', 0)
                    actual_score = f"{home_goals}:{away_goals}"
                    
                    # Bestimme Treffertyp
                    hit_type, tendency_correct, exact_correct = self._analyze_prediction_accuracy(
                        prediction.predicted_score, 
                        actual_score,
                        prediction.home_win_prob,
                        prediction.draw_prob,
                        prediction.away_win_prob
                    )
                    
                    quality_entry = PredictionQualityEntry(
                        match=match,
                        predicted_score=prediction.predicted_score,
                        actual_score=actual_score,
                        predicted_home_win_prob=prediction.home_win_prob,
                        predicted_draw_prob=prediction.draw_prob,
                        predicted_away_win_prob=prediction.away_win_prob,
                        hit_type=hit_type,
                        tendency_correct=tendency_correct,
                        exact_score_correct=exact_correct
                    )
                    
                    quality_entries.append(quality_entry)
                    processed_matches += 1
                
                # Berechne Statistiken
                stats = self._calculate_quality_stats(quality_entries)
                
                result = {
                    "entries": quality_entries,
                    "stats": stats,
                    "processed_matches": processed_matches,
                    "cached_at": datetime.now().isoformat()
                }
                
                # Speichere im Cache (24 Stunden gültig)
                self._cache_quality_data(result)
                
                logger.info(f"Qualitätsdaten verarbeitet: {processed_matches} Spiele")
                return result
                
        except Exception as e:
            logger.error(f"Fehler beim Berechnen der Vorhersagequalität: {str(e)}")
            # Falls ein Fehler auftritt und wir haben Cache-Daten, verwende diese
            if self._quality_cache:
                logger.warning("Verwende veraltete Cache-Daten aufgrund von API-Fehler")
                return self._quality_cache
            return {"entries": [], "stats": None, "error": str(e)}
    
    async def _simulate_prediction_for_match(self, match: Match) -> Prediction:
        """
        Simuliert eine Vorhersage für ein vergangenes Spiel (für Demo-Zwecke)
        In einer echten Implementierung würden hier gespeicherte Vorhersagen abgerufen
        """
        # Import hier um Zirkelbezug zu vermeiden
        from app.services.prediction_service import PredictionService
        prediction_service = PredictionService(self)
        
        return await prediction_service.predict_match(match)
    
    def _analyze_prediction_accuracy(self, predicted_score: str, actual_score: str, 
                                   home_win_prob: float, draw_prob: float, away_win_prob: float) -> tuple:
        """
        Analysiert die Genauigkeit einer Vorhersage
        """
        # Prüfe auf exakte Übereinstimmung
        exact_correct = predicted_score == actual_score
        if exact_correct:
            return HitType.EXACT_MATCH, True, True
        
        # Extrahiere Tore aus den Scores
        try:
            pred_home, pred_away = map(int, predicted_score.split(':'))
            actual_home, actual_away = map(int, actual_score.split(':'))
        except:
            return HitType.MISS, False, False
        
        # Bestimme Tendenzen
        pred_tendency = self._get_match_tendency(pred_home, pred_away)
        actual_tendency = self._get_match_tendency(actual_home, actual_away)
        
        # Prüfe auf Tendenz-Übereinstimmung
        tendency_correct = pred_tendency == actual_tendency
        
        if tendency_correct:
            return HitType.TENDENCY_MATCH, True, False
        else:
            return HitType.MISS, False, False
    
    def _get_match_tendency(self, home_goals: int, away_goals: int) -> str:
        """
        Bestimmt die Tendenz eines Spiels (Heimsieg, Unentschieden, Auswärtssieg)
        """
        if home_goals > away_goals:
            return "home_win"
        elif home_goals < away_goals:
            return "away_win"
        else:
            return "draw"
    
    def _calculate_quality_stats(self, entries: List[PredictionQualityEntry]) -> PredictionQualityStats:
        """
        Berechnet Qualitätsstatistiken basierend auf den Vorhersageeinträgen
        """
        if not entries:
            return PredictionQualityStats(
                total_predictions=0,
                exact_matches=0,
                tendency_matches=0,
                misses=0,
                exact_match_rate=0.0,
                tendency_match_rate=0.0,
                overall_accuracy=0.0,
                quality_score=0.0
            )
        
        total = len(entries)
        exact_matches = len([e for e in entries if e.hit_type == HitType.EXACT_MATCH])
        tendency_matches = len([e for e in entries if e.hit_type == HitType.TENDENCY_MATCH])
        misses = len([e for e in entries if e.hit_type == HitType.MISS])
        
        exact_rate = exact_matches / total
        tendency_rate = tendency_matches / total
        overall_accuracy = (exact_matches + tendency_matches) / total
        
        # Qualitätsscore: 3 Punkte für Volltreffer, 1 Punkt für Tendenz
        quality_score = (exact_matches * 3 + tendency_matches * 1) / (total * 3)
        
        return PredictionQualityStats(
            total_predictions=total,
            exact_matches=exact_matches,
            tendency_matches=tendency_matches,
            misses=misses,
            exact_match_rate=round(exact_rate, 3),
            tendency_match_rate=round(tendency_rate, 3),
            overall_accuracy=round(overall_accuracy, 3),
            quality_score=round(quality_score, 3)
        )
