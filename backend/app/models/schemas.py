from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class HitType(str, Enum):
    EXACT_MATCH = "exact_match"  # Exakte Ergebnis-Übereinstimmung
    TENDENCY_MATCH = "tendency_match"  # Tendenz richtig (Sieg/Unentschieden/Niederlage)
    MISS = "miss"  # Komplett falsch

class Team(BaseModel):
    id: int
    name: str
    short_name: str
    logo_url: Optional[str] = None

class Match(BaseModel):
    id: int
    home_team: Team
    away_team: Team
    date: datetime
    matchday: int
    season: str

class MatchResult(BaseModel):
    match: Match
    home_goals: int
    away_goals: int
    home_xg: float
    away_xg: float

class FormFactor(BaseModel):
    home_form: float
    away_form: float
    home_xg_last_6: float
    away_xg_last_6: float

class TableEntry(BaseModel):
    position: int
    team: Team
    matches_played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int

class MatchdayInfo(BaseModel):
    current_matchday: int
    next_matchday: int
    predictions_available_until: int
    season: str

class Prediction(BaseModel):
    match: Match
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_score: str
    form_factors: FormFactor

class PredictionQualityEntry(BaseModel):
    match: Match
    predicted_score: str
    actual_score: str
    predicted_home_win_prob: float
    predicted_draw_prob: float
    predicted_away_win_prob: float
    hit_type: HitType
    tendency_correct: bool
    exact_score_correct: bool

class PredictionQualityStats(BaseModel):
    total_predictions: int
    exact_matches: int
    tendency_matches: int
    misses: int
    exact_match_rate: float
    tendency_match_rate: float
    overall_accuracy: float
    quality_score: float  # Gewichteter Score: 3 Punkte für Volltreffer, 1 Punkt für Tendenz
