"""
Vereinfachte Backend Version für Cloud Run Deployment - Master DB Schema
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
    description="API mit echten Bundesliga-Daten - Master DB Schema",
    version="3.0.0"
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
    return {"message": "Kick Predictor API - Cloud Edition", "status": "running", "version": "3.0.0"}

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
        
        # Einfache Tabelle ohne Match-Statistiken (da lokale matches Tabelle evtl. keine Tore hat)
        cursor.execute("""
            SELECT 
                name,
                logo_url,
                short_name,
                external_id
            FROM teams
            ORDER BY name
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
    """Vorhersage-Qualitäts-Statistiken im erwarteten Frontend Format"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hole die Prediction-Einträge
        cursor.execute("""
            SELECT 
                match_info,
                predicted_score,
                actual_score,
                hit_type,
                tendency_correct,
                exact_score_correct,
                predicted_home_win_prob,
                predicted_draw_prob,
                predicted_away_win_prob
            FROM prediction_quality
            ORDER BY synced_at DESC
            LIMIT 50
        """)
        
        entries = []
        for row in cursor.fetchall():
            # Mock Match Structure da wir keine echten Match-Daten haben
            match_info_parts = row["match_info"].split(" vs ")
            home_team = match_info_parts[0] if len(match_info_parts) > 0 else "Team A"
            away_team = match_info_parts[1] if len(match_info_parts) > 1 else "Team B"
            
            entries.append({
                "match": {
                    "id": 1,
                    "home_team": {
                        "id": 1,
                        "name": home_team,
                        "short_name": home_team[:10]
                    },
                    "away_team": {
                        "id": 2,
                        "name": away_team,
                        "short_name": away_team[:10]
                    },
                    "date": "2025-09-16T15:30:00Z",
                    "matchday": 1,
                    "season": "2025"
                },
                "predicted_score": row["predicted_score"],
                "actual_score": row["actual_score"],
                "predicted_home_win_prob": row["predicted_home_win_prob"] or 0.5,
                "predicted_draw_prob": row["predicted_draw_prob"] or 0.3,
                "predicted_away_win_prob": row["predicted_away_win_prob"] or 0.2,
                "hit_type": row["hit_type"],
                "tendency_correct": bool(row["tendency_correct"]),
                "exact_score_correct": bool(row["exact_score_correct"])
            })
        
        # Berechne Statistiken
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
        misses = total - exact - (tendency - exact)  # tendency includes exact
        
        stats_data = {
            "total_predictions": total,
            "exact_matches": exact,
            "tendency_matches": tendency,
            "misses": misses,
            "exact_match_rate": round((exact / total), 3) if total > 0 else 0,
            "tendency_match_rate": round((tendency / total), 3) if total > 0 else 0,
            "overall_accuracy": round(((exact + tendency) / total), 3) if total > 0 else 0,
            "quality_score": round((exact * 3 + tendency * 1) / (total * 3), 3) if total > 0 else 0
        }
        
        result = {
            "entries": entries,
            "stats": stats_data,
            "processed_matches": total,
            "cached_at": datetime.now().isoformat()
        }
        
        conn.close()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Qualitätsstatistiken: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)