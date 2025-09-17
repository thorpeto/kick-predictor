#!/usr/bin/env python3
"""
Test für das einheitliche xG-Vorhersagemodell
"""
import asyncio
import sqlite3
import sys
import os

# Füge Backend-Verzeichnis zum Pfad hinzu
sys.path.append('/workspaces/kick-predictor/backend')

from main_cloud import get_db_connection, predict_match_xg

async def test_xg_model():
    print("🧪 Teste das einheitliche xG-Vorhersagemodell...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hole ein echtes Spiel zum Testen
        cursor.execute("""
            SELECT 
                m.home_team_name,
                m.away_team_name,
                m.home_goals,
                m.away_goals,
                m.home_team_id,
                m.away_team_id
            FROM matches_real m
            WHERE m.is_finished = 1
            ORDER BY m.season DESC, m.matchday DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("❌ Keine Spiele gefunden")
            return
            
        home_team = row[0]
        away_team = row[1]
        actual_home = row[2]
        actual_away = row[3]
        home_team_id = row[4] or 1
        away_team_id = row[5] or 2
        
        print(f"\n📊 Test-Spiel: {home_team} vs {away_team}")
        print(f"🎯 Echtes Ergebnis: {actual_home}:{actual_away}")
        
        # Teste xG-Vorhersagemodell
        prediction = await predict_match_xg(cursor, home_team_id, away_team_id)
        
        print(f"\n🤖 xG-Vorhersage:")
        print(f"   Ergebnis: {prediction['predicted_score']}")
        print(f"   Wahrscheinlichkeiten:")
        print(f"     Heimsieg: {prediction['home_win_prob']:.1%}")
        print(f"     Unentschieden: {prediction['draw_prob']:.1%}")
        print(f"     Auswärtssieg: {prediction['away_win_prob']:.1%}")
        print(f"   Expected Goals:")
        print(f"     {home_team}: {prediction['home_xg']:.2f}")
        print(f"     {away_team}: {prediction['away_xg']:.2f}")
        print(f"   Form:")
        print(f"     {home_team}: {prediction['home_form']:.1%}")
        print(f"     {away_team}: {prediction['away_form']:.1%}")
        
        # Teste mit verschiedenen Teams
        print(f"\n🔄 Teste weitere Team-Kombinationen...")
        
        # Bayern vs Dortmund
        cursor.execute("SELECT team_id FROM teams_real WHERE name LIKE '%Bayern%' LIMIT 1")
        bayern_id = cursor.fetchone()
        cursor.execute("SELECT team_id FROM teams_real WHERE name LIKE '%Dortmund%' LIMIT 1") 
        dortmund_id = cursor.fetchone()
        
        if bayern_id and dortmund_id:
            bayern_result = await predict_match_xg(cursor, bayern_id[0], dortmund_id[0])
            print(f"   Bayern vs Dortmund: {bayern_result['predicted_score']} (H:{bayern_result['home_win_prob']:.1%})")
            
        # Prüfe auf 1:1-Problem
        all_scores = []
        cursor.execute("SELECT team_id FROM teams_real LIMIT 6")
        team_ids = [row[0] for row in cursor.fetchall()]
        
        for i in range(0, len(team_ids)-1, 2):
            try:
                pred = await predict_match_xg(cursor, team_ids[i], team_ids[i+1])
                all_scores.append(pred['predicted_score'])
            except:
                pass
        
        unique_scores = set(all_scores)
        print(f"\n✅ Verschiedene Ergebnisse generiert: {len(unique_scores)} verschiedene von {len(all_scores)} Tests")
        print(f"   Beispiele: {list(unique_scores)[:5]}")
        
        if len(unique_scores) == 1 and '1:1' in unique_scores:
            print("❌ PROBLEM: Alle Vorhersagen zeigen 1:1!")
        else:
            print("✅ xG-Modell funktioniert - vielfältige Vorhersagen!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_xg_model())