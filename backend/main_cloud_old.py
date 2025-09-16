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
        cursor.execute("SELECT COUNT(*) FROM teams")
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
            SELECT external_id, name, logo_url, short_name
            FROM teams 
            ORDER BY name
        """)
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                "team_id": row["external_id"],
                "team_name": row["name"],
                "team_icon_url": row["logo_url"],
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
        cursor.execute("SELECT DISTINCT season FROM matches ORDER BY season DESC LIMIT 1")
        current_season_result = cursor.fetchone()
        if not current_season_result:
            return []
        current_season = current_season_result[0]
        
        # Tabelle berechnen - hier nehmen wir an, dass matches Tabelle home_goals und away_goals hat
        # Falls nicht vorhanden, erstellen wir eine einfache Tabelle ohne Statistiken
        cursor.execute("""
            SELECT 
                t.name,
                t.logo_url,
                t.short_name,
                t.external_id
            FROM teams t
            ORDER BY t.name
        """)
        
        table = []
        position = 1
        for row in cursor.fetchall():
            table.append({
                "position": position,
                "team_name": row["name"],
                "team_icon_url": row["logo_url"],
                "shortname": row["short_name"],
                "games": 0,
                "wins": 0,
                "draws": 0, 
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0
            })
            position += 1
            
        conn.close()
        return table
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Tabelle: {str(e)}")

@app.get("/api/next-matchday")
async def get_next_matchday():
    """Nächster Spieltag"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Aktuellen Spieltag ermitteln
        cursor.execute("""
            SELECT DISTINCT matchday, season 
            FROM matches 
            ORDER BY season DESC, matchday ASC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            return {"matchday": result["matchday"], "season": result["season"]}
        else:
            return {"matchday": 1, "season": "2025"}
            
    except Exception as e:
        return {"matchday": 1, "season": "2025"}

@app.get("/api/matchday-info")
async def get_matchday_info():
    """Spieltag Informationen"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT matchday, season, COUNT(*) as match_count
            FROM matches 
            GROUP BY matchday, season
            ORDER BY season DESC, matchday DESC
            LIMIT 10
        """)
        
        matchdays = []
        for row in cursor.fetchall():
            matchdays.append({
                "matchday": row["matchday"],
                "season": row["season"],
                "match_count": row["match_count"]
            })
        
        conn.close()
        return matchdays
        
    except Exception as e:
        return []

@app.get("/api/predictions")
async def get_predictions():
    """Vorhersage-Qualität"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                match_info,
                predicted_score,
                actual_score,
                hit_type,
                tendency_correct,
                exact_score_correct
            FROM prediction_quality
            ORDER BY synced_at DESC
            LIMIT 50
        """)
        
        predictions = []
        for row in cursor.fetchall():
            predictions.append({
                "match_info": row["match_info"],
                "predicted_score": row["predicted_score"],
                "actual_score": row["actual_score"],
                "hit_type": row["hit_type"],
                "tendency_correct": bool(row["tendency_correct"]),
                "exact_score_correct": bool(row["exact_score_correct"])
            })
        
        conn.close()
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Vorhersagen: {str(e)}")

@app.get("/api/prediction-quality")
async def get_prediction_quality():
    """Vorhersage-Qualitäts-Statistiken"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Gesamtstatistiken
        cursor.execute("""
            SELECT 
                COUNT(*) as total_predictions,
                SUM(CASE WHEN exact_score_correct = 1 THEN 1 ELSE 0 END) as exact_matches,
                SUM(CASE WHEN tendency_correct = 1 THEN 1 ELSE 0 END) as tendency_matches
            FROM prediction_quality
        """)
        
        stats = cursor.fetchone()
        total = stats["total_predictions"] or 0
        exact = stats["exact_matches"] or 0
        tendency = stats["tendency_matches"] or 0
        
        result = {
            "total_predictions": total,
            "exact_matches": exact,
            "tendency_matches": tendency,
            "exact_accuracy": round((exact / total * 100), 2) if total > 0 else 0,
            "tendency_accuracy": round((tendency / total * 100), 2) if total > 0 else 0,
            "overall_accuracy": round(((exact + tendency) / total * 100), 2) if total > 0 else 0
        }
        
        conn.close()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Qualitätsstatistiken: {str(e)}")

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