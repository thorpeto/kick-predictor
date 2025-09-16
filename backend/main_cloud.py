"""
Vereinfachte Backend Version für Cloud Run Deployment
"""
import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

app = FastAPI(
    title="Kick Predictor API - Cloud Edition",
    description="API mit echten Bundesliga-Daten - vereinfacht für Cloud Run",
    version="2.0.1"
)

# CORS-Einstellungen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_PATH = 'kick_predictor_final.db'

def get_db_connection():
    """Datenbankverbindung erstellen"""
    if not os.path.exists(DATABASE_PATH):
        raise HTTPException(status_code=500, detail="Datenbank nicht gefunden")
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    """Root Endpoint"""
    return {"message": "Kick Predictor API - Cloud Edition", "status": "running"}

@app.get("/health")
async def health_check():
    """Health Check für Cloud Run"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM teams_real")
        team_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "teams": team_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/teams")
async def get_teams():
    """Alle Teams abrufen"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT team_id, name, icon_url, short_name
            FROM teams_real 
            ORDER BY name
        """)
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                "team_id": row["team_id"],
                "team_name": row["name"],
                "team_icon_url": row["icon_url"],
                "shortname": row["short_name"]
            })
        
        conn.close()
        return teams
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Teams: {str(e)}")

@app.get("/api/table")
async def get_table():
    """Aktuelle Bundesliga-Tabelle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Aktuelle Saison bestimmen
        cursor.execute("SELECT DISTINCT season FROM matches_real ORDER BY season DESC LIMIT 1")
        current_season = cursor.fetchone()[0]
        
        # Tabelle berechnen
        cursor.execute("""
            SELECT 
                t.name,
                t.icon_url,
                t.short_name,
                COUNT(CASE WHEN (m.home_team_id = t.team_id AND m.home_goals > m.away_goals) 
                            OR (m.away_team_id = t.team_id AND m.away_goals > m.home_goals) THEN 1 END) as wins,
                COUNT(CASE WHEN m.home_goals = m.away_goals AND (m.home_team_id = t.team_id OR m.away_team_id = t.team_id) THEN 1 END) as draws,
                COUNT(CASE WHEN (m.home_team_id = t.team_id AND m.home_goals < m.away_goals) 
                            OR (m.away_team_id = t.team_id AND m.away_goals < m.home_goals) THEN 1 END) as losses,
                SUM(CASE WHEN m.home_team_id = t.team_id THEN COALESCE(m.home_goals, 0) ELSE 0 END) +
                SUM(CASE WHEN m.away_team_id = t.team_id THEN COALESCE(m.away_goals, 0) ELSE 0 END) as goals_for,
                SUM(CASE WHEN m.home_team_id = t.team_id THEN COALESCE(m.away_goals, 0) ELSE 0 END) +
                SUM(CASE WHEN m.away_team_id = t.team_id THEN COALESCE(m.home_goals, 0) ELSE 0 END) as goals_against,
                COUNT(CASE WHEN (m.home_team_id = t.team_id AND m.home_goals > m.away_goals) 
                            OR (m.away_team_id = t.team_id AND m.away_goals > m.home_goals) THEN 1 END) * 3 +
                COUNT(CASE WHEN m.home_goals = m.away_goals AND (m.home_team_id = t.team_id OR m.away_team_id = t.team_id) THEN 1 END) as points
            FROM teams_real t
            LEFT JOIN matches_real m ON (t.team_id = m.home_team_id OR t.team_id = m.away_team_id) 
                AND m.season = ? AND m.is_finished = 1
            GROUP BY t.team_id, t.name, t.icon_url, t.short_name
            ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC
        """, (current_season,))
        
        table = []
        position = 1
        for row in cursor.fetchall():
            table.append({
                "position": position,
                "team_name": row["name"],
                "team_icon_url": row["icon_url"],
                "shortname": row["short_name"],
                "games": row["wins"] + row["draws"] + row["losses"],
                "wins": row["wins"],
                "draws": row["draws"], 
                "losses": row["losses"],
                "goals_for": row["goals_for"],
                "goals_against": row["goals_against"],
                "goal_difference": row["goals_for"] - row["goals_against"],
                "points": row["points"]
            })
            position += 1
            
        conn.close()
        return table
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Tabelle: {str(e)}")

