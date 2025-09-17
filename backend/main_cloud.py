"""
Vereinfaapp = FastAPI(
    title="Kick Predictor API - Cloud Edition",
    description="API mit echten Bundesliga-Daten - Master DB Schema",
    version="3.0.5"
)Backend Version für Cloud Run Deployment - Master DB Schema
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
    version="3.0.1"
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
    return {"message": "Kick Predictor API - Cloud Edition", "status": "running", "version": "3.0.5"}

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
    """Nächster Spieltag mit Matches für Frontend Homepage"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe zuerst matches_real Tabelle (hat die aktuellen Daten!)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches_real'")
        matches_real_exists = cursor.fetchone() is not None
        
        if matches_real_exists:
            # Hole nächsten Spieltag aus matches_real Tabelle  
            cursor.execute("""
                SELECT DISTINCT matchday, season 
                FROM matches_real 
                WHERE is_finished = 0 OR is_finished IS NULL
                ORDER BY season DESC, matchday ASC 
                LIMIT 1
            """)
            
            matchday_result = cursor.fetchone()
            if matchday_result:
                matchday = matchday_result["matchday"]
                season = matchday_result["season"]
                
                # Hole alle Matches für diesen Spieltag mit Team-Details aus matches_real
                cursor.execute("""
                    SELECT 
                        mr.id as match_id,
                        mr.matchday,
                        mr.season,
                        mr.match_date as date,
                        mr.is_finished,
                        mr.home_goals,
                        mr.away_goals,
                        mr.home_team_id,
                        mr.home_team_name,
                        mr.away_team_id,
                        mr.away_team_name,
                        tr_home.short_name as home_team_short,
                        tr_home.icon_url as home_team_logo,
                        tr_away.short_name as away_team_short,
                        tr_away.icon_url as away_team_logo
                    FROM matches_real mr
                    LEFT JOIN teams_real tr_home ON mr.home_team_id = tr_home.team_id
                    LEFT JOIN teams_real tr_away ON mr.away_team_id = tr_away.team_id
                    WHERE mr.matchday = ? AND mr.season = ?
                    ORDER BY mr.match_date
                """, (matchday, season))
                
                matches = []
                for row in cursor.fetchall():
                    matches.append({
                        "id": row["match_id"],
                        "home_team": {
                            "id": row["home_team_id"],
                            "name": row["home_team_name"],
                            "short_name": row["home_team_short"] or row["home_team_name"],
                            "logo_url": row["home_team_logo"]
                        },
                        "away_team": {
                            "id": row["away_team_id"],
                            "name": row["away_team_name"],
                            "short_name": row["away_team_short"] or row["away_team_name"],
                            "logo_url": row["away_team_logo"]
                        },
                        "date": row["date"],
                        "matchday": row["matchday"],
                        "season": row["season"],
                        "is_finished": bool(row["is_finished"]) if row["is_finished"] is not None else False,
                        "home_goals": row["home_goals"],
                        "away_goals": row["away_goals"]
                    })
                
                conn.close()
                return {
                    "matchday": matchday,
                    "season": season,
                    "matches": matches
                }
        
        # Fallback: Prüfe ob matches Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches'")
        matches_table_exists = cursor.fetchone() is not None
        
        if matches_table_exists:
            # Hole nächsten Spieltag aus matches Tabelle
            cursor.execute("""
                SELECT DISTINCT matchday, season 
                FROM matches 
                ORDER BY season DESC, matchday ASC 
                LIMIT 1
            """)
            
            matchday_result = cursor.fetchone()
            if matchday_result:
                matchday = matchday_result["matchday"]
                season = matchday_result["season"]
                
                # Hole alle Matches für diesen Spieltag mit Team-Details
                cursor.execute("""
                    SELECT 
                        m.id as match_id,
                        m.matchday,
                        m.season,
                        m.date,
                        m.home_goals,
                        m.away_goals,
                        ht.external_id as home_team_id,
                        ht.name as home_team_name,
                        ht.short_name as home_team_short,
                        ht.logo_url as home_team_logo,
                        at.external_id as away_team_id,
                        at.name as away_team_name,
                        at.short_name as away_team_short,
                        at.logo_url as away_team_logo
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.id
                    JOIN teams at ON m.away_team_id = at.id
                    WHERE m.matchday = ? AND m.season = ?
                    ORDER BY m.date
                """, (matchday, season))
                
                matches = []
                for row in cursor.fetchall():
                    matches.append({
                        "id": row["match_id"],
                        "home_team": {
                            "id": row["home_team_id"],
                            "name": row["home_team_name"],
                            "short_name": row["home_team_short"],
                            "logo_url": row["home_team_logo"]
                        },
                        "away_team": {
                            "id": row["away_team_id"],
                            "name": row["away_team_name"],
                            "short_name": row["away_team_short"],
                            "logo_url": row["away_team_logo"]
                        },
                        "date": row["date"],
                        "matchday": row["matchday"],
                        "season": row["season"],
                        "is_finished": False,  # Standard für matches ohne is_finished Feld
                        "home_goals": row["home_goals"],
                        "away_goals": row["away_goals"]
                    })
                
                conn.close()
                return {
                    "matchday": matchday,
                    "season": season,
                    "matches": matches
                }
        
        # Fallback: Verwende matches_real Tabelle falls vorhanden
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches_real'")
        matches_real_exists = cursor.fetchone() is not None
        
        if matches_real_exists:
            cursor.execute("""
                SELECT DISTINCT matchday, season 
                FROM matches_real 
                ORDER BY season DESC, matchday ASC 
                LIMIT 1
            """)
            
            matchday_result = cursor.fetchone()
            if matchday_result:
                matchday = matchday_result["matchday"]
                season = matchday_result["season"]
                
                # Hole Matches mit Team-Details aus matches_real und teams_real
                cursor.execute("""
                    SELECT 
                        mr.match_id,
                        mr.matchday,
                        mr.season,
                        mr.match_date,
                        mr.is_finished,
                        mr.home_goals,
                        mr.away_goals,
                        mr.home_team_id,
                        mr.home_team_name,
                        mr.away_team_id,
                        mr.away_team_name,
                        ht.short_name as home_team_short,
                        ht.icon_url as home_team_logo,
                        at.short_name as away_team_short,
                        at.icon_url as away_team_logo
                    FROM matches_real mr
                    LEFT JOIN teams_real ht ON mr.home_team_id = ht.team_id
                    LEFT JOIN teams_real at ON mr.away_team_id = at.team_id
                    WHERE mr.matchday = ? AND mr.season = ?
                    ORDER BY mr.match_date
                """, (matchday, season))
                
                matches = []
                for row in cursor.fetchall():
                    matches.append({
                        "id": row["match_id"],
                        "home_team": {
                            "id": row["home_team_id"],
                            "name": row["home_team_name"],
                            "short_name": row["home_team_short"] or row["home_team_name"][:3],
                            "logo_url": row["home_team_logo"] or ""
                        },
                        "away_team": {
                            "id": row["away_team_id"],
                            "name": row["away_team_name"],
                            "short_name": row["away_team_short"] or row["away_team_name"][:3],
                            "logo_url": row["away_team_logo"] or ""
                        },
                        "date": row["match_date"],
                        "matchday": row["matchday"],
                        "season": row["season"],
                        "is_finished": bool(row["is_finished"]),
                        "home_goals": row["home_goals"],
                        "away_goals": row["away_goals"]
                    })
                
                conn.close()
                return {
                    "matchday": matchday,
                    "season": season,
                    "matches": matches
                }
        
        # Fallback: Generiere Dummy-Matches basierend auf Teams
        cursor.execute("""
            SELECT external_id, name, short_name, logo_url
            FROM teams 
            ORDER BY name
            LIMIT 18
        """)
        teams = cursor.fetchall()
        
        if len(teams) >= 2:
            matches = []
            # Erstelle einige Dummy-Matches
            for i in range(0, min(len(teams)-1, 8), 2):
                if i+1 < len(teams):
                    matches.append({
                        "id": i+1,
                        "home_team": {
                            "id": teams[i]["external_id"],
                            "name": teams[i]["name"],
                            "short_name": teams[i]["short_name"],
                            "logo_url": teams[i]["logo_url"]
                        },
                        "away_team": {
                            "id": teams[i+1]["external_id"],
                            "name": teams[i+1]["name"],
                            "short_name": teams[i+1]["short_name"],
                            "logo_url": teams[i+1]["logo_url"]
                        },
                        "date": "2025-09-21T15:30:00Z",
                        "matchday": 1,
                        "season": "2025",
                        "is_finished": False,
                        "home_goals": None,
                        "away_goals": None
                    })
            
            conn.close()
            return {
                "matchday": 1,
                "season": "2025",
                "matches": matches
            }
        
        conn.close()
        return {
            "matchday": 1,
            "season": "2025",
            "matches": []
        }
            
    except Exception as e:
        return {
            "matchday": 1,
            "season": "2025",
            "matches": [],
            "error": str(e)
        }

