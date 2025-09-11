# Initialisierungsdatei für das Modul
from app.services.data_service import DataService
from app.services.prediction_service import PredictionService

# Services erstellen
data_service = DataService()
prediction_service = PredictionService(data_service)
