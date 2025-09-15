from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import Match, Prediction, MatchResult, TableEntry, MatchdayInfo, PredictionQualityEntry, PredictionQualityStats
from app import data_service, prediction_service
from app.database.database_service import DatabaseService
import logging

router = APIRouter(tags=["Bundesliga"])
logger = logging.getLogger(__name__)

@router.get("/test")
async def test_connection():
    """
    Test-Endpoint um die API-Verbindung zu überprüfen
    """
    return {
        "status": "success",
        "message": "API-Verbindung funktioniert!",
        "service": "Kick Predictor Backend"
    }

@router.get("/next-matchday", response_model=List[Match])
async def get_next_matchday():
    """
    Liefert die Spiele des nächsten Spieltags
    """
    try:
        matches = await data_service.get_next_matchday()
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Daten: {str(e)}")

@router.get("/predictions/{matchday}", response_model=List[Prediction])
async def get_predictions(matchday: int):
    """
    Berechnet Vorhersagen für einen bestimmten Spieltag
    """
    if matchday < 1 or matchday > 34:
        raise HTTPException(status_code=400, detail="Spieltag muss zwischen 1 und 34 liegen")
    
    try:
        predictions = await prediction_service.predict_matchday(matchday)
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Berechnung der Vorhersagen: {str(e)}")

