import numpy as np
from typing import Dict, List
from app.models.schemas import Match, MatchResult, Prediction, FormFactor
from app.interfaces.data_interface import DataServiceInterface
import logging

logger = logging.getLogger(__name__)

class PredictionService:
    """
    Service zur Vorhersage von Spielergebnissen
    """
    
    def __init__(self, data_service: DataServiceInterface):
        self.data_service = data_service
        # Hier später das trainierte Modell laden
    
    async def calculate_form_factors(self, match: Match) -> FormFactor:
        """
        Berechnet die Formfaktoren für ein Spiel
        """
        home_form = await self.data_service.get_team_form(match.home_team.id)
        away_form = await self.data_service.get_team_form(match.away_team.id)
        
        # Lade die letzten Spiele, um xG zu berechnen
        home_last_matches = await self.data_service.get_last_n_matches(match.home_team.id, 6)
        away_last_matches = await self.data_service.get_last_n_matches(match.away_team.id, 6)
        
        # Berechne xG für die letzten 6 Spiele
        home_xg_last_6 = 0
        
        for m in home_last_matches:
            if m.match.home_team.id == match.home_team.id:
                home_xg_last_6 += m.home_xg
            else:
                home_xg_last_6 += m.away_xg
        
        away_xg_last_6 = 0
        
        for m in away_last_matches:
            if m.match.home_team.id == match.away_team.id:
                away_xg_last_6 += m.home_xg
            else:
                away_xg_last_6 += m.away_xg
        
        # Fallback auf Schätzwerte, falls keine Daten verfügbar sind
        if not home_last_matches:
            home_xg_last_6 = 8.5
        
        if not away_last_matches:
            away_xg_last_6 = 7.5
        
        return FormFactor(
            home_form=home_form,
            away_form=away_form,
            home_xg_last_6=home_xg_last_6,
            away_xg_last_6=away_xg_last_6
        )
    
    async def predict_match(self, match: Match) -> Prediction:
        """
        Erstellt eine Vorhersage für ein Spiel
        """
        # Formfaktoren berechnen
        form_factors = await self.calculate_form_factors(match)
        
        # Einfaches Modell zur Berechnung der Siegwahrscheinlichkeiten
        # Später durch ein ML-Modell ersetzen
        form_diff = form_factors.home_form - form_factors.away_form
        xg_diff = form_factors.home_xg_last_6 - form_factors.away_xg_last_6
        
        # Heimvorteil einbeziehen
        home_advantage = 0.1
        
        # Siegwahrscheinlichkeiten berechnen
        home_win_prob = 0.5 + (form_diff / 3) + (xg_diff / 20) + home_advantage
        away_win_prob = 0.5 - (form_diff / 3) - (xg_diff / 20) - home_advantage
        
        # Normalisieren
        total = home_win_prob + away_win_prob
        home_win_prob /= total
        away_win_prob /= total
        
        # Unentschieden-Wahrscheinlichkeit berechnen
        draw_prob = max(0, 1 - home_win_prob - away_win_prob)
        
        # Vorhersage des Ergebnisses
        home_expected_goals = max(0, round(form_factors.home_xg_last_6 / 6 * form_factors.home_form, 1))
        away_expected_goals = max(0, round(form_factors.away_xg_last_6 / 6 * form_factors.away_form, 1))
        
        predicted_score = f"{int(round(home_expected_goals))}:{int(round(away_expected_goals))}"
        
        return Prediction(
            match=match,
            home_win_prob=round(home_win_prob, 2),
            draw_prob=round(draw_prob, 2),
            away_win_prob=round(away_win_prob, 2),
            predicted_score=predicted_score,
            form_factors=form_factors
        )
    
    async def predict_matchday(self, matchday: int) -> List[Prediction]:
        """
        Erstellt Vorhersagen für alle Spiele eines Spieltags mit Caching
        """
        # Prüfe zunächst den Cache
        cached_predictions = self.data_service._get_cached_predictions(matchday)
        if cached_predictions:
            return cached_predictions
        
        # Lade die Spiele des spezifischen Spieltags
        matches = await self.data_service.get_matches_by_matchday(matchday)
        
        if not matches:
            logger.warning(f"Keine Spiele für Spieltag {matchday} gefunden")
            return []
        
        predictions = []
        for match in matches:
            prediction = await self.predict_match(match)
            predictions.append(prediction)
        
        logger.info(f"Vorhersagen für {len(predictions)} Spiele in Spieltag {matchday} erstellt")
        
        # Speichere die Vorhersagen im Cache
        self.data_service._cache_predictions(matchday, predictions)
        
        return predictions
