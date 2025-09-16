import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lade Umgebungsvariablen
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting application...")
    
    # Initialisiere Enhanced Database früh im Startup-Prozess
    try:
        from app.database.config_enhanced import init_enhanced_database
        init_enhanced_database()
        logger.info("Enhanced database initialization successful")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        # In Produktion versuche es nochmal nach kurzer Wartezeit
        if os.getenv("ENVIRONMENT") == "production":
            import time
            logger.info("Retrying database initialization in 5 seconds...")
            time.sleep(5)
            try:
                from app.database.config_enhanced import init_enhanced_database as retry_init
                retry_init()
                logger.info("Database initialization successful on retry")
            except Exception as retry_error:
                logger.error(f"Database initialization failed on retry: {str(retry_error)}")
    
    # Starte Scheduler
    try:
        from app.services.scheduler_service import scheduler_service
        await scheduler_service.start()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    # Auto-Sync beim Start wenn aktiviert
    if os.getenv("AUTO_SYNC_ON_START") == "true":
        logger.info("Auto-sync on start enabled, triggering initial sync...")
        try:
            from app.services.sync_service import SyncService
            sync_service = SyncService()
            
            # Führe initiale Synchronisation durch
            result = await sync_service.sync_all_data()
            logger.info(f"Initial sync completed: {result}")
            
        except Exception as e:
            logger.error(f"Auto-sync failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        from app.services.scheduler_service import scheduler_service
        await scheduler_service.stop()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")

app = FastAPI(
    title="Kick Predictor API",
    description="API für die Vorhersage von Bundesliga-Spielergebnissen",
    version="0.1.0",
    lifespan=lifespan
)

# CORS-Einstellungen für Frontend-Verbindung
# Definiere erlaubte Ursprünge basierend auf der Umgebungsvariable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = allowed_origins_str.split(",") if allowed_origins_str else []

if not allowed_origins or allowed_origins[0] == "":
    # Standard-Ursprünge für Entwicklung oder wenn keine definiert sind
    allowed_origins = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "https://kick-predictor-frontend.onrender.com",  # Render.com Frontend URL
        "https://kick-predictor-frontend-*.onrender.com",  # Render Preview Deployments
    ]

# Für Debugging in der Produktionsumgebung
print(f"CORS allowed origins: {allowed_origins}")
print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # OPTIONS für Preflight-Requests hinzufügen
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Willkommen bei der Kick Predictor API!"}

@app.get("/health")
async def health_check():
    return {"status": "online"}

# Routen einbinden
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Render verwendet PORT als Umgebungsvariable
    port = int(os.getenv("PORT", "8000"))  # Fallback auf 8000 für lokale Entwicklung
    host = "0.0.0.0"
    
    # Für Produktionsumgebung optimierte Einstellungen
    if os.getenv("ENVIRONMENT") == "production":
        uvicorn.run("main:app", host=host, port=port, reload=False)
    else:
        uvicorn.run("main:app", host=host, port=port, reload=True)
