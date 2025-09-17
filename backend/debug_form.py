#!/usr/bin/env python3
"""
Debug für Form-Berechnung
"""
import asyncio
import sqlite3
import sys
import os

# Füge Backend-Verzeichnis zum Pfad hinzu
sys.path.append('/workspaces/kick-predictor/backend')

from main_cloud import get_db_connection, get_team_form_from_db, get_team_expected_goals

async def debug_form_calculation():
    print("🔍 Debug: Form-Berechnung...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe Bayern München
        cursor.execute("SELECT team_id, name FROM teams_real WHERE name LIKE '%Bayern%' LIMIT 1")
        bayern = cursor.fetchone()
        
        if bayern:
            bayern_id = bayern[0]  # team_id, nicht id!
            bayern_name = bayern[1]
            
            print(f"\n📊 Team: {bayern_name} (ID: {bayern_id})")
            
            # Prüfe Spiele für dieses Team
            cursor.execute("""
                SELECT 
                    mr.home_team_id,
                    mr.away_team_id,
                    mr.home_goals,
                    mr.away_goals,
                    mr.match_date,
                    mr.season
                FROM matches_real mr
                WHERE (mr.home_team_id = ? OR mr.away_team_id = ?)
                    AND mr.is_finished = 1
                    AND mr.season IN ('2024', '2025')
                ORDER BY mr.match_date DESC
                LIMIT 5
            """, (bayern_id, bayern_id))
            
            matches = cursor.fetchall()
            print(f"   Gefundene Spiele: {len(matches)}")
            
            for i, match in enumerate(matches):
                home_id = match[0]
                away_id = match[1]
                home_goals = match[2] or 0
                away_goals = match[3] or 0
                date = match[4]
                season = match[5]
                
                is_home = home_id == bayern_id
                result = "H" if (is_home and home_goals > away_goals) or (not is_home and away_goals > home_goals) else "D" if home_goals == away_goals else "A"
                points = 3 if result == "H" else 1 if result == "D" else 0
                
                position = "Heim" if is_home else "Auswärts"
                print(f"   {i+1}. {date} ({season}): {home_goals}:{away_goals} ({position}) -> {points} Punkte")
            
            # Berechne Form
            form = await get_team_form_from_db(cursor, bayern_id)
            print(f"   ✅ Berechnete Form: {form:.3f} ({form*100:.1f}%)")
            
            # Berechne Expected Goals
            xg = await get_team_expected_goals(cursor, bayern_id, 14)
            print(f"   ⚽ Expected Goals: {xg:.2f}")
            
        # Teste auch mit Leipzig
        cursor.execute("SELECT team_id, name FROM teams_real WHERE name LIKE '%Leipzig%' LIMIT 1")
        leipzig = cursor.fetchone()
        
        if leipzig:
            leipzig_id = leipzig[0]  # team_id
            leipzig_name = leipzig[1]
            
            print(f"\n📊 Team: {leipzig_name} (ID: {leipzig_id})")
            
            leipzig_form = await get_team_form_from_db(cursor, leipzig_id)
            leipzig_xg = await get_team_expected_goals(cursor, leipzig_id, 14)
            
            print(f"   ✅ Form: {leipzig_form:.3f} ({leipzig_form*100:.1f}%)")
            print(f"   ⚽ Expected Goals: {leipzig_xg:.2f}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_form_calculation())