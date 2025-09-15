"""
Database Configuration und Session Management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.models import Base
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        # SQLite Database Path - verwende app-Verzeichnis für Docker
        default_path = '/app/data/kick_predictor.db' if os.path.exists('/app') else '/workspaces/kick-predictor/backend/kick_predictor.db'
        self.db_path = os.getenv('DATABASE_PATH', default_path)
        
        # Stelle sicher, dass das Verzeichnis existiert
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
        
        # SQLite Connection String
        self.database_url = f"sqlite:///{self.db_path}"
        
        # Engine Configuration
        self.engine = create_engine(
            self.database_url,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,  # Für SQLite Multi-Threading
                "timeout": 30  # 30 Sekunden Timeout
            },
            echo=False  # Set zu True für SQL-Logging
        )
        
        # Session Factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = False
    
    def initialize_database(self):
        """Erstellt alle Tabellen falls sie nicht existieren"""
        if self._initialized:
            return
            
        try:
            # Erstelle alle Tabellen
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized at {self.db_path}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def get_session(self):
        """Erstellt eine neue Database Session"""
        if not self._initialized:
            self.initialize_database()
        return self.SessionLocal()
    
    def close_session(self, session):
        """Schließt eine Database Session"""
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {str(e)}")

# Global Database Instance
db_config = DatabaseConfig()

def get_database_session():
    """Dependency Injection für FastAPI"""
    session = db_config.get_session()
    try:
        yield session
    finally:
        db_config.close_session(session)

def init_database():
    """Initialisiert die Datenbank (für Startup)"""
    db_config.initialize_database()
    logger.info("Database initialization completed")