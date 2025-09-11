import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

# Konfiguriere Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Lade Umgebungsvariablen
load_dotenv()

app = FastAPI(
    title="Kick Predictor API",
    description="API für die Vorhersage von Bundesliga-Spielergebnissen",
    version="0.1.0",
)

# CORS-Einstellungen für Frontend-Verbindung
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Willkommen bei der Kick Predictor API!"}

@app.get("/health")
async def health_check():
    return {"status": "online"}

# Routen einbinden
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
