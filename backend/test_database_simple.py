"""
Einfacher Database Test
"""
import asyncio
import logging
from app.database.config import init_database
from app.database.database_service import DatabaseService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_basic():
    """Basic Database Test"""
    
    logger.info("=== Basic Database Test ===")
    
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
            
            # Test team creation
            test_team = {
                'id': 1,
                'name': 'Test Team',
                'short_name': 'TT',
                'logo_url': 'https://example.com/logo.png'
            }
            
            team = db.get_or_create_team(test_team)
            logger.info(f"Created/Updated team: {team}")
            
        logger.info("✅ DatabaseService working")
        
        # 3. Check final stats
        with DatabaseService() as db:
            final_stats = db.get_database_stats()
            logger.info(f"Final database stats: {final_stats}")
        
        logger.info("✅ All basic tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_basic()