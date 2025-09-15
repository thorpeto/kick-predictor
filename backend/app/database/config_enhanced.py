"""
Enhanced Database Configuration - Support for PostgreSQL (Supabase) and SQLite
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.models import Base
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class EnhancedDatabaseConfig:
    def __init__(self):
        # Verwende DATABASE_URL wenn gesetzt (für Render/Supabase), sonst umgebungsabhängige Pfade
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Parse URL to determine database type
            parsed = urlparse(database_url)
            if parsed.scheme in ['postgres', 'postgresql']:
                # PostgreSQL (Supabase)
                logger.info("Using PostgreSQL database (Supabase)")
                self.database_url = database_url
                self.db_type = 'postgresql'
                # PostgreSQL doesn't need local file paths
                self.db_path = None
            elif parsed.scheme == 'sqlite':
                # SQLite from URL
                logger.info("Using SQLite database from DATABASE_URL")
                self.database_url = database_url
                self.db_type = 'sqlite'
                # Extract path from sqlite URL
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
                # Unknown database type, assume generic
                self.database_url = database_url
                self.db_type = 'generic'
                self.db_path = None
        else:
            # Lokale Entwicklung - SQLite fallback
            logger.info("No DATABASE_URL found, using local SQLite")
            self.db_type = 'sqlite'
            if os.path.exists('/app'):
                # Docker-Umgebung
                self.db_path = '/app/data/kick_predictor.db'
            else:
                # Dev-Container oder lokale Entwicklung
                self.db_path = '/workspaces/kick-predictor/backend/kick_predictor.db'
            
            self.database_url = f"sqlite:///{self.db_path}"
        
        # Fallback-Mechanismus für SQLite wenn Primary Path nicht funktioniert
        if self.db_type == 'sqlite':
            self._setup_fallback_paths()
            self._ensure_directory_exists()
        
        # Engine Configuration based on database type
        self._create_engine()
        
        # Session Factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = False
    
    def _create_engine(self):
        """Create database engine based on database type"""
        if self.db_type == 'postgresql':
            # PostgreSQL configuration for Supabase
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set zu True für SQL-Logging
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Validate connections before use
                pool_recycle=300,    # Recycle connections every 5 minutes
                connect_args={
                    "sslmode": "require",  # Supabase requires SSL
                }
            )
        elif self.db_type == 'sqlite':
            # SQLite configuration
            self.engine = create_engine(
                self.database_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,  # Für SQLite Multi-Threading
                    "timeout": 30  # 30 Sekunden Timeout
                },
                echo=False  # Set zu True für SQL-Logging
            )
        else:
            # Generic fallback
            self.engine = create_engine(
                self.database_url,
                echo=False
            )
    
    def _setup_fallback_paths(self):
        """Setup fallback paths for SQLite in different environments"""
        self.fallback_paths = []
        
        if os.getenv('ENVIRONMENT') == 'production' or os.getenv('RENDER'):
            # Render.com Fallback-Pfade
            self.fallback_paths = [
                '/tmp/kick_predictor.db',  # Temporäres Verzeichnis (immer beschreibbar)
                '/app/kick_predictor.db',  # App-Root
                './kick_predictor.db'     # Current directory
            ]
    
    def _ensure_directory_exists(self):
        """Ensure SQLite database directory exists with fallback handling"""
        if not self.db_path:
            return
            
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
                        self._create_engine()  # Recreate engine with new path
                        break
                    except (PermissionError, OSError):
                        continue
                else:
                    logger.error("No writable SQLite database path found!")
    
    def test_database_connection(self):
        """Test if database can be opened"""
        try:
            with self.engine.connect() as conn:
                if self.db_type == 'postgresql':
                    conn.execute(text("SELECT version()"))
                else:
                    conn.execute(text("SELECT 1"))
            return True, "Database connection successful"
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False, f"Database connection failed: {str(e)}"
    
    def initialize_database(self):
        """Erstellt alle Tabellen falls sie nicht existieren"""
        if self._initialized:
            return
            
        # Test connection first and try fallbacks if needed (only for SQLite)
        connection_ok, connection_msg = self.test_database_connection()
        
        if not connection_ok and self.db_type == 'sqlite' and hasattr(self, 'fallback_paths'):
            logger.warning("Primary SQLite database path failed, trying fallbacks...")
            for fallback_path in self.fallback_paths:
                self.db_path = fallback_path
                self.database_url = f"sqlite:///{fallback_path}"
                self._create_engine()
                
                connection_ok, connection_msg = self.test_database_connection()
                if connection_ok:
                    logger.info(f"Successfully using fallback database: {fallback_path}")
                    break
            else:
                raise Exception("No working SQLite database path found")
        elif not connection_ok:
            raise Exception(f"Database connection failed: {connection_msg}")
        
        try:
            # Erstelle alle Tabellen
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized successfully ({self.db_type})")
            if self.db_path:
                logger.info(f"Database location: {self.db_path}")
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

# Global Enhanced Database Instance
enhanced_db_config = EnhancedDatabaseConfig()

def get_enhanced_database_session():
    """Dependency Injection für FastAPI mit Enhanced Config"""
    session = enhanced_db_config.get_session()
    try:
        yield session
    finally:
        enhanced_db_config.close_session(session)

def init_enhanced_database():
    """Initialisiert die Enhanced Datenbank (für Startup)"""
    enhanced_db_config.initialize_database()
    logger.info("Enhanced database initialization completed")