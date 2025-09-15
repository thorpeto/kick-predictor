"""
Database Configu            # Extrahiere Pfad aus sqlite:////app/data/kick_predictor.db Format
            if database_url.startswith('sqlite:////'):
                # Absoluter Pfad mit vier Slashes: sqlite:////app/data/file.db -> //app/data/file.db -> /app/data/file.db
                self.db_path = database_url[8:].lstrip('/')  # Entferne 'sqlite://' und führende Slashes
                if not self.db_path.startswith('/'):
                    self.db_path = '/' + self.db_pathon und Session Management
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
        # Verwende DATABASE_URL wenn gesetzt (für Render), sonst umgebungsabhängige Pfade
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Für Render oder andere Cloud-Deployments
            self.database_url = database_url
            # Extrahiere Pfad aus sqlite:////app/data/kick_predictor.db Format
            if database_url.startswith('sqlite:////'):
                # Absoluter Pfad mit vier Slashes: sqlite:////app/data/file.db -> /app/data/file.db
                path_part = database_url[8:].lstrip('/')  # Entferne 'sqlite://' und führende Slashes
                self.db_path = '/' + path_part if not path_part.startswith('/') else path_part
            elif database_url.startswith('sqlite:///'):
                # Relativer Pfad mit drei Slashes
                self.db_path = database_url[10:]  # Entferne 'sqlite:///'
            else:
                self.db_path = database_url
        else:
            # Lokale Entwicklung - umgebungsabhängige Pfade
            if os.path.exists('/app'):
                # Docker-Umgebung
                self.db_path = '/app/data/kick_predictor.db'
            else:
                # Dev-Container oder lokale Entwicklung
                self.db_path = '/workspaces/kick-predictor/backend/kick_predictor.db'
            
            self.database_url = f"sqlite:///{self.db_path}"
        
        # Stelle sicher, dass das Verzeichnis existiert (nur wenn beschreibbar)
        db_dir = os.path.dirname(self.db_path)
        try:
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
        except PermissionError:
            logger.warning(f"Cannot create database directory {db_dir}, assuming it exists or will be created by deployment")
        
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