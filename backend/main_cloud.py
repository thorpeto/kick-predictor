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
                COUNT(CASE WHEN (m.team1_id = t.team_id AND m.points_team1 > m.points_team2) 
                            OR (m.team2_id = t.team_id AND m.points_team2 > m.points_team1) THEN 1 END) as wins,
                COUNT(CASE WHEN m.points_team1 = m.points_team2 AND (m.team1_id = t.team_id OR m.team2_id = t.team_id) THEN 1 END) as draws,
                COUNT(CASE WHEN (m.team1_id = t.team_id AND m.points_team1 < m.points_team2) 
                            OR (m.team2_id = t.team_id AND m.points_team2 < m.points_team1) THEN 1 END) as losses,
                SUM(CASE WHEN m.team1_id = t.team_id THEN COALESCE(m.points_team1, 0) ELSE 0 END) +
                SUM(CASE WHEN m.team2_id = t.team_id THEN COALESCE(m.points_team2, 0) ELSE 0 END) as goals_for,
                SUM(CASE WHEN m.team1_id = t.team_id THEN COALESCE(m.points_team2, 0) ELSE 0 END) +
                SUM(CASE WHEN m.team2_id = t.team_id THEN COALESCE(m.points_team1, 0) ELSE 0 END) as goals_against,
                COUNT(CASE WHEN (m.team1_id = t.team_id AND m.points_team1 > m.points_team2) 
                            OR (m.team2_id = t.team_id AND m.points_team2 > m.points_team1) THEN 1 END) * 3 +
                COUNT(CASE WHEN m.points_team1 = m.points_team2 AND (m.team1_id = t.team_id OR m.team2_id = t.team_id) THEN 1 END) as points
            FROM teams_real t
            LEFT JOIN matches_real m ON (t.team_id = m.team1_id OR t.team_id = m.team2_id) 
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)