@app.get("/api/matchday-info")
async def get_matchday_info():
    """Spieltag Informationen - verwendet matches_real für aktuelle Daten"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe zuerst matches_real Tabelle (hat aktuelle Daten)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches_real'")
        matches_real_exists = cursor.fetchone() is not None
        
        if matches_real_exists:
            cursor.execute("""
                SELECT matchday, season, COUNT(*) as match_count
                FROM matches_real 
                GROUP BY matchday, season
                ORDER BY season DESC, matchday DESC
                LIMIT 10
            """)
            
            matchdays = []
            max_matchday = 0
            current_season = None
            
            for row in cursor.fetchall():
                matchdays.append({
                    "matchday": row["matchday"],
                    "season": row["season"],
                    "match_count": row["match_count"]
                })
                
                if current_season is None:
                    current_season = row["season"]
                    
                if row["season"] == current_season and row["matchday"] > max_matchday:
                    max_matchday = row["matchday"]
            
            # Gebe erweiterte Info zurück für Vorhersageseite
            conn.close()
            return {
                "current_matchday": max_matchday,
                "next_matchday": max_matchday + 1 if max_matchday < 34 else max_matchday,
                "predictions_available_until": max_matchday,
                "season": current_season or "2025",
                "matchdays": matchdays
            }
        
        # Fallback: verwende matches Tabelle
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
        return {
            "current_matchday": 1,
            "next_matchday": 2,
            "predictions_available_until": 1,
            "season": "2025",
            "matchdays": matchdays
        }
        
    except Exception as e:
        return {
            "current_matchday": 1,
            "next_matchday": 2,
            "predictions_available_until": 1,
            "season": "2025",
            "matchdays": []
        }

@app.get("/api/predictions/{matchday}")
async def get_predictions_for_matchday(matchday: int):
    """Vorhersagen für einen bestimmten Spieltag"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe zuerst matches_real Tabelle (hat aktuelle Daten)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches_real'")
        matches_real_exists = cursor.fetchone() is not None
        
        if matches_real_exists:
            # Hole alle Matches für diesen Spieltag aus matches_real
            cursor.execute("""
                SELECT 
                    mr.id as match_id,
                    mr.matchday,
                    mr.season,
                    mr.match_date as date,
                    mr.is_finished,
                    mr.home_goals,
                    mr.away_goals,
                    mr.home_team_id,
                    mr.home_team_name,
                    mr.away_team_id,
                    mr.away_team_name,
                    tr_home.short_name as home_team_short,
                    tr_home.icon_url as home_team_logo,
                    tr_away.short_name as away_team_short,
                    tr_away.icon_url as away_team_logo
                FROM matches_real mr
                LEFT JOIN teams_real tr_home ON mr.home_team_id = tr_home.team_id
                LEFT JOIN teams_real tr_away ON mr.away_team_id = tr_away.team_id
                WHERE mr.matchday = ? AND mr.season = '2025'
                ORDER BY mr.match_date
            """, (matchday,))
            
            predictions = []
            for row in cursor.fetchall():
                # Vereinfachte Vorhersagelogik basierend auf Team-Namen
                home_team = row["home_team_name"]
                away_team = row["away_team_name"]
                
                # Basis-Wahrscheinlichkeiten (können später durch ML ersetzt werden)
                home_win_prob = 0.45
                draw_prob = 0.30
                away_win_prob = 0.25
                
                # Einfache Anpassung basierend auf Team-Stärke (vereinfacht)
                strong_teams = ["FC Bayern München", "Borussia Dortmund", "RB Leipzig", "Bayer 04 Leverkusen"]
                if home_team in strong_teams:
                    home_win_prob += 0.15
                    away_win_prob -= 0.10
                    draw_prob -= 0.05
                if away_team in strong_teams:
                    away_win_prob += 0.15
                    home_win_prob -= 0.10
                    draw_prob -= 0.05
                
                # Normalisierung
                total = home_win_prob + draw_prob + away_win_prob
                home_win_prob = home_win_prob / total
                draw_prob = draw_prob / total
                away_win_prob = away_win_prob / total
                
                # Vorhersage für Ergebnis
                if home_win_prob > away_win_prob:
                    predicted_score = "2:1"
                elif away_win_prob > home_win_prob:
                    predicted_score = "1:2"
                else:
                    predicted_score = "1:1"
                
                predictions.append({
                    "match": {
                        "id": row["match_id"],
                        "home_team": {
                            "id": row["home_team_id"],
                            "name": row["home_team_name"],
                            "short_name": row["home_team_short"] or row["home_team_name"],
                            "logo_url": row["home_team_logo"]
                        },
                        "away_team": {
                            "id": row["away_team_id"],
                            "name": row["away_team_name"],
                            "short_name": row["away_team_short"] or row["away_team_name"],
                            "logo_url": row["away_team_logo"]
                        },
                        "date": row["date"],
                        "matchday": row["matchday"],
                        "season": row["season"]
                    },
                    "home_win_prob": home_win_prob,
                    "draw_prob": draw_prob,
                    "away_win_prob": away_win_prob,
                    "predicted_score": predicted_score,
                    "form_factors": {
                        "home_form": 50.0 + (home_win_prob - 0.33) * 100,
                        "away_form": 50.0 + (away_win_prob - 0.33) * 100,
                        "home_goals_last_14": int(10 + home_win_prob * 5),
                        "away_goals_last_14": int(10 + away_win_prob * 5)
                    }
                })
            
            conn.close()
            return predictions
        
        # Fallback: keine Vorhersagen verfügbar
        conn.close()
        return []
        
    except Exception as e:
        print(f"Error in get_predictions_for_matchday: {str(e)}")
        return []

@app.get("/api/predictions")
async def get_predictions():
    """Vorhersage-Qualität (Legacy Endpoint)"""
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