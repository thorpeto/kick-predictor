import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lade Umgebungsvariablen
load_dotenv()

# Initialisiere Datenbank früh im Startup-Prozess
try:
    from app.database.config import init_database
    init_database()
    logger.info("Database initialization successful")
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    # In Produktion nicht abbrechen - manchmal wird die DB später gemountet
    if os.getenv("ENVIRONMENT") != "production":
        raise

app = FastAPI(
    title="Kick Predictor API",
    description="API für die Vorhersage von Bundesliga-Spielergebnissen",
    version="0.1.0",
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
        "https://*.onrender.com",  # Alle Render.com Subdomains
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
