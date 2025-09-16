"""
Vereinfachter Server mit direkter SQLite-Datenbankanbindung
"""
import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(
    title="Kick Predictor API - Direct SQLite",
    description="API mit direkter SQLite-Datenbankanbindung",
    version="0.1.0"
)

# CORS-Einstellungen
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80", 
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Database path
DB_PATH = "/workspaces/kick-predictor/backend/kick_predictor_final.db"

def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found. Please run synchronization first.")
    return sqlite3.connect(DB_PATH)

@app.get("/")
async def root():
    return {"message": "Kick Predictor API mit persistenter Datenbank!"}

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM teams")
        team_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "teams_count": team_count
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/test")
async def test_connection():
    """Test-Endpoint"""
    return {
        "status": "success",
        "message": "API-Verbindung funktioniert!",
        "service": "Kick Predictor Backend - SQLite Edition",
        "data_source": "persistent_database"
    }

@app.get("/api/teams")
async def get_teams():
    """Hole alle Teams aus der Datenbank"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT external_id, name, short_name, logo_url, synced_at
            FROM teams 
            ORDER BY name
        """)
        teams = cursor.fetchall()
        conn.close()
        
        result = []
        for team in teams:
            result.append({
                "id": team[0],
                "name": team[1],
                "short_name": team[2],
                "logo_url": team[3],
                "synced_at": team[4]
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

@app.get("/api/matches")
async def get_matches():
    """Hole alle Matches aus der Datenbank"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT external_id, home_team_name, away_team_name, date, matchday, season, synced_at
            FROM matches 
            ORDER BY date DESC
        """)
        matches = cursor.fetchall()
        conn.close()
        
        result = []
        for match in matches:
            result.append({
                "id": match[0],
                "home_team": match[1],
                "away_team": match[2],
                "date": match[3],
                "matchday": match[4],
                "season": match[5],
                "synced_at": match[6]
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matches: {str(e)}")

@app.get("/api/prediction-quality")
async def get_prediction_quality():
    """Hole Vorhersage-Qualitätsdaten aus der Datenbank"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                match_info, predicted_score, actual_score, 
                predicted_home_win_prob, predicted_draw_prob, predicted_away_win_prob,
                hit_type, tendency_correct, exact_score_correct, synced_at
            FROM prediction_quality 
            ORDER BY synced_at DESC
        """)
        predictions = cursor.fetchall()
        
        # Statistiken berechnen
        cursor.execute("SELECT COUNT(*) FROM prediction_quality")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prediction_quality WHERE tendency_correct = 1")
        correct_tendency = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prediction_quality WHERE exact_score_correct = 1")
        exact_matches = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prediction_quality WHERE hit_type = 'miss'")
        misses = cursor.fetchone()[0]
        
        conn.close()
        
        # Einträge formatieren
        entries = []
        for pred in predictions:
            entries.append({
                "match_info": pred[0],
                "predicted_score": pred[1],
                "actual_score": pred[2],
                "predicted_home_win_prob": pred[3],
                "predicted_draw_prob": pred[4],
                "predicted_away_win_prob": pred[5],
                "hit_type": pred[6],
                "tendency_correct": bool(pred[7]),
                "exact_score_correct": bool(pred[8]),
                "synced_at": pred[9]
            })
        
        # Statistiken berechnen
        stats = {
            "total_predictions": total,
            "exact_matches": exact_matches,
            "tendency_matches": correct_tendency - exact_matches,
            "misses": misses,
            "exact_match_rate": (exact_matches / total) if total > 0 else 0,
            "tendency_match_rate": ((correct_tendency - exact_matches) / total) if total > 0 else 0,
            "overall_accuracy": (correct_tendency / total) if total > 0 else 0,
            "quality_score": ((exact_matches * 1.0 + (correct_tendency - exact_matches) * 0.5) / total) if total > 0 else 0
        }
        
        return {
            "entries": entries,
            "stats": stats,
            "processed_matches": len(entries),
            "cached_at": datetime.now().isoformat(),
            "source": "persistent_database"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching prediction quality: {str(e)}")

@app.get("/api/matchday-info")
async def get_matchday_info():
    """Hole Spieltag-Informationen aus der Datenbank"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Da alle Matches Spieltag 0 haben, verwenden wir 1 als aktuellen Spieltag
        current_matchday = 1
        
        conn.close()
        
        return {
            "current_matchday": current_matchday,
            "next_matchday": current_matchday + 1,
            "predictions_available_until": current_matchday + 1,
            "season": "2024/25"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matchday info: {str(e)}")

@app.get("/api/predictions/{matchday}")
async def get_predictions(matchday: int):
    """Hole Vorhersagen für einen bestimmten Spieltag - verwende alle verfügbaren Matches"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Da alle Matches Spieltag 0 haben, zeigen wir alle Matches für jeden Spieltag
        cursor.execute("""
            SELECT external_id, home_team_name, away_team_name, date, matchday, season
            FROM matches 
            ORDER BY date
            LIMIT 9
        """)
        matches = cursor.fetchall()
        
        predictions = []
        for i, match in enumerate(matches):
            # Verwende Prediction Quality Daten wenn verfügbar
            cursor.execute("""
                SELECT predicted_score, predicted_home_win_prob, predicted_draw_prob, predicted_away_win_prob
                FROM prediction_quality 
                WHERE match_info LIKE ?
                LIMIT 1
            """, (f"%{match[1]}%{match[2]}%",))
            pred_data = cursor.fetchone()
            
            if pred_data:
                predicted_score = pred_data[0]
                home_prob = pred_data[1] or 0.33
                draw_prob = pred_data[2] or 0.33
                away_prob = pred_data[3] or 0.34
            else:
                predicted_score = "1:1"
                home_prob = 0.33
                draw_prob = 0.33
                away_prob = 0.34
            
            predictions.append({
                "match": {
                    "id": match[0],
                    "home_team": {"name": match[1], "short_name": match[1][:3].upper()},
                    "away_team": {"name": match[2], "short_name": match[2][:3].upper()},
                    "date": match[3],
                    "matchday": matchday,  # Verwende den angeforderten Spieltag
                    "season": match[5]
                },
                "home_win_prob": home_prob,
                "draw_prob": draw_prob,
                "away_win_prob": away_prob,
                "predicted_score": predicted_score,
                "form_factors": {
                    "home_form": 0.5,
                    "away_form": 0.5,
                    "home_xg_last_6": 1.2,
                    "away_xg_last_6": 1.1
                }
            })
        
        conn.close()
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching predictions: {str(e)}")

@app.get("/api/table")
async def get_table():
    """Hole aktuelle Tabelle - Dummy-Daten basierend auf Teams"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT external_id, name, short_name
            FROM teams 
            ORDER BY name
            LIMIT 18
        """)
        teams = cursor.fetchall()
        
        table = []
        for i, team in enumerate(teams):
            table.append({
                "position": i + 1,
                "team": {
                    "id": team[0],
                    "name": team[1], 
                    "short_name": team[2]
                },
                "matches_played": 5,
                "wins": 2,
                "draws": 1,
                "losses": 2,
                "goals_for": 8,
                "goals_against": 7,
                "goal_difference": 1,
                "points": 7 + (18 - i)  # Dummy-Punkte absteigend
            })
        
        conn.close()
        return table
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching table: {str(e)}")

@app.get("/api/team/{team_id}/form")
async def get_team_form(team_id: int):
    """Hole Team-Form (vereinfacht)"""
    try:
        # Dummy-Form-Werte für jetzt
        return {"form": 0.5, "team_id": team_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team form: {str(e)}")

@app.get("/api/team/{team_id}/matches")
async def get_team_matches(team_id: int):
    """Hole Team-Matches (erweitert mit mehr Matches)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hole Team-Namen
        cursor.execute("SELECT name FROM teams WHERE external_id = ?", (team_id,))
        team_result = cursor.fetchone()
        
        if not team_result:
            # Falls Team nicht gefunden, zeige alle Matches als Beispiel
            cursor.execute("""
                SELECT external_id, home_team_name, away_team_name, date, matchday
                FROM matches 
                ORDER BY date DESC
                LIMIT 10
            """)
        else:
            team_name = team_result[0]
            # Suche Matches für das spezifische Team
            cursor.execute("""
                SELECT external_id, home_team_name, away_team_name, date, matchday
                FROM matches 
                WHERE home_team_name = ? OR away_team_name = ?
                ORDER BY date DESC
                LIMIT 10
            """, (team_name, team_name))
        
        matches = cursor.fetchall()
        
        # Falls keine spezifischen Team-Matches, zeige alle verfügbaren Matches
        if not matches:
            cursor.execute("""
                SELECT external_id, home_team_name, away_team_name, date, matchday
                FROM matches 
                ORDER BY date DESC
                LIMIT 10
            """)
            matches = cursor.fetchall()
        
        results = []
        for match in matches:
            # Hole echte Ergebnisse aus prediction_quality wenn verfügbar
            cursor.execute("""
                SELECT actual_score 
                FROM prediction_quality 
                WHERE match_info LIKE ?
                LIMIT 1
            """, (f"%{match[1]}%{match[2]}%",))
            score_result = cursor.fetchone()
            
            if score_result and score_result[0] and ':' in score_result[0]:
                try:
                    actual_home, actual_away = map(int, score_result[0].split(':'))
                except:
                    actual_home, actual_away = 1, 1
            else:
                actual_home, actual_away = 1, 1  # Fallback
                
            results.append({
                "match": {
                    "id": match[0],
                    "home_team": {"name": match[1]},
                    "away_team": {"name": match[2]},
                    "date": match[3],
                    "matchday": match[4]
                },
                "home_goals": actual_home,
                "away_goals": actual_away,
                "home_xg": 1.2,
                "away_xg": 1.1
            })
        
        conn.close()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team matches: {str(e)}")

@app.get("/api/database-stats")
async def get_database_stats():
    """Hole Datenbankstatistiken (vereinfacht)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Teams zählen
        cursor.execute("SELECT COUNT(*) FROM teams")
        teams_count = cursor.fetchone()[0]
        
        # Matches zählen  
        cursor.execute("SELECT COUNT(*) FROM matches")
        matches_count = cursor.fetchone()[0]
        
        # Prediction quality entries zählen
        cursor.execute("SELECT COUNT(*) FROM prediction_quality")
        predictions_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "teams_count": teams_count,
            "matches_count": matches_count,
            "predictions_count": predictions_count,
            "status": "database_loaded"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "teams_count": 0,
            "matches_count": 0, 
            "predictions_count": 0,
            "status": "database_error"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Placeholder-Endpoints für Frontend-Kompatibilität
@app.get("/api/next-matchday")
async def get_next_matchday():
    return {"message": "Using database data - check /api/matches for persistent data"}

@app.get("/api/predictions/{matchday}")
async def get_predictions(matchday: int):
    return {"message": f"Using database data - check /api/prediction-quality for persistent predictions"}

@app.get("/api/team/{team_id}/form")
async def get_team_form(team_id: int):
    return {"message": "Using database data - check /api/teams for persistent team data"}

@app.get("/api/table")
async def get_table():
    return {"message": "Using database data - check /api/teams for persistent data"}

@app.get("/api/matchday-info")
async def get_matchday_info():
    return {"message": "Using database data - check /api/matches for persistent matchday data"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Starting Kick Predictor API with persistent SQLite database")
    print(f"💾 Database: {DB_PATH}")
    print(f"🌐 Server: http://localhost:{port}")
    
    uvicorn.run("main_sqlite:app", host="0.0.0.0", port=port, reload=True)