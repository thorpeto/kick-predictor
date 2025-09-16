from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import Match, Prediction, MatchResult, TableEntry, MatchdayInfo, PredictionQualityEntry, PredictionQualityStats
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

# ========== SYNC ENDPOINTS ==========

@router.post("/sync/full")
async def trigger_full_sync():
    """Trigger full data synchronization"""
    try:
        from app.services.sync_service import SyncService
        sync_service = SyncService()
        
        result = await sync_service.sync_all_data()
        return result
        
    except Exception as e:
        logger.error(f"Error in full sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/teams")
async def trigger_teams_sync():
    """Trigger teams synchronization"""
    try:
        from app.services.sync_service import SyncService
        sync_service = SyncService()
        
        result = await sync_service.sync_teams()
        return result
        
    except Exception as e:
        logger.error(f"Error in teams sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/matches")
async def trigger_matches_sync():
    """Trigger matches synchronization"""
    try:
        from app.services.sync_service import SyncService
        sync_service = SyncService()
        
        result = await sync_service.sync_matches()
        return result
        
    except Exception as e:
        logger.error(f"Error in matches sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/predictions")
async def trigger_predictions_sync():
    """Trigger predictions synchronization"""
    try:
        from app.services.sync_service import SyncService
        sync_service = SyncService()
        
        result = await sync_service.sync_current_predictions()
        return result
        
    except Exception as e:
        logger.error(f"Error in predictions sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/quality")
async def trigger_quality_sync():
    """Trigger prediction quality synchronization"""
    try:
        from app.services.sync_service import SyncService
        sync_service = SyncService()
        
        result = await sync_service.sync_prediction_quality()
        return result
        
    except Exception as e:
        logger.error(f"Error in quality sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def get_sync_status():
    """Get synchronization status and statistics"""
    try:
        from app.services.sync_service import SyncService
        from app.services.scheduler_service import scheduler_service
        
        sync_service = SyncService()
        sync_stats = await sync_service.get_sync_statistics()
        job_status = scheduler_service.get_job_status()
        
        return {
            "sync_statistics": sync_stats,
            "scheduler_status": job_status
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/scheduler/start")
async def start_scheduler():
    """Start the background scheduler"""
    try:
        from app.services.scheduler_service import scheduler_service
        
        await scheduler_service.start()
        return {"message": "Scheduler started successfully"}
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/scheduler/stop")
async def stop_scheduler():
    """Stop the background scheduler"""
    try:
        from app.services.scheduler_service import scheduler_service
        
        await scheduler_service.stop()
        return {"message": "Scheduler stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/immediate/{sync_type}")
async def trigger_immediate_sync(sync_type: str):
    """Trigger immediate synchronization of specific type"""
    try:
        from app.services.scheduler_service import scheduler_service
        
        valid_types = ["teams", "matches", "predictions", "quality", "full"]
        if sync_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sync type. Must be one of: {', '.join(valid_types)}"
            )
        
        result = await scheduler_service.trigger_immediate_sync(sync_type)
        return result
        
    except Exception as e:
        logger.error(f"Error in immediate sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== DATABASE ENDPOINTS ==========

@router.get("/db/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        with DatabaseService() as db:
            stats = db.get_database_stats()
            return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENHANCED DATA SERVICE ENDPOINTS ==========

@router.get("/prediction-quality")
async def get_prediction_quality():
    """
    Hole alle Vorhersage-Qualitäts-Analysen aus der Datenbank
    """
    try:
        from app.services.enhanced_data_service import EnhancedDataService
        data_service = EnhancedDataService()
        quality_data = await data_service.get_prediction_quality()
        return quality_data
    except Exception as e:
        logger.error(f"Error getting prediction quality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== PLACEHOLDER ENDPOINTS ==========

@router.get("/next-matchday")
async def get_next_matchday():
    """Placeholder - will be re-enabled after sync implementation"""
    return {"message": "Endpoint temporarily disabled during sync implementation"}

@router.get("/predictions/{matchday}")
async def get_predictions(matchday: int):
    """Placeholder - will be re-enabled after sync implementation"""
    return {"message": "Endpoint temporarily disabled during sync implementation"}

@router.get("/team/{team_id}/form")
async def get_team_form(team_id: int):
    """Placeholder - will be re-enabled after sync implementation"""
    return {"message": "Endpoint temporarily disabled during sync implementation"}

@router.get("/team/{team_id}/matches")
async def get_team_matches(team_id: int):
    """Placeholder - will be re-enabled after sync implementation"""
    return {"message": "Endpoint temporarily disabled during sync implementation"}

@router.get("/table")
async def get_table():
    """Placeholder - will be re-enabled after sync implementation"""
    return {"message": "Endpoint temporarily disabled during sync implementation"}

@router.get("/matchday-info")
async def get_matchday_info():
    """Placeholder - will be re-enabled after sync implementation"""
    return {"message": "Endpoint temporarily disabled during sync implementation"}