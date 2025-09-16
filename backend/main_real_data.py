"""
Backend mit echten Bundesliga-Daten
Verwendet die neuen Tabellen teams_real und matches_real
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
    title="Kick Predictor API - Real Data Edition",
    description="API mit echten Bundesliga-Daten von OpenLigaDB",
    version="2.0.0"
)

# CORS-Einstellungen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datenbank-Pfad
DB_PATH = "/workspaces/kick-predictor/backend/kick_predictor_final.db"

def get_db_connection():
    """Erstelle Datenbankverbindung"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Datenbank nicht gefunden")
    return sqlite3.connect(DB_PATH)

def calculate_team_form(team_id: int, last_n_games: int = 14) -> Dict[str, Any]:
    """Berechne Team-Form basierend auf den letzten N Spielen (saisonübergreifend)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Hole die letzten N Spiele des Teams (neueste zuerst)
    cursor.execute("""
        SELECT season, matchday, home_team_id, away_team_id, home_goals, away_goals, match_date
        FROM matches_real 
        WHERE (home_team_id = ? OR away_team_id = ?) 
        AND is_finished = 1
        AND home_goals IS NOT NULL 
        AND away_goals IS NOT NULL
        ORDER BY season DESC, matchday DESC
        LIMIT ?
    """, (team_id, team_id, last_n_games))
    
    matches = cursor.fetchall()
    conn.close()
    
    if not matches:
        return {
            "games_played": 0,
            "points": 0,
            "avg_points": 0.0,
            "form_percentage": 0.0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0
        }
    
    total_points = 0
    total_goals_for = 0
    total_goals_against = 0
    
    for match in matches:
        season, matchday, home_id, away_id, home_goals, away_goals, match_date = match
        
        if home_id == team_id:
            # Team spielte zu Hause
            team_goals = home_goals
            opponent_goals = away_goals
        else:
            # Team spielte auswärts
            team_goals = away_goals
            opponent_goals = home_goals
        
        total_goals_for += team_goals
        total_goals_against += opponent_goals
        
        # Punkte berechnen
        if team_goals > opponent_goals:
            total_points += 3  # Sieg
        elif team_goals == opponent_goals:
            total_points += 1  # Unentschieden
        # Niederlage = 0 Punkte
    
    games_played = len(matches)
    avg_points = total_points / games_played if games_played > 0 else 0
    max_possible_points = games_played * 3
    form_percentage = (total_points / max_possible_points * 100) if max_possible_points > 0 else 0
    
    return {
        "games_played": games_played,
        "points": total_points,
        "avg_points": round(avg_points, 2),
        "form_percentage": round(form_percentage, 1),
        "goals_for": total_goals_for,
        "goals_against": total_goals_against,
        "goal_difference": total_goals_for - total_goals_against
    }

def calculate_current_table() -> List[Dict[str, Any]]:
    """Berechne aktuelle Tabelle basierend auf Saison 2024/25"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Hole alle Teams mit Logo-URLs aus der Datenbank
    cursor.execute("SELECT team_id, name, short_name, icon_url FROM teams_real ORDER BY name")
    teams = cursor.fetchall()
    
    table = []
    
    for team in teams:
        team_id, team_name, short_name, icon_url = team
        
        # Hole alle Spiele des Teams in der aktuellen Saison
        cursor.execute("""
            SELECT home_team_id, away_team_id, home_goals, away_goals
            FROM matches_real 
            WHERE (home_team_id = ? OR away_team_id = ?) 
            AND season = '2025'
            AND is_finished = 1
            AND home_goals IS NOT NULL 
            AND away_goals IS NOT NULL
        """, (team_id, team_id))
        
        matches = cursor.fetchall()
        
        # Statistiken berechnen
        games_played = len(matches)
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for match in matches:
            home_id, away_id, home_goals, away_goals = match
            
            if home_id == team_id:
                # Team spielte zu Hause
                team_goals = home_goals
                opponent_goals = away_goals
            else:
                # Team spielte auswärts
                team_goals = away_goals
                opponent_goals = home_goals
            
            goals_for += team_goals
            goals_against += opponent_goals
            
            if team_goals > opponent_goals:
                wins += 1
            elif team_goals == opponent_goals:
                draws += 1
            else:
                losses += 1
        
        points = wins * 3 + draws
        goal_difference = goals_for - goals_against
        
        table.append({
            "team": {
                "id": team_id,
                "name": team_name,
                "short_name": short_name,
                "logo_url": icon_url or ""
            },
            "matches_played": games_played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goal_difference,
            "points": points
        })
    
    # Sortiere nach Punkten, dann nach Tordifferenz, dann nach geschossenen Toren
    table.sort(key=lambda x: (-x["points"], -x["goal_difference"], -x["goals_for"]))
    
    # Füge Position hinzu
    for i, entry in enumerate(table):
        entry["position"] = i + 1
    
    conn.close()
    return table

