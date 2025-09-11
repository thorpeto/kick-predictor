from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

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
    home_possession: float
    away_possession: float

class FormFactor(BaseModel):
    home_form: float
    away_form: float
    home_xg_last_6: float
    away_xg_last_6: float
    home_possession_avg: float
    away_possession_avg: float

class Prediction(BaseModel):
    match: Match
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_score: str
    form_factors: FormFactor
