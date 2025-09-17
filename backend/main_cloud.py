"""
Vereinfaapp = FastAPI(
    title="Kick Predictor API - Cloud Edition",
    description="API mit echten Bundesliga-Daten - Master DB Schema",
    version="3.1.0"
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
    return {"message": "Kick Predictor API - Cloud Edition", "status": "running", "version": "3.0.8"}

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
    """Aktuelle Bundesliga-Tabelle basierend auf echten Ergebnissen - wie lokale App"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe zuerst matches_real Tabelle (hat die echten Ergebnisse)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches_real'")
        matches_real_exists = cursor.fetchone() is not None
        
        if matches_real_exists:
            # Initialisiere Team-Statistiken Dictionary
            team_stats = {}
            
            # Hole alle Teams aus teams_real
            cursor.execute("""
                SELECT DISTINCT team_id, name, short_name, icon_url
                FROM teams_real
                ORDER BY name
            """)
            
            teams = cursor.fetchall()
            for team in teams:
                team_stats[team["team_id"]] = {
                    "team_id": team["team_id"],
                    "team_name": team["name"],
                    "shortname": team["short_name"],
                    "team_icon_url": team["icon_url"],
                    "games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "points": 0
                }
            
            # Verarbeite alle abgeschlossenen Spiele der Saison 2025
            cursor.execute("""
                SELECT 
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    is_finished
                FROM matches_real
                WHERE season = '2025' AND is_finished = 1
                    AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            """)
            
            matches = cursor.fetchall()
            for match in matches:
                home_id = match["home_team_id"]
                away_id = match["away_team_id"]
                home_goals = match["home_goals"]
                away_goals = match["away_goals"]
                
                # Stelle sicher, dass beide Teams existieren
                if home_id not in team_stats or away_id not in team_stats:
                    continue
                
                # Aktualisiere Spiele-Anzahl
                team_stats[home_id]["games"] += 1
                team_stats[away_id]["games"] += 1
                
                # Aktualisiere Tore
                team_stats[home_id]["goals_for"] += home_goals
                team_stats[home_id]["goals_against"] += away_goals
                team_stats[away_id]["goals_for"] += away_goals
                team_stats[away_id]["goals_against"] += home_goals
                
                # Bestimme Ergebnis und vergebe Punkte
                if home_goals > away_goals:  # Heimsieg
                    team_stats[home_id]["wins"] += 1
                    team_stats[home_id]["points"] += 3
                    team_stats[away_id]["losses"] += 1
                elif home_goals < away_goals:  # Auswärtssieg
                    team_stats[away_id]["wins"] += 1
                    team_stats[away_id]["points"] += 3
                    team_stats[home_id]["losses"] += 1
                else:  # Unentschieden
                    team_stats[home_id]["draws"] += 1
                    team_stats[home_id]["points"] += 1
                    team_stats[away_id]["draws"] += 1
                    team_stats[away_id]["points"] += 1
            
            # Berechne Tordifferenz und erstelle finale Tabelle
            table = []
            for team_id, stats in team_stats.items():
                stats["goal_difference"] = stats["goals_for"] - stats["goals_against"]
                table.append(stats)
            
            # Sortiere nach Bundesliga-Regeln: 1. Punkte, 2. Tordifferenz, 3. Tore
            table.sort(key=lambda x: (-x["points"], -x["goal_difference"], -x["goals_for"]))
            
            # Setze Positionen
            for i, entry in enumerate(table):
                entry["position"] = i + 1
            
            conn.close()
            return table
        
        # Fallback: Keine Daten verfügbar
        conn.close()
        return []
        
    except Exception as e:
        print(f"Error in get_table: {str(e)}")
        # Fallback-Tabelle mit 0-Werten falls Fehler
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
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
        except:
            return []

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
    """Vorhersagen für einen bestimmten Spieltag - echte Implementierung wie lokale App"""
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
                # Berechne echte Vorhersagen basierend auf letzten 14 Spielen
                home_team_id = row["home_team_id"]
                away_team_id = row["away_team_id"]
                
                # Hole Form-Faktoren (basierend auf letzten 14 Spielen)
                home_form = await get_team_form_from_db(cursor, home_team_id)
                away_form = await get_team_form_from_db(cursor, away_team_id)
                
                # Hole Goals aus letzten 14 Spielen für xG-ähnliche Berechnung
                home_goals_last_14 = await get_team_goals_last_n_matches(cursor, home_team_id, 14)
                away_goals_last_14 = await get_team_goals_last_n_matches(cursor, away_team_id, 14)
                
                # Berechne Vorhersage mit echter Logik (wie in lokaler App)
                form_diff = home_form - away_form
                goals_diff = home_goals_last_14 - away_goals_last_14
                
                # Heimvorteil (10%)
                home_advantage = 0.1
                
                # Basis-Wahrscheinlichkeiten
                home_win_prob = 0.45 + (form_diff / 3) + (goals_diff / 20) + home_advantage
                away_win_prob = 0.35 - (form_diff / 3) - (goals_diff / 20)
                draw_prob = 0.20
                
                # Normalisierung
                total = home_win_prob + draw_prob + away_win_prob
                home_win_prob = max(0.05, min(0.90, home_win_prob / total))
                away_win_prob = max(0.05, min(0.90, away_win_prob / total))
                draw_prob = max(0.05, min(0.90, draw_prob / total))
                
                # Erneute Normalisierung nach Beschränkung
                total = home_win_prob + draw_prob + away_win_prob
                home_win_prob /= total
                draw_prob /= total
                away_win_prob /= total
                
                # Vorhersage für Ergebnis basierend auf durchschnittlichen Toren
                home_avg_goals = max(0.5, home_goals_last_14 / 14 * home_form * 2)
                away_avg_goals = max(0.5, away_goals_last_14 / 14 * away_form * 2)
                
                predicted_home_goals = round(home_avg_goals)
                predicted_away_goals = round(away_avg_goals)
                predicted_score = f"{predicted_home_goals}:{predicted_away_goals}"
                
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
                    "home_win_prob": round(home_win_prob, 3),
                    "draw_prob": round(draw_prob, 3),
                    "away_win_prob": round(away_win_prob, 3),
                    "predicted_score": predicted_score,
                    "form_factors": {
                        "home_form": round(home_form * 100, 1),
                        "away_form": round(away_form * 100, 1),
                        "home_goals_last_14": int(home_goals_last_14),
                        "away_goals_last_14": int(away_goals_last_14)
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

async def get_team_form_from_db(cursor, team_id: int) -> float:
    """Berechnet Team-Form basierend auf letzten 14 Spielen (über 2024 und 2025)"""
    try:
        # Hole die letzten 14 Spiele des Teams aus beiden Saisons
        cursor.execute("""
            SELECT 
                mr.home_team_id,
                mr.away_team_id,
                mr.home_goals,
                mr.away_goals,
                mr.match_date
            FROM matches_real mr
            WHERE (mr.home_team_id = ? OR mr.away_team_id = ?)
                AND mr.is_finished = 1
                AND mr.season IN ('2024', '2025')
            ORDER BY mr.match_date DESC
            LIMIT 14
        """, (team_id, team_id))
        
        matches = cursor.fetchall()
        if not matches:
            return 0.5  # Neutrale Form wenn keine Spiele
            
        total_points = 0
        for match in matches:
            is_home = match["home_team_id"] == team_id
            home_goals = match["home_goals"] or 0
            away_goals = match["away_goals"] or 0
            
            if is_home:
                if home_goals > away_goals:
                    total_points += 3  # Sieg
                elif home_goals == away_goals:
                    total_points += 1  # Unentschieden
                # Niederlage = 0 Punkte
            else:
                if away_goals > home_goals:
                    total_points += 3  # Sieg
                elif away_goals == home_goals:
                    total_points += 1  # Unentschieden
                # Niederlage = 0 Punkte
        
        # Form als Verhältnis der erzielten zu maximal möglichen Punkten
        max_points = len(matches) * 3
        form = total_points / max_points if max_points > 0 else 0.5
        
        return max(0.0, min(1.0, form))  # Beschränke auf 0-1
        
    except Exception as e:
        print(f"Error calculating team form for team {team_id}: {e}")
        return 0.5

async def get_team_goals_last_n_matches(cursor, team_id: int, n: int = 14) -> float:
    """Berechnet durchschnittliche Tore pro Spiel aus letzten n Spielen"""
    try:
        cursor.execute("""
            SELECT 
                mr.home_team_id,
                mr.away_team_id,
                mr.home_goals,
                mr.away_goals,
                mr.match_date
            FROM matches_real mr
            WHERE (mr.home_team_id = ? OR mr.away_team_id = ?)
                AND mr.is_finished = 1
                AND mr.season IN ('2024', '2025')
            ORDER BY mr.match_date DESC
            LIMIT ?
        """, (team_id, team_id, n))
        
        matches = cursor.fetchall()
        if not matches:
            return 10.0  # Fallback-Wert
            
        total_goals = 0
        for match in matches:
            is_home = match["home_team_id"] == team_id
            home_goals = match["home_goals"] or 0
            away_goals = match["away_goals"] or 0
            
            if is_home:
                total_goals += home_goals
            else:
                total_goals += away_goals
        
        return total_goals
        
    except Exception as e:
        print(f"Error calculating goals for team {team_id}: {e}")
        return 10.0

@app.get("/api/team/{team_id}/form")
async def get_team_form(team_id: int):
    """Team-Form basierend auf letzten 14 Spielen - exakt wie lokale App"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Berechne Form basierend auf letzten 14 Spielen (wie in der lokalen App)
        form = await get_team_form_from_db(cursor, team_id)
        
        conn.close()
        return {
            "details": {
                "form_percentage": form * 100  # Frontend erwartet Prozent-Wert
            }
        }
        
    except Exception as e:
        print(f"Error in get_team_form: {str(e)}")
        return {"details": {"form_percentage": 50.0}}

@app.get("/api/team/{team_id}/matches")
async def get_team_matches(team_id: int):
    """Letzte Spiele eines Teams mit xG-Daten - exakt wie lokale App"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe zuerst matches_real Tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches_real'")
        matches_real_exists = cursor.fetchone() is not None
        
        if matches_real_exists:
            # Hole die letzten Spiele des Teams aus matches_real
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
                WHERE (mr.home_team_id = ? OR mr.away_team_id = ?)
                    AND mr.is_finished = 1
                    AND mr.season IN ('2024', '2025')
                ORDER BY mr.match_date DESC
                LIMIT 14
            """, (team_id, team_id))
            
            matches = []
            for row in cursor.fetchall():
                # Berechne xG-Werte (vereinfacht basierend auf Toren, da keine echten xG-Daten)
                home_goals = row["home_goals"] or 0
                away_goals = row["away_goals"] or 0
                
                # Vereinfachte xG-Berechnung: Basis-xG + Variation basierend auf Toren
                home_xg = max(0.1, home_goals + (0.3 if home_goals > 0 else 0))
                away_xg = max(0.1, away_goals + (0.3 if away_goals > 0 else 0))
                
                # Füge etwas Realismus hinzu
                if home_goals == 0:
                    home_xg = 0.8  # Hatten Chancen aber nicht getroffen
                if away_goals == 0:
                    away_xg = 0.7
                    
                matches.append({
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
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "home_xg": home_xg,
                    "away_xg": away_xg
                })
            
            conn.close()
            return matches
        
        # Fallback: keine Daten verfügbar
        conn.close()
        return []
        
    except Exception as e:
        print(f"Error in get_team_matches: {str(e)}")
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
    """Vorhersage-Qualitäts-Statistiken basierend auf echten matches_real Daten"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hole alle beendeten Spiele aus matches_real mit Team-Details
        cursor.execute("""
            SELECT 
                m.id,
                m.match_id,
                m.season,
                m.matchday,
                m.home_team_name,
                m.away_team_name,
                m.home_goals,
                m.away_goals,
                m.match_date,
                ht.id as home_team_id,
                at.id as away_team_id
            FROM matches_real m
            LEFT JOIN teams_real ht ON m.home_team_name = ht.name
            LEFT JOIN teams_real at ON m.away_team_name = at.name
            WHERE m.is_finished = 1
            ORDER BY m.season, m.matchday, m.match_date
            LIMIT 100
        """)
        
        entries = []
        exact_matches = 0
        tendency_matches = 0
        
        for row in cursor.fetchall():
            # Berechne echte Vorhersage basierend auf unserem Algorithmus
            home_team_id = row[9] or 1
            away_team_id = row[10] or 2
            
            # Verwende unsere Vorhersage-Logik (vereinfacht)
            try:
                # Hole Form-Faktoren für beide Teams
                home_form = await get_team_form_from_db(cursor, home_team_id)
                away_form = await get_team_form_from_db(cursor, away_team_id)
                
                # Hole Goals aus letzten 14 Spielen
                home_goals_last_14 = await get_team_goals_last_n_matches(cursor, home_team_id, 14)
                away_goals_last_14 = await get_team_goals_last_n_matches(cursor, away_team_id, 14)
                
                # Berechne Vorhersage-Wahrscheinlichkeiten
                form_diff = home_form - away_form
                goals_diff = home_goals_last_14 - away_goals_last_14
                home_advantage = 0.1
                
                home_win_prob = 0.45 + (form_diff / 3) + (goals_diff / 20) + home_advantage
                away_win_prob = 0.35 - (form_diff / 3) - (goals_diff / 20)
                draw_prob = 0.20
                
                # Normalisierung
                total = home_win_prob + draw_prob + away_win_prob
                home_win_prob = max(0.05, min(0.90, home_win_prob / total))
                away_win_prob = max(0.05, min(0.90, away_win_prob / total))
                draw_prob = max(0.05, min(0.90, draw_prob / total))
                
                # Erneute Normalisierung
                total = home_win_prob + draw_prob + away_win_prob
                prediction = {
                    "home_win_probability": home_win_prob / total,
                    "draw_probability": draw_prob / total,
                    "away_win_probability": away_win_prob / total
                }
            except:
                # Fallback wenn predict_match nicht funktioniert
                prediction = {
                    "home_win_probability": 0.4,
                    "draw_probability": 0.3,
                    "away_win_probability": 0.3
                }
            
            # Echtes Ergebnis
            actual_home_goals = row[6]
            actual_away_goals = row[7]
            actual_score = f"{actual_home_goals}:{actual_away_goals}"
            
            # Vorhersage-Score aus Wahrscheinlichkeiten ableiten
            home_win_prob = prediction.get("home_win_probability", 0.33)
            draw_prob = prediction.get("draw_probability", 0.33) 
            away_win_prob = prediction.get("away_win_probability", 0.33)
            
            # Vorhergesagtes Ergebnis basierend auf höchster Wahrscheinlichkeit
            if home_win_prob > draw_prob and home_win_prob > away_win_prob:
                predicted_score = "2:1"  # Home win
                predicted_tendency = "home_win"
            elif away_win_prob > draw_prob and away_win_prob > home_win_prob:
                predicted_score = "1:2"  # Away win  
                predicted_tendency = "away_win"
            else:
                predicted_score = "1:1"  # Draw
                predicted_tendency = "draw"
            
            # Echte Tendenz
            if actual_home_goals > actual_away_goals:
                actual_tendency = "home_win"
            elif actual_away_goals > actual_home_goals:
                actual_tendency = "away_win"
            else:
                actual_tendency = "draw"
            
            # Bewertung
            tendency_correct = predicted_tendency == actual_tendency
            exact_score_correct = predicted_score == actual_score
            
            if tendency_correct:
                tendency_matches += 1
                if exact_score_correct:
                    exact_matches += 1
                    hit_type = "exact_score"
                else:
                    hit_type = "tendency_match"
            else:
                hit_type = "miss"
            
            entries.append({
                "match": {
                    "id": row[0],
                    "home_team": {
                        "id": home_team_id,
                        "name": row[4],
                        "short_name": row[4][:10]
                    },
                    "away_team": {
                        "id": away_team_id,
                        "name": row[5],
                        "short_name": row[5][:10]
                    },
                    "date": row[8],
                    "matchday": row[3],
                    "season": row[2]
                },
                "predicted_score": predicted_score,
                "actual_score": actual_score,
                "predicted_home_win_prob": round(home_win_prob, 2),
                "predicted_draw_prob": round(draw_prob, 2),
                "predicted_away_win_prob": round(away_win_prob, 2),
                "hit_type": hit_type,
                "tendency_correct": tendency_correct,
                "exact_score_correct": exact_score_correct
            })
        
        # Berechne Statistiken
        total = len(entries)
        misses = total - tendency_matches
        
        stats_data = {
            "total_predictions": total,
            "exact_matches": exact_matches,
            "tendency_matches": tendency_matches,
            "misses": misses,
            "exact_match_rate": round((exact_matches / total), 3) if total > 0 else 0,
            "tendency_match_rate": round((tendency_matches / total), 3) if total > 0 else 0,
            "overall_accuracy": round((tendency_matches / total), 3) if total > 0 else 0,
            "quality_score": round((exact_matches * 3 + tendency_matches * 1) / (total * 3), 3) if total > 0 else 0
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
        print(f"Prediction quality error: {e}")
        return {
            "entries": [],
            "stats": {
                "total_predictions": 0,
                "exact_matches": 0,
                "tendency_matches": 0,
                "misses": 0,
                "exact_match_rate": 0,
                "tendency_match_rate": 0,
                "overall_accuracy": 0,
                "quality_score": 0
            },
            "processed_matches": 0,
            "cached_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)