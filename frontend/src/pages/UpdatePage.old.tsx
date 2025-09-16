import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { buildApiUrl } from '../services/api'

interface NextMatchdayInfo {
  current_season: string;
  last_completed_matchday: number;
  next_matchday: number;
  next_matchday_info: {
    total_matches: number;
    finished_matches: number;
    first_match_date: string;
    last_match_date: string;
    is_complete: boolean;
  };
  update_recommended: boolean;
}

interface UpdateStatus {
  status: string;
  message: string;
  updated_at: string;
  stats?: {
    finished_matches: number;
    last_completed_matchday: number;
    total_matches_updated: number;
  };
}

const UpdatePage = () => {
  const [matchdayInfo, setMatchdayInfo] = useState<NextMatchdayInfo | null>(null)
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchMatchdayInfo()
  }, [])

  const fetchMatchdayInfo = async () => {
    try {
      setLoading(true)
      const response = await axios.get(buildApiUrl('/next-matchday-info'))
      setMatchdayInfo(response.data)
    } catch (err: any) {
      console.error('Fehler beim Laden der Spieltag-Info:', err)
      setError('Fehler beim Laden der Spieltag-Informationen')
    } finally {
      setLoading(false)
    }
  }

  const performUpdate = async () => {
    try {
      setIsUpdating(true)
      setError(null)
      
      const response = await axios.post(buildApiUrl('/update-data'))
      setUpdateStatus(response.data)
      
      // Aktualisiere die Spieltag-Info nach dem Update
      await fetchMatchdayInfo()
      
    } catch (err: any) {
      console.error('Fehler beim Update:', err)
      setError('Fehler beim Aktualisieren der Daten')
    } finally {
      setIsUpdating(false)
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('de-DE', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getUpdateButtonColor = () => {
    if (matchdayInfo?.update_recommended) {
      return 'bg-orange-500 hover:bg-orange-600 text-white'
    }
    return 'bg-green-500 hover:bg-green-600 text-white'
  }

  const getUpdateButtonText = () => {
    if (isUpdating) return 'Aktualisiere...'
    if (matchdayInfo?.update_recommended) return '🔄 Neue Daten verfügbar - Jetzt aktualisieren'
    return '✅ Daten aktualisieren'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Lade Update-Informationen...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8 text-center">Daten-Update Management</h1>
      
      {/* Spieltag Status */}
      {matchdayInfo && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            📅 Spieltag-Status {matchdayInfo.current_season}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="font-medium">Letzter abgeschlossener Spieltag:</span>
                <span className="text-green-600 font-bold">{matchdayInfo.last_completed_matchday}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="font-medium">Nächster Spieltag:</span>
                <span className="text-blue-600 font-bold">{matchdayInfo.next_matchday}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="font-medium">Spiele im nächsten Spieltag:</span>
                <span className="font-bold">
                  {matchdayInfo.next_matchday_info.finished_matches} / {matchdayInfo.next_matchday_info.total_matches}
                </span>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <span className="font-medium block mb-1">Erster Anstoß:</span>
                <span className="text-gray-600 text-sm">
                  {formatDate(matchdayInfo.next_matchday_info.first_match_date)}
                </span>
              </div>
              
              <div>
                <span className="font-medium block mb-1">Letzter Anstoß:</span>
                <span className="text-gray-600 text-sm">
                  {formatDate(matchdayInfo.next_matchday_info.last_match_date)}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="font-medium">Spieltag abgeschlossen:</span>
                <span className={`px-2 py-1 rounded text-sm font-medium ${
                  matchdayInfo.next_matchday_info.is_complete 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {matchdayInfo.next_matchday_info.is_complete ? '✅ Ja' : '⏳ Nein'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Update-Empfehlung */}
          {matchdayInfo.update_recommended && (
            <div className="mt-4 p-4 bg-orange-50 border-l-4 border-orange-400 rounded">
              <div className="flex items-center">
                <div className="ml-3">
                  <p className="text-sm text-orange-700">
                    <strong>🔔 Neue Ergebnisse verfügbar!</strong> Es sind neue Spielergebnisse verfügbar. 
                    Aktualisiere die Daten, um die neuesten Vorhersagen und Statistiken zu erhalten.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Update-Steuerung */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          🔄 Daten-Update
        </h2>
        
        <div className="space-y-4">
          <p className="text-gray-600">
            Aktualisiere die Spielergebnisse und Teamstatistiken mit den neuesten Daten von OpenLigaDB.
            Dies verbessert die Genauigkeit der Vorhersagen und aktualisiert die Tabelle.
          </p>
          
          <button
            onClick={performUpdate}
            disabled={isUpdating}
            className={`px-6 py-3 rounded-lg font-medium transition-colors duration-200 ${getUpdateButtonColor()} ${
              isUpdating ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isUpdating && (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {getUpdateButtonText()}
          </button>
        </div>
      </div>
      
      {/* Update-Status */}
      {updateStatus && (
        <div className={`rounded-lg shadow-md p-6 mb-6 ${
          updateStatus.status === 'success' ? 'bg-green-50 border-l-4 border-green-400' : 
          updateStatus.status === 'no_new_data' ? 'bg-blue-50 border-l-4 border-blue-400' :
          'bg-red-50 border-l-4 border-red-400'
        }`}>
          <h3 className="text-lg font-semibold mb-2 flex items-center">
            {updateStatus.status === 'success' ? '✅' : updateStatus.status === 'no_new_data' ? 'ℹ️' : '❌'} 
            <span className="ml-2">Update-Ergebnis</span>
          </h3>
          
          <p className={`mb-3 ${
            updateStatus.status === 'success' ? 'text-green-700' :
            updateStatus.status === 'no_new_data' ? 'text-blue-700' :
            'text-red-700'
          }`}>
            {updateStatus.message}
          </p>
          
          {updateStatus.stats && (
            <div className="space-y-2 text-sm text-gray-600">
              <p><strong>Beendete Spiele:</strong> {updateStatus.stats.finished_matches}</p>
              <p><strong>Letzter Spieltag:</strong> {updateStatus.stats.last_completed_matchday}</p>
              <p><strong>Aktualisierte Matches:</strong> {updateStatus.stats.total_matches_updated}</p>
            </div>
          )}
          
          <p className="text-xs text-gray-500 mt-3">
            Aktualisiert am: {formatDate(updateStatus.updated_at)}
          </p>
        </div>
      )}
      
      {/* Fehler-Anzeige */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Hilfe-Sektion */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          💡 Wie funktioniert das Update?
        </h3>
        
        <div className="space-y-3 text-sm text-gray-700">
          <p>
            <strong>Automatisch:</strong> Das System prüft regelmäßig auf neue Ergebnisse und aktualisiert die Daten.
          </p>
          <p>
            <strong>Manuell:</strong> Nutze den Update-Button oben, um sofort nach neuen Ergebnissen zu suchen.
          </p>
          <p>
            <strong>Verbesserungen:</strong> Nach jedem Update werden die Vorhersagen mit den neuesten Team-Formen neu berechnet.
          </p>
          <p className="text-xs text-gray-500">
            Datenquelle: OpenLigaDB • Update-Intervall: Alle 2 Stunden während Spieltagen
          </p>
        </div>
      </div>
    </div>
  )
}

export default UpdatePage