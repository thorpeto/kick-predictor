"""
SQLAlchemy Database Models für Kick-Predictor
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import enum

Base = declarative_base()

class HitType(str, enum.Enum):
    exact_match = "exact_match"
    tendency_match = "tendency_match"
    miss = "miss"

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=False)
    logo_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    home_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    matchday = Column(Integer, nullable=False)
    season = Column(String(100), nullable=False)
    
    # Ergebnisse (nur für abgeschlossene Spiele)
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    is_finished = Column(Boolean, default=False)
    
    # Metadaten
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    predictions = relationship("Prediction", back_populates="match")
    prediction_quality = relationship("PredictionQuality", back_populates="match")
    
    def __repr__(self):
        return f"<Match(id={self.id}, {self.home_team.short_name if self.home_team else self.home_team_id} vs {self.away_team.short_name if self.away_team else self.away_team_id}, MD {self.matchday})>"

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Vorhersage-Daten
    home_win_prob = Column(Float, nullable=False)
    draw_prob = Column(Float, nullable=False)
    away_win_prob = Column(Float, nullable=False)
    predicted_home_goals = Column(Integer)
    predicted_away_goals = Column(Integer)
    predicted_score = Column(String(20))  # "2:1" Format
    
    # Form-Faktoren
    home_form = Column(Float)
    away_form = Column(Float)
    home_xg_last_6 = Column(Float)
    away_xg_last_6 = Column(Float)
    
    # Metadaten
    calculated_at = Column(DateTime, default=datetime.utcnow)
    algorithm_version = Column(String(50), default="1.0")
    
    # Relationships
    match = relationship("Match", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(match_id={self.match_id}, score={self.predicted_score})>"

class PredictionQuality(Base):
    __tablename__ = "prediction_quality"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Vorhersage vs. Realität
    predicted_score = Column(String(20), nullable=False)
    actual_score = Column(String(20), nullable=False)
    
    # Wahrscheinlichkeiten
    predicted_home_win_prob = Column(Float)
    predicted_draw_prob = Column(Float)
    predicted_away_win_prob = Column(Float)
    
    # Qualitäts-Bewertung
    hit_type = Column(SQLEnum(HitType), nullable=False)
    tendency_correct = Column(Boolean, nullable=False)
    exact_score_correct = Column(Boolean, nullable=False)
    quality_score = Column(Float)  # 0.0 - 1.0
    
    # Metadaten
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="prediction_quality")
    
    def __repr__(self):
        return f"<PredictionQuality(match_id={self.match_id}, hit_type={self.hit_type})>"

class SyncStatus(Base):
    __tablename__ = "sync_status"
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False)  # 'teams', 'matches', 'predictions'
    last_sync = Column(DateTime, nullable=False)
    last_sync_success = Column(Boolean, default=True)
    sync_message = Column(Text)
    records_synced = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<SyncStatus(entity_type={self.entity_type}, last_sync={self.last_sync})>"