@router.get("/team/{team_id}/form")
async def get_team_form(team_id: int):
    """
    Berechnet die aktuelle Form eines Teams
    """
    try:
        form = await data_service.get_team_form(team_id)
        return {"team_id": team_id, "form": round(form, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Berechnung der Form: {str(e)}")

@router.get("/team/{team_id}/matches", response_model=List[MatchResult])
async def get_team_matches(team_id: int):
    """
    Liefert die letzten Spiele eines Teams (bis zu 14 Spiele, einschließlich der letzten Saison)
    """
    try:
        matches = await data_service.get_last_n_matches(team_id, 14)
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Spiele: {str(e)}")

@router.get("/table", response_model=List[TableEntry])
async def get_current_table():
    """
    Liefert die aktuelle Bundesliga-Tabelle
    """
    try:
        table = await data_service.get_current_table()
        return table
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Tabelle: {str(e)}")

@router.get("/matchday-info", response_model=MatchdayInfo)
async def get_matchday_info():
    """
    Liefert Informationen über den aktuellen Spieltag und Vorhersagen-Verfügbarkeit
    """
    try:
        info = await data_service.get_current_matchday_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Spieltag-Informationen: {str(e)}")

@router.delete("/predictions/cache")
async def clear_predictions_cache(matchday: Optional[int] = Query(None, description="Spieltag für spezifische Cache-Löschung")):
    """
    Löscht den Vorhersagen-Cache (optional für einen bestimmten Spieltag)
    """
    try:
        data_service.clear_predictions_cache(matchday)
        if matchday:
            return {"status": "success", "message": f"Cache für Spieltag {matchday} gelöscht"}
        else:
            return {"status": "success", "message": "Gesamter Vorhersagen-Cache gelöscht"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Löschen des Caches: {str(e)}")

@router.get("/prediction-quality")
async def get_prediction_quality():
    """
    Hole alle Vorhersage-Qualitäts-Analysen
    """
    quality_data = await data_service.get_prediction_quality()
    return quality_data

# ========== NEW DATABASE ENDPOINTS ==========

@router.get("/db/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        with DatabaseService() as db:
            stats = db.get_database_stats()
            sync_status = db.get_sync_status()
            
            return {
                "database_stats": stats,
                "sync_status": [
                    {
                        "entity_type": status.entity_type,
                        "last_sync": status.last_sync.isoformat() if status.last_sync else None,
                        "last_sync_success": status.last_sync_success,
                        "records_synced": status.records_synced,
                        "sync_message": status.sync_message
                    }
                    for status in sync_status
                ]
            }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/db/sync-teams")
async def sync_teams_only():
    """Sync only teams from API to database"""
    try:
        # Vereinfachtes Team-Sync mit verfügbaren Methoden
        from app.services.openliga_client import OpenLigaDBClient
        
        async with OpenLigaDBClient() as client:
            # Hole Teams aus Matches
            try:
                matches_data = await client.get_matches_by_league_season("bl1", "2025")
                
                # Extrahiere Teams aus Matches
                teams_set = set()
                for match in matches_data:
                    if 'team1' in match and match['team1']:
                        team1 = match['team1']
                        teams_set.add((
                            team1.get('teamId'),
                            team1.get('teamName', ''),
                            team1.get('shortName', ''),
                            team1.get('teamIconUrl', '')
                        ))
                    if 'team2' in match and match['team2']:
                        team2 = match['team2']
                        teams_set.add((
                            team2.get('teamId'),
                            team2.get('teamName', ''),
                            team2.get('shortName', ''),
                            team2.get('teamIconUrl', '')
                        ))
                
                synced_count = 0
                with DatabaseService() as db:
                    for team_id, name, short_name, logo_url in teams_set:
                        if team_id and name:
                            team_dict = {
                                'id': team_id,
                                'name': name,
                                'short_name': short_name or name[:3].upper(),
                                'logo_url': logo_url
                            }
                            
                            db.get_or_create_team(team_dict)
                            synced_count += 1
                    
                    db.update_sync_status("teams", True, f"Synced {synced_count} teams", synced_count)
                
                return {"message": f"Successfully synced {synced_count} teams", "synced_count": synced_count}
                
            except Exception as api_error:
                logger.error(f"API error during team sync: {str(api_error)}")
                raise HTTPException(status_code=500, detail=f"API error: {str(api_error)}")
                
    except Exception as e:
        logger.error(f"Error syncing teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db/teams")
async def get_teams_from_database():
    """Get all teams from database"""
    try:
        with DatabaseService() as db:
            teams = db.get_all_teams()
            return [
                {
                    "id": team.id,
                    "name": team.name,
                    "short_name": team.short_name,
                    "logo_url": team.logo_url,
                    "created_at": team.created_at.isoformat() if team.created_at else None,
                    "updated_at": team.updated_at.isoformat() if team.updated_at else None
                }
                for team in teams
            ]
    except Exception as e:
        logger.error(f"Error getting teams from database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/db/sync-matches")
async def sync_matches():
    """Sync matches from API to database"""
    try:
        from app.services.openliga_client import OpenLigaDBClient
        
        async with OpenLigaDBClient() as client:
            # Hole alle Matches der Saison
            matches_data = await client.get_matches_by_league_season("bl1", "2025")
            
            synced_count = 0
            with DatabaseService() as db:
                for match_data in matches_data:
                    try:
                        # Prüfe, ob Teams existieren
                        home_team_id = match_data.get('team1', {}).get('teamId')
                        away_team_id = match_data.get('team2', {}).get('teamId')
                        
                        if not home_team_id or not away_team_id:
                            continue
                        
                        # Erstelle Team-Dicts für get_or_create_match
                        home_team_dict = {
                            'id': home_team_id,
                            'name': match_data.get('team1', {}).get('teamName', ''),
                            'short_name': match_data.get('team1', {}).get('shortName', ''),
                            'logo_url': match_data.get('team1', {}).get('teamIconUrl', '')
                        }
                        
                        away_team_dict = {
                            'id': away_team_id,
                            'name': match_data.get('team2', {}).get('teamName', ''),
                            'short_name': match_data.get('team2', {}).get('shortName', ''),
                            'logo_url': match_data.get('team2', {}).get('teamIconUrl', '')
                        }
                        
                        # Extrahiere Match-Informationen
                        match_dict = {
                            'id': match_data.get('matchID'),
                            'home_team': home_team_dict,
                            'away_team': away_team_dict,
                            'date': match_data.get('matchDateTime'),
                            'matchday': match_data.get('group', {}).get('groupOrderID', 0),
                            'season': '2025',
                            'is_finished': match_data.get('matchIsFinished', False)
                        }
                        
                        # Füge Ergebnisse hinzu falls Match fertig ist
                        if match_data.get('matchIsFinished', False):
                            results = match_data.get('matchResults', [])
                            if results:
                                final_result = results[-1]  # Letztes Ergebnis ist meist das finale
                                match_dict['home_goals'] = final_result.get('pointsTeam1', 0)
                                match_dict['away_goals'] = final_result.get('pointsTeam2', 0)
                        
                        if match_dict['id']:
                            db.get_or_create_match(match_dict)
                            synced_count += 1
                            
                    except Exception as match_error:
                        logger.warning(f"Error syncing match {match_data.get('matchID', 'unknown')}: {str(match_error)}")
                        continue
                
                db.update_sync_status("matches", True, f"Synced {synced_count} matches", synced_count)
            
            return {"message": f"Successfully synced {synced_count} matches", "synced_count": synced_count}
            
    except Exception as e:
        logger.error(f"Error syncing matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/db/sync-predictions")
async def sync_predictions():
    """Sync predictions and prediction quality from API to database"""
    try:
        from app.services.data_service import DataService as OriginalDataService
        
        # Verwende den Original-DataService um aktuelle Prediction Quality zu holen
        original_service = OriginalDataService()
        quality_data = await original_service.get_prediction_quality()
        
        synced_count = 0
        quality_count = 0
        
        with DatabaseService() as db:
            # Sync predictions and quality data
            for entry in quality_data.get('entries', []):
                match_id = None  # Initialize match_id
                try:
                    # entry ist ein PredictionQualityEntry-Pydantic-Modell
                    match_info = entry.match
                    match_id = match_info.id
                    
                    if not match_id:
                        continue
                    
                    # Erstelle Prediction
                    predicted_score_parts = entry.predicted_score.split(':')
                    prediction_dict = {
                        'match_id': match_id,
                        'predicted_home_goals': int(predicted_score_parts[0]),
                        'predicted_away_goals': int(predicted_score_parts[1]),
                        'predicted_score': entry.predicted_score,
                        'home_win_prob': entry.predicted_home_win_prob,
                        'draw_prob': entry.predicted_draw_prob,
                        'away_win_prob': entry.predicted_away_win_prob,
                        'calculated_at': datetime.now()
                    }
                    
                    prediction = db.get_or_create_prediction(prediction_dict)
                    synced_count += 1
                    
                    # Erstelle PredictionQuality falls Match fertig ist und actual_score vorhanden
                    if entry.actual_score and entry.hit_type:
                        quality_dict = {
                            'match_id': match_id,
                            'predicted_score': entry.predicted_score,
                            'actual_score': entry.actual_score,
                            'predicted_home_win_prob': entry.predicted_home_win_prob,
                            'predicted_draw_prob': entry.predicted_draw_prob,
                            'predicted_away_win_prob': entry.predicted_away_win_prob,
                            'hit_type': entry.hit_type,
                            'tendency_correct': entry.tendency_correct,
                            'exact_score_correct': entry.exact_score_correct,
                            'quality_score': 1.0 if entry.exact_score_correct else (0.5 if entry.tendency_correct else 0.0)
                        }
                        
                        db.get_or_create_prediction_quality(quality_dict)
                        quality_count += 1
                        
                except Exception as entry_error:
                    logger.warning(f"Error syncing prediction for match {match_id}: {str(entry_error)}")
                    continue
            
            db.update_sync_status("predictions", True, f"Synced {synced_count} predictions, {quality_count} quality entries", synced_count)
        
        return {
            "message": f"Successfully synced {synced_count} predictions and {quality_count} quality entries",
            "predictions_synced": synced_count,
            "quality_synced": quality_count
        }
        
    except Exception as e:
        logger.error(f"Error syncing predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/db/full-sync")
async def full_sync():
    """Sync all data: teams, matches, and predictions"""
    try:
        results = {}
        
        # 1. Sync Teams
        try:
            team_result = await sync_teams_only()
            results["teams"] = team_result
        except Exception as e:
            results["teams"] = {"error": str(e)}
        
        # 2. Sync Matches
        try:
            match_result = await sync_matches()
            results["matches"] = match_result
        except Exception as e:
            results["matches"] = {"error": str(e)}
        
        # 3. Sync Predictions
        try:
            prediction_result = await sync_predictions()
            results["predictions"] = prediction_result
        except Exception as e:
            results["predictions"] = {"error": str(e)}
        
        return {
            "message": "Full sync completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in full sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
