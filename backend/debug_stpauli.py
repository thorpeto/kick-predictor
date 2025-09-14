#!/usr/bin/env python3
"""
Debug-Tool für St. Pauli Team-Daten
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.openliga_client import OpenLigaDBClient
from app.services.data_converter import DataConverter
from app.services.data_service import DataService
import json
from datetime import datetime

async def debug_stpauli():
    """Debug St. Pauli Team-Daten"""
    
    STPAULI_ID = 98
    
    print(f"🔍 Debugging St. Pauli (Team-ID: {STPAULI_ID})")
    print("=" * 60)
    
    try:
        # 1. Test OpenLigaDB direkt
        print("\n1️⃣ Direkte OpenLigaDB API-Abfrage:")
        async with OpenLigaDBClient() as client:
            # Hole aktuelle Saison Spiele
            current_matches = await client.get_team_matches(STPAULI_ID, "bl1", "2025")
            print(f"   Spiele in Saison 2025: {len(current_matches)}")
            
            # Hole vorherige Saison Spiele
            previous_matches = await client.get_team_matches(STPAULI_ID, "bl1", "2024")
            print(f"   Spiele in Saison 2024: {len(previous_matches)}")
            
            # Letzte n Spiele
            last_matches = await client.get_matches_across_seasons(STPAULI_ID, 14, "bl1", "2025", "2024")
            print(f"   Letzte 14 Spiele (beide Saisons): {len(last_matches)}")
            
            # Zeige Details der letzten Spiele
            print(f"\n📋 Details der letzten {min(10, len(last_matches))} Spiele:")
            for i, match in enumerate(last_matches[:10]):
                if not match.get('matchIsFinished', False):
                    continue
                    
                home_team = match.get('team1', {})
                away_team = match.get('team2', {})
                match_date = match.get('matchDateTime', '')
                results = match.get('matchResults', [])
                final_result = next((r for r in results if r.get('resultTypeID') == 2), None)
                
                if final_result:
                    home_goals = final_result.get('pointsTeam1', 0)
                    away_goals = final_result.get('pointsTeam2', 0)
                    
                    # Bestimme ob St. Pauli Heim oder Auswärts war
                    is_home = home_team.get('teamId') == STPAULI_ID
                    opponent = away_team.get('teamName') if is_home else home_team.get('teamName')
                    stpauli_goals = home_goals if is_home else away_goals
                    opponent_goals = away_goals if is_home else home_goals
                    
                    # Bestimme Ergebnis
                    if stpauli_goals > opponent_goals:
                        result = "SIEG"
                    elif stpauli_goals < opponent_goals:
                        result = "NIEDERLAGE"
                    else:
                        result = "UNENTSCHIEDEN"
                    
                    venue = "Heim" if is_home else "Auswärts"
                    date_str = datetime.fromisoformat(match_date.replace('Z', '+00:00')).strftime('%d.%m.%Y')
                    
                    print(f"   {i+1:2d}. {date_str} - {venue:9s} vs {opponent:25s} {stpauli_goals}:{opponent_goals} ({result})")

        # 2. Test DataService
        print(f"\n2️⃣ DataService Test:")
        data_service = DataService()
        
        # Form berechnen
        form = await data_service.get_team_form(STPAULI_ID)
        print(f"   Berechnete Form: {form:.3f} ({form*100:.1f}%)")
        
        # Letzte Spiele über DataService
        last_matches_service = await data_service.get_last_n_matches(STPAULI_ID, 14)
        print(f"   Spiele über DataService: {len(last_matches_service)}")
        
        # Formberechnung im Detail
        print(f"\n📊 Detaillierte Formberechnung:")
        total_points = 0
        for i, match_result in enumerate(last_matches_service):
            match = match_result.match
            is_home = match.home_team.id == STPAULI_ID
            
            stpauli_goals = match_result.home_goals if is_home else match_result.away_goals
            opponent_goals = match_result.away_goals if is_home else match_result.home_goals
            
            if stpauli_goals > opponent_goals:
                points = 3
                result = "SIEG"
            elif stpauli_goals == opponent_goals:
                points = 1
                result = "UNENTSCHIEDEN"
            else:
                points = 0
                result = "NIEDERLAGE"
            
            total_points += points
            opponent = match.away_team.name if is_home else match.home_team.name
            venue = "Heim" if is_home else "Auswärts"
            date_str = match.date.strftime('%d.%m.%Y')
            
            print(f"   {i+1:2d}. {date_str} - {venue:9s} vs {opponent:25s} {stpauli_goals}:{opponent_goals} ({result}) -> {points} Punkte")
        
        max_points = len(last_matches_service) * 3
        calculated_form = total_points / max_points if max_points > 0 else 0.5
        
        print(f"\n   Gesamt: {total_points}/{max_points} Punkte = {calculated_form:.3f} ({calculated_form*100:.1f}%)")
        
        # Vergleiche mit API-Ergebnis
        if abs(form - calculated_form) < 0.001:
            print("   ✅ Form-Berechnung stimmt überein!")
        else:
            print(f"   ❌ Form-Berechnung weicht ab! API: {form:.3f}, Berechnet: {calculated_form:.3f}")
            
    except Exception as e:
        print(f"❌ Fehler beim Debugging: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_stpauli())