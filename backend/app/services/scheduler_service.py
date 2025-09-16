"""
Background scheduler for automatic data synchronization
Uses APScheduler to run periodic sync tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

class SchedulerService:
    """Background scheduler for data synchronization"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.sync_service = SyncService()
        self.is_running = False
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            logger.info("Starting background scheduler...")
            
            # Add scheduled jobs
            await self._add_scheduled_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Background scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        try:
            logger.info("Stopping background scheduler...")
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _add_scheduled_jobs(self):
        """Add all scheduled jobs"""
        
        # 1. Team synchronization - once per day at 2 AM
        self.scheduler.add_job(
            func=self._sync_teams_job,
            trigger=CronTrigger(hour=2, minute=0),
            id="sync_teams",
            name="Sync Teams",
            replace_existing=True,
            max_instances=1
        )
        
        # 2. Match synchronization - every 4 hours
        self.scheduler.add_job(
            func=self._sync_matches_job,
            trigger=IntervalTrigger(hours=4),
            id="sync_matches",
            name="Sync Matches",
            replace_existing=True,
            max_instances=1
        )
        
        # 3. Prediction synchronization - every 2 hours during active periods
        # More frequent during weekends (Friday-Monday)
        self.scheduler.add_job(
            func=self._sync_predictions_job,
            trigger=IntervalTrigger(hours=2),
            id="sync_predictions",
            name="Sync Predictions",
            replace_existing=True,
            max_instances=1
        )
        
        # 4. Prediction quality synchronization - every 6 hours
        self.scheduler.add_job(
            func=self._sync_quality_job,
            trigger=IntervalTrigger(hours=6),
            id="sync_quality",
            name="Sync Prediction Quality",
            replace_existing=True,
            max_instances=1
        )
        
        # 5. Full synchronization - once per week on Monday at 1 AM
        self.scheduler.add_job(
            func=self._full_sync_job,
            trigger=CronTrigger(day_of_week=0, hour=1, minute=0),  # Monday
            id="full_sync",
            name="Full Data Sync",
            replace_existing=True,
            max_instances=1
        )
        
        # 6. Cleanup old sync logs - daily at 3 AM
        self.scheduler.add_job(
            func=self._cleanup_job,
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup_sync_logs",
            name="Cleanup Sync Logs",
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("All scheduled jobs added successfully")
    
    async def _sync_teams_job(self):
        """Scheduled job for team synchronization"""
        logger.info("Starting scheduled team sync...")
        try:
            result = await self.sync_service.sync_teams()
            logger.info(f"Scheduled team sync completed: {result['count']} teams synced")
        except Exception as e:
            logger.error(f"Scheduled team sync failed: {e}")
    
    async def _sync_matches_job(self):
        """Scheduled job for match synchronization"""
        logger.info("Starting scheduled match sync...")
        try:
            result = await self.sync_service.sync_matches()
            logger.info(f"Scheduled match sync completed: {result['count']} matches synced")
        except Exception as e:
            logger.error(f"Scheduled match sync failed: {e}")
    
    async def _sync_predictions_job(self):
        """Scheduled job for prediction synchronization"""
        logger.info("Starting scheduled prediction sync...")
        try:
            result = await self.sync_service.sync_current_predictions()
            logger.info(f"Scheduled prediction sync completed: {result['count']} predictions synced")
        except Exception as e:
            logger.error(f"Scheduled prediction sync failed: {e}")
    
    async def _sync_quality_job(self):
        """Scheduled job for prediction quality synchronization"""
        logger.info("Starting scheduled quality sync...")
        try:
            result = await self.sync_service.sync_prediction_quality()
            logger.info(f"Scheduled quality sync completed: {result['count']} quality entries synced")
        except Exception as e:
            logger.error(f"Scheduled quality sync failed: {e}")
    
    async def _full_sync_job(self):
        """Scheduled job for full synchronization"""
        logger.info("Starting scheduled full sync...")
        try:
            result = await self.sync_service.sync_all_data()
            logger.info(f"Scheduled full sync completed: {result}")
        except Exception as e:
            logger.error(f"Scheduled full sync failed: {e}")
    
    async def _cleanup_job(self):
        """Scheduled job for cleanup operations"""
        logger.info("Starting scheduled cleanup...")
        try:
            from app.database.config_enhanced import DatabaseService
            from app.database.models import SyncStatus
            
            # Delete sync logs older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            
            with DatabaseService() as db:
                deleted_count = db.session.query(SyncStatus).filter(
                    SyncStatus.created_at < cutoff_date
                ).delete()
                db.session.commit()
                
            logger.info(f"Cleanup completed: {deleted_count} old sync logs deleted")
            
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {e}")
    
    def _job_executed_listener(self, event):
        """Listener for successful job executions"""
        logger.info(f"Job '{event.job_id}' executed successfully")
    
    def _job_error_listener(self, event):
        """Listener for job execution errors"""
        logger.error(f"Job '{event.job_id}' failed: {event.exception}")
    
    async def trigger_immediate_sync(self, sync_type: str = "full") -> Dict[str, Any]:
        """Trigger immediate synchronization"""
        logger.info(f"Triggering immediate {sync_type} sync...")
        
        try:
            if sync_type == "teams":
                result = await self.sync_service.sync_teams()
            elif sync_type == "matches":
                result = await self.sync_service.sync_matches()
            elif sync_type == "predictions":
                result = await self.sync_service.sync_current_predictions()
            elif sync_type == "quality":
                result = await self.sync_service.sync_prediction_quality()
            elif sync_type == "full":
                result = await self.sync_service.sync_all_data()
            else:
                raise ValueError(f"Unknown sync type: {sync_type}")
            
            logger.info(f"Immediate {sync_type} sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Immediate {sync_type} sync failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "max_instances": job.max_instances
            })
        
        return {
            "scheduler_running": self.is_running,
            "jobs": jobs_info,
            "total_jobs": len(jobs_info)
        }

# Global scheduler instance
scheduler_service = SchedulerService()

@asynccontextmanager
async def lifespan_scheduler(app):
    """Lifespan context manager for FastAPI app with scheduler"""
    # Startup
    await scheduler_service.start()
    try:
        yield
    finally:
        # Shutdown
        await scheduler_service.stop()