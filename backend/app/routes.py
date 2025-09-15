from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.schemas import Match, Prediction, MatchResult, TableEntry, MatchdayInfo, PredictionQualityEntry, PredictionQualityStats
from app import data_service, prediction_service

router = APIRouter(tags=["Bundesliga"])

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
    Liefert eine Analyse der Vorhersagequalität durch Vergleich mit realen Ergebnissen
    """
    try:
        quality_data = await data_service.get_prediction_quality()
        return quality_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Vorhersagequalität: {str(e)}")
