import React, { useState, useEffect } from 'react';
import axios from 'axios';

const getApiBaseUrl = () => {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  if (window.location.hostname.includes('onrender.com')) {
    return 'https://kick-predictor-backend.onrender.com';
  }
  return window.location.origin;
};

interface UpdateStatus {
  is_running: boolean;
  is_gameday_time: boolean;
  last_update: string | null;
  update_count: number;
  current_time: string;
  next_scheduled_updates: Array<{
    date: string;
    day: string;
    times: string;
  }>;
}

interface MatchdayInfo {
  current_season: number;
  last_completed_matchday: number;
  upcoming_matchdays: Array<{
    matchday: number;
    matches_count: number;
    next_match_date: string;
  }>;
  weekend_matches: number;
  is_game_weekend: boolean;
  weekend_period: {
    start: string;
    end: string;
  };
  auto_updater: UpdateStatus;
}

const UpdatePage: React.FC = () => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState('');
  const [matchdayInfo, setMatchdayInfo] = useState<MatchdayInfo | null>(null);
  const [autoUpdaterStatus, setAutoUpdaterStatus] = useState<UpdateStatus | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchMatchdayInfo = async () => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.get(`${apiBaseUrl}/api/next-matchday-info`);
      const data: MatchdayInfo = response.data;
      setMatchdayInfo(data);
      setAutoUpdaterStatus(data.auto_updater);
      setUpdateMessage('');
    } catch (error: any) {
      console.error('Fetch error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unbekannter Fehler';
      setUpdateMessage(`Fehler beim Laden der Spieltag-Informationen: ${errorMsg}`);
    }
  };

  const fetchAutoUpdaterStatus = async () => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.get(`${apiBaseUrl}/api/auto-updater/status`);
      const data: UpdateStatus = response.data;
      setAutoUpdaterStatus(data);
    } catch (error: any) {
      console.error('Fehler beim Laden des Auto-Updater Status:', error);
    }
  };

  const performManualUpdate = async () => {
    setIsUpdating(true);
    setUpdateMessage('Update wird durchgeführt...');
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.post(`${apiBaseUrl}/api/update-data`);
      const result = response.data;
      
      setUpdateMessage(`✅ ${result.message}`);
      if (result.stats) {
        setUpdateMessage(prev => 
          `${prev}

📊 Statistiken:
• Abgeschlossene Spiele: ${result.stats.finished_matches}
• Letzter kompletter Spieltag: ${result.stats.last_completed_matchday}
• Aktualisierte Spiele: ${result.stats.total_matches_updated}`
        );
      }
      setTimeout(() => {
        fetchMatchdayInfo();
        fetchAutoUpdaterStatus();
      }, 1000);
    } catch (error: any) {
      console.error('Update-Fehler:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unbekannter Fehler';
      setUpdateMessage(`❌ Fehler beim Update: ${errorMsg}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const toggleAutoUpdater = async (action: 'start' | 'stop') => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.post(`${apiBaseUrl}/api/auto-updater/${action}`);
      const result = response.data;
      
      setUpdateMessage(`✅ ${result.message}`);
      setTimeout(() => {
        fetchAutoUpdaterStatus();
      }, 1000);
    } catch (error: any) {
      console.error('Auto-Updater Fehler:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unbekannter Fehler';
      setUpdateMessage(`❌ Auto-Updater Fehler: ${errorMsg}`);
    }
  };

  useEffect(() => {
    fetchMatchdayInfo();
    
    const interval = setInterval(() => {
      fetchAutoUpdaterStatus();
      setLastRefresh(new Date());
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 flex items-center">
          <span className="mr-3">🔄</span>
          Daten-Management
        </h1>
        
        {autoUpdaterStatus && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">🤖</span>
              Auto-Updater Status
              <span className="ml-2 text-sm text-gray-500">
                (aktualisiert: {formatTime(lastRefresh.toISOString())})
              </span>
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-white p-3 rounded-lg">
                <div className="flex items-center mb-2">
                  <span className={`w-3 h-3 rounded-full mr-2 ${
                    autoUpdaterStatus.is_running ? 'bg-green-500' : 'bg-red-500'
                  }`}></span>
                  <span className="font-medium">
                    {autoUpdaterStatus.is_running ? 'Aktiv' : 'Gestoppt'}
                  </span>
                </div>
                {autoUpdaterStatus.is_running && (
                  <div className="text-sm text-gray-600">
                    <p>Spieltag-Zeit: {autoUpdaterStatus.is_gameday_time ? '✅ Ja' : '❌ Nein'}</p>
                    <p>Updates durchgeführt: {autoUpdaterStatus.update_count}</p>
                    {autoUpdaterStatus.last_update && (
                      <p>Letztes Update: {formatTime(autoUpdaterStatus.last_update)}</p>
                    )}
                  </div>
                )}
              </div>
              
              <div className="bg-white p-3 rounded-lg">
                <h4 className="font-medium mb-2">Geplante Updates:</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  {autoUpdaterStatus.next_scheduled_updates.map((schedule, idx) => (
                    <div key={idx}>
                      <span className="font-medium">{schedule.day}</span> ({schedule.date})
                      <br />
                      <span className="text-xs">{schedule.times}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => toggleAutoUpdater(autoUpdaterStatus.is_running ? 'stop' : 'start')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  autoUpdaterStatus.is_running
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
              >
                {autoUpdaterStatus.is_running ? '⏹️ Stoppen' : '▶️ Starten'}
              </button>
              
              <button
                onClick={fetchAutoUpdaterStatus}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium"
              >
                🔄 Status aktualisieren
              </button>
            </div>
          </div>
        )}
        
        {matchdayInfo && (
          <div className="bg-green-50 rounded-lg p-4 mb-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">⚽</span>
              Spieltag-Informationen
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-3 rounded-lg">
                <h4 className="font-medium mb-2">Aktuelle Saison {matchdayInfo.current_season}</h4>
                <p className="text-sm text-gray-600">
                  Letzter kompletter Spieltag: <span className="font-bold">{matchdayInfo.last_completed_matchday}</span>
                </p>
                <p className="text-sm text-gray-600">
                  Spiele am Wochenende: <span className="font-bold">{matchdayInfo.weekend_matches}</span>
                </p>
                <p className="text-sm">
                  <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                    matchdayInfo.is_game_weekend ? 'bg-orange-500' : 'bg-gray-400'
                  }`}></span>
                  {matchdayInfo.is_game_weekend ? 'Spielwochenende' : 'Kein Spielwochenende'}
                </p>
              </div>
              
              <div className="bg-white p-3 rounded-lg">
                <h4 className="font-medium mb-2">Kommende Spieltage</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  {matchdayInfo.upcoming_matchdays.map((matchday, idx) => (
                    <div key={idx}>
                      <span className="font-medium">Spieltag {matchday.matchday}</span>
                      <br />
                      <span className="text-xs">
                        {matchday.matches_count} Spiele ab {formatTime(matchday.next_match_date)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">🔧</span>
            Manuelles Update
          </h2>
          
          <p className="text-gray-600 mb-4">
            Führe ein sofortiges Update aller Bundesliga-Daten durch. Dies holt die neuesten 
            Spielergebnisse und Tabellenstände von der OpenLigaDB.
          </p>
          
          <button
            onClick={performManualUpdate}
            disabled={isUpdating}
            className={`px-6 py-3 rounded-lg font-medium ${
              isUpdating
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600'
            } text-white flex items-center`}
          >
            {isUpdating ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Update läuft...
              </>
            ) : (
              <>
                <span className="mr-2">🚀</span>
                Jetzt aktualisieren
              </>
            )}
          </button>
        </div>
        
        {updateMessage && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium mb-2">Update-Status:</h3>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap">
              {updateMessage}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default UpdatePage;