@app.get("/health")
async def health_check():
    """Health Check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM teams_real")
        team_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2025'")
        current_matches = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2024'")
        previous_matches = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "teams_count": team_count,
            "current_season_matches": current_matches,
            "previous_season_matches": previous_matches,
            "data_source": "real_bundesliga_data"
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
        "message": "API mit echten Bundesliga-Daten funktioniert!",
        "service": "Kick Predictor Backend - Real Data Edition",
        "data_source": "OpenLigaDB_real_data",
        "seasons": ["2024/25 (current)", "2023/24 (historical)"]
    }

@app.get("/api/teams")
async def get_teams():
    """Hole alle Teams aus der Datenbank"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT team_id, name, short_name, icon_url, synced_at
            FROM teams_real 
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

@app.get("/api/matchday-info")
async def get_matchday_info():
    """Hole aktuelle Spieltag-Informationen"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Finde den letzten gespielten Spieltag
        cursor.execute("""
            SELECT MAX(matchday) 
            FROM matches_real 
            WHERE season = '2025' AND is_finished = 1
        """)
        result = cursor.fetchone()
        last_played_matchday = result[0] if result and result[0] else 3
        
        # Der nächste Spieltag ist der erste noch nicht gespielte
        next_matchday = last_played_matchday + 1
        
        conn.close()
        
        return {
            "current_matchday": next_matchday,
            "next_matchday": next_matchday,
            "predictions_available_until": next_matchday,
            "season": "2024/25",
            "completed_matchdays": last_played_matchday,
            "last_played_matchday": last_played_matchday
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matchday info: {str(e)}")

@app.get("/api/predictions/{matchday}")
async def get_predictions(matchday: int):
    """Hole Vorhersagen/Matches für einen bestimmten Spieltag"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.match_id, m.home_team_name, m.away_team_name, m.match_date, 
                   m.matchday, m.season, m.is_finished, m.home_goals, m.away_goals,
                   ht.team_id as home_team_id, at.team_id as away_team_id
            FROM matches_real m
            LEFT JOIN teams_real ht ON m.home_team_id = ht.team_id
            LEFT JOIN teams_real at ON m.away_team_id = at.team_id
            WHERE m.matchday = ? AND m.season = '2025'
            ORDER BY m.match_date
        """, (matchday,))
        matches = cursor.fetchall()
        
        predictions = []
        for match in matches:
            match_id, home_name, away_name, match_date, md, season, is_finished, home_goals, away_goals, home_id, away_id = match
            
            # Berechne Form für beide Teams
            home_form = calculate_team_form(home_id) if home_id else {"form_percentage": 50.0}
            away_form = calculate_team_form(away_id) if away_id else {"form_percentage": 50.0}
            
            # Einfache Wahrscheinlichkeitsberechnung basierend auf Form
            home_form_factor = home_form["form_percentage"] / 100
            away_form_factor = away_form["form_percentage"] / 100
            
            # Basis-Wahrscheinlichkeiten (leicht zugunsten Heimteam)
            home_base = 0.4
            draw_base = 0.3
            away_base = 0.3
            
            # Anpassung basierend auf Form
            form_diff = home_form_factor - away_form_factor
            home_win_prob = max(0.1, min(0.8, home_base + form_diff * 0.3))
            away_win_prob = max(0.1, min(0.8, away_base - form_diff * 0.3))
            draw_prob = max(0.1, 1.0 - home_win_prob - away_win_prob)
            
            # Normalisierung
            total = home_win_prob + draw_prob + away_win_prob
            home_win_prob /= total
            draw_prob /= total
            away_win_prob /= total
            
            # Predicted Score basierend auf Form
            home_expected = 1.0 + (home_form_factor - 0.5)
            away_expected = 1.0 + (away_form_factor - 0.5)
            predicted_score = f"{max(0, round(home_expected))}:{max(0, round(away_expected))}"
            
            predictions.append({
                "match": {
                    "id": match_id,
                    "home_team": {"id": home_id, "name": home_name, "short_name": home_name[:3].upper()},
                    "away_team": {"id": away_id, "name": away_name, "short_name": away_name[:3].upper()},
                    "date": match_date,
                    "matchday": md,
                    "season": season,
                    "is_finished": is_finished,
                    "actual_score": f"{home_goals}:{away_goals}" if is_finished and home_goals is not None else None
                },
                "home_win_prob": round(home_win_prob, 3),
                "draw_prob": round(draw_prob, 3),
                "away_win_prob": round(away_win_prob, 3),
                "predicted_score": predicted_score,
                "form_factors": {
                    "home_form": round(home_form["form_percentage"], 1),
                    "away_form": round(away_form["form_percentage"], 1),
                    "home_goals_last_14": home_form["goals_for"],
                    "away_goals_last_14": away_form["goals_for"]
                }
            })
        
        conn.close()
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching predictions: {str(e)}")

@app.get("/api/table")
async def get_table():
    """Hole aktuelle Tabelle"""
    try:
        return calculate_current_table()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching table: {str(e)}")

@app.get("/api/team/{team_id}/form")
async def get_team_form(team_id: int):
    """Hole Team-Form der letzten 14 Spiele"""
    try:
        form_data = calculate_team_form(team_id, 14)
        return {
            "form": form_data["avg_points"],
            "team_id": team_id,
            "details": form_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team form: {str(e)}")

@app.get("/api/team/{team_id}/matches")
async def get_team_matches(team_id: int):
    """Hole die letzten 14 Spiele eines Teams"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.match_id, m.season, m.matchday, m.home_team_name, m.away_team_name, 
                   m.match_date, m.home_goals, m.away_goals, m.home_team_id, m.away_team_id
            FROM matches_real m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
            AND m.is_finished = 1
            AND m.home_goals IS NOT NULL
            ORDER BY m.season DESC, m.matchday DESC
            LIMIT 14
        """, (team_id, team_id))
        matches = cursor.fetchall()
        
        results = []
        for match in matches:
            match_id, season, matchday, home_name, away_name, match_date, home_goals, away_goals, home_id, away_id = match
            
            # Bestimme Team-Perspektive
            if home_id == team_id:
                team_goals = home_goals
                opponent_goals = away_goals
                is_home = True
                opponent_name = away_name
            else:
                team_goals = away_goals
                opponent_goals = home_goals
                is_home = False
                opponent_name = home_name
            
            # Ergebnis-Typ
            if team_goals > opponent_goals:
                result_type = "win"
            elif team_goals == opponent_goals:
                result_type = "draw"
            else:
                result_type = "loss"
            
            results.append({
                "match": {
                    "id": match_id,
                    "season": season,
                    "matchday": matchday,
                    "home_team": {"id": home_id, "name": home_name},
                    "away_team": {"id": away_id, "name": away_name},
                    "date": match_date,
                    "opponent": opponent_name,
                    "is_home": is_home
                },
                "home_goals": home_goals,
                "away_goals": away_goals,
                "team_goals": team_goals,
                "opponent_goals": opponent_goals,
                "result_type": result_type,
                "home_xg": 1.2,  # Placeholder für xG
                "away_xg": 1.1
            })
        
        conn.close()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team matches: {str(e)}")

@app.get("/api/database-stats")
async def get_database_stats():
    """Hole Datenbankstatistiken der echten Daten"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM teams_real")
        teams_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2025'")
        current_matches = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2024'")
        previous_matches = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2025' AND is_finished = 1")
        finished_current = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches_real WHERE season = '2024' AND is_finished = 1")
        finished_previous = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "teams_count": teams_count,
            "current_season_matches": current_matches,
            "previous_season_matches": previous_matches,
            "finished_current_season": finished_current,
            "finished_previous_season": finished_previous,
            "total_matches": current_matches + previous_matches,
            "data_source": "real_bundesliga_openligadb",
            "last_sync": "2024/25 Season: 3 Spieltage, 2023/24 Season: Complete"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "teams_count": 0,
            "current_season_matches": 0,
            "previous_season_matches": 0,
            "status": "database_error"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)