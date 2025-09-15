"""
Database Initialization und Test Script
"""
import asyncio
import logging
from app.database.config import init_database, db_config
from app.database.database_service import DatabaseService
from app.database.sync_service import SyncService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_setup():
    """Test Database Setup und Basic Operations"""
    
    logger.info("=== Database Initialization Test ===")
    
    try:
        # 1. Initialize Database
        logger.info("Initializing database...")
        init_database()
        logger.info("✅ Database initialized successfully")
        
        # 2. Test Database Service
        logger.info("Testing DatabaseService...")
        with DatabaseService() as db:
            stats = db.get_database_stats()
            logger.info(f"Database stats: {stats}")
        logger.info("✅ DatabaseService working")
        
        # 3. Test Sync Service
        logger.info("Testing SyncService...")
        sync_service = SyncService()
        
        # Test Teams Sync
        logger.info("Syncing teams...")
        teams_result = await sync_service.sync_teams()
        logger.info(f"Teams sync result: {teams_result}")
        
        # Test Matches Sync
        logger.info("Syncing matches...")
        matches_result = await sync_service.sync_matches(force_full_sync=True)
        logger.info(f"Matches sync result: {matches_result}")
        
        # 4. Check final stats
        with DatabaseService() as db:
            final_stats = db.get_database_stats()
            logger.info(f"Final database stats: {final_stats}")
        
        logger.info("✅ All tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_database_setup())