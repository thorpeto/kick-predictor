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
        
        # Fallback-Mechanismus für Render wenn Primary Path nicht funktioniert
        self._setup_fallback_paths()
        
        # Stelle sicher, dass das Verzeichnis existiert (nur wenn beschreibbar)
        self._ensure_directory_exists()
        
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
    
    def _setup_fallback_paths(self):
        """Setup fallback paths for different environments"""
        self.fallback_paths = []
        
        if os.getenv('ENVIRONMENT') == 'production':
            # Render.com Fallback-Pfade
            self.fallback_paths = [
                '/tmp/kick_predictor.db',  # Temporäres Verzeichnis (immer beschreibbar)
                '/app/kick_predictor.db',  # App-Root
                './kick_predictor.db'     # Current directory
            ]
    
    def _ensure_directory_exists(self):
        """Ensure database directory exists with fallback handling"""
        db_dir = os.path.dirname(self.db_path)
        
        try:
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot create database directory {db_dir}: {e}")
            
            # Try fallback paths in production
            if hasattr(self, 'fallback_paths') and self.fallback_paths:
                for fallback_path in self.fallback_paths:
                    try:
                        # Test if we can write to this location
                        test_file = fallback_path + '.test'
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        
                        # If successful, use this path
                        logger.info(f"Using fallback database path: {fallback_path}")
                        self.db_path = fallback_path
                        self.database_url = f"sqlite:///{fallback_path}"
                        break
                    except (PermissionError, OSError):
                        continue
                else:
                    logger.error("No writable database path found!")
    
    def test_database_connection(self):
        """Test if database can be opened"""
        from sqlalchemy import text
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def initialize_database(self):
        """Erstellt alle Tabellen falls sie nicht existieren"""
        if self._initialized:
            return
            
        # Test connection first and try fallbacks if needed
        if not self.test_database_connection() and hasattr(self, 'fallback_paths'):
            logger.warning("Primary database path failed, trying fallbacks...")
            for fallback_path in self.fallback_paths:
                self.db_path = fallback_path
                self.database_url = f"sqlite:///{fallback_path}"
                
                # Recreate engine with new path
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    },
                    echo=False
                )
                
                if self.test_database_connection():
                    logger.info(f"Successfully using fallback database: {fallback_path}")
                    break
            else:
                raise Exception("No working database path found")
        
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