@app.get("/api/matchday-info")
async def get_matchday_info():
    """Informationen zum aktuellen Spieltag"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Aktuelle Saison bestimmen
        cursor.execute("SELECT DISTINCT season FROM matches_real ORDER BY season DESC LIMIT 1")
        current_season = cursor.fetchone()[0]
        
        # Aktueller und nächster Spieltag
        cursor.execute("""
            SELECT DISTINCT matchday FROM matches_real 
            WHERE season = ? 
            ORDER BY matchday ASC
        """, (current_season,))
        
        matchdays = [row[0] for row in cursor.fetchall()]
        current_matchday = matchdays[0] if matchdays else 1
        next_matchday = matchdays[1] if len(matchdays) > 1 else current_matchday
        
        conn.close()
        return {
            "current_matchday": current_matchday,
            "next_matchday": next_matchday,
            "predictions_available_until": next_matchday,
            "season": current_season
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Spieltag-Info: {str(e)}")

@app.get("/api/next-matchday")
async def get_next_matchday():
    """Nächste Spiele abrufen"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Aktuelle Saison bestimmen
        cursor.execute("SELECT DISTINCT season FROM matches_real ORDER BY season DESC LIMIT 1")
        current_season = cursor.fetchone()[0]
        
        # Nächsten Spieltag finden
        cursor.execute("""
            SELECT MIN(matchday) FROM matches_real 
            WHERE season = ? AND is_finished = 0
        """, (current_season,))
        
        next_matchday = cursor.fetchone()[0] or 1
        
        # Spiele des nächsten Spieltags
        cursor.execute("""
            SELECT 
                m.match_id,
                m.home_team_id,
                m.away_team_id,
                m.home_team_name,
                m.away_team_name,
                m.match_date,
                m.matchday,
                m.season
            FROM matches_real m
            WHERE m.season = ? AND m.matchday = ? 
            ORDER BY m.match_date
        """, (current_season, next_matchday))
        
        matches = []
        for row in cursor.fetchall():
            matches.append({
                "id": row["match_id"],
                "home_team": {
                    "id": row["home_team_id"],
                    "name": row["home_team_name"],
                    "short_name": row["home_team_name"][:10]
                },
                "away_team": {
                    "id": row["away_team_id"], 
                    "name": row["away_team_name"],
                    "short_name": row["away_team_name"][:10]
                },
                "date": row["match_date"],
                "matchday": row["matchday"],
                "season": row["season"]
            })
        
        conn.close()
        return matches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der nächsten Spiele: {str(e)}")

@app.get("/api/predictions/{matchday}")
async def get_predictions(matchday: int):
    """Einfache Vorhersagen für einen Spieltag (Dummy-Daten)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Aktuelle Saison bestimmen
        cursor.execute("SELECT DISTINCT season FROM matches_real ORDER BY season DESC LIMIT 1")
        current_season = cursor.fetchone()[0]
        
        # Spiele des Spieltags
        cursor.execute("""
            SELECT 
                m.match_id,
                m.home_team_id,
                m.away_team_id,
                m.home_team_name,
                m.away_team_name,
                m.match_date,
                m.matchday,
                m.season
            FROM matches_real m
            WHERE m.season = ? AND m.matchday = ? 
            ORDER BY m.match_date
        """, (current_season, matchday))
        
        predictions = []
        for row in cursor.fetchall():
            # Einfache Dummy-Vorhersagen
            predictions.append({
                "match": {
                    "id": row["match_id"],
                    "home_team": {
                        "id": row["home_team_id"],
                        "name": row["home_team_name"],
                        "short_name": row["home_team_name"][:10]
                    },
                    "away_team": {
                        "id": row["away_team_id"], 
                        "name": row["away_team_name"],
                        "short_name": row["away_team_name"][:10]
                    },
                    "date": row["match_date"],
                    "matchday": row["matchday"],
                    "season": row["season"]
                },
                "home_win_prob": 0.4,
                "draw_prob": 0.3,
                "away_win_prob": 0.3,
                "predicted_score": "2:1",
                "form_factors": {
                    "home_form": 0.6,
                    "away_form": 0.5,
                    "home_goals_last_14": 1.5,
                    "away_goals_last_14": 1.2
                }
            })
        
        conn.close()
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Vorhersagen: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)