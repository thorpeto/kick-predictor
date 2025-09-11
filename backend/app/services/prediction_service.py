import numpy as np
from typing import Dict, List
from app.models.schemas import Match, MatchResult, Prediction, FormFactor
from app.services.data_service import DataService

class PredictionService:
    """
    Service zur Vorhersage von Spielergebnissen
    """
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        # Hier später das trainierte Modell laden
    
    async def calculate_form_factors(self, match: Match) -> FormFactor:
        """
        Berechnet die Formfaktoren für ein Spiel
        """
        home_form = await self.data_service.get_team_form(match.home_team.id)
        away_form = await self.data_service.get_team_form(match.away_team.id)
        
        # Mock-Daten für die anderen Faktoren
        # In der realen Implementierung würden diese aus den historischen Daten berechnet
        return FormFactor(
            home_form=home_form,
            away_form=away_form,
            home_xg_last_6=np.random.normal(10, 2),
            away_xg_last_6=np.random.normal(8, 2),
            home_possession_avg=np.random.normal(55, 10),
            away_possession_avg=np.random.normal(50, 10)
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
        Erstellt Vorhersagen für alle Spiele eines Spieltags
        """
        # In einer realen Implementierung würden hier die Spiele des Spieltags geladen
        # Für den Beispielcode verwenden wir die Spiele des nächsten Spieltags
        matches = await self.data_service.get_next_matchday()
        
        predictions = []
        for match in matches:
            prediction = await self.predict_match(match)
            predictions.append(prediction)
        
        return predictions
