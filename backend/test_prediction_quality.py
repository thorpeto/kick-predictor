#!/usr/bin/env python3
"""
Test der Vorhersagequalität-API mit xG-Modell
"""
import requests
import json

def test_prediction_quality_api():
    print("🧪 Teste Vorhersagequalität-API mit xG-Modell...")
    
    try:
        response = requests.get("http://localhost:8080/api/prediction-quality", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API funktioniert - {len(data['entries'])} Einträge")
            print(f"📊 Statistiken:")
            print(f"   Tendenz korrekt: {data['summary']['tendency_accuracy']:.1%}")
            print(f"   Exakte Treffer: {data['summary']['exact_score_accuracy']:.1%}")
            
            print(f"\n🎯 Erste 3 Vorhersagen:")
            for i, entry in enumerate(data['entries'][:3]):
                match = entry['match']
                home = match['home_team']['name']
                away = match['away_team']['name']
                predicted = entry['predicted_score']
                actual = entry['actual_score']
                hit_type = entry['hit_type']
                
                print(f"   {i+1}. {home} vs {away}")
                print(f"      Vorhersage: {predicted} | Ergebnis: {actual} | {hit_type}")
                
            # Prüfe auf 1:1-Problem
            all_predictions = [entry['predicted_score'] for entry in data['entries']]
            unique_predictions = set(all_predictions)
            
            print(f"\n📈 Vorhersage-Vielfalt:")
            print(f"   {len(unique_predictions)} verschiedene von {len(all_predictions)} Vorhersagen")
            print(f"   Beispiele: {list(unique_predictions)[:10]}")
            
            if len(unique_predictions) == 1 and '1:1' in unique_predictions:
                print("❌ PROBLEM: Alle Vorhersagen sind 1:1!")
            else:
                print("✅ Vielfältige Vorhersagen - xG-Modell funktioniert!")
                
        else:
            print(f"❌ API-Fehler: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_prediction_quality_api()