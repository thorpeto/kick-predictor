import { useState, useEffect } from 'react'
import axios from 'axios'
import { buildApiUrl } from '../services/api'

// Interface-Definitionen
interface Team {
  id: number;
  name: string;
  short_name: string;
  logo_url?: string;
}

interface Match {
  id: number;
  home_team: Team;
  away_team: Team;
  date: string;
  matchday: number;
  season: string;
}

interface PredictionQualityEntry {
  match: Match;
  predicted_score: string;
  actual_score: string;
  predicted_home_win_prob: number;
  predicted_draw_prob: number;
  predicted_away_win_prob: number;
  hit_type: 'exact_match' | 'tendency_match' | 'miss';
  tendency_correct: boolean;
  exact_score_correct: boolean;
}

interface PredictionQualityStats {
  total_predictions: number;
  exact_matches: number;
  tendency_matches: number;
  misses: number;
  exact_match_rate: number;
  tendency_match_rate: number;
  overall_accuracy: number;
  quality_score: number;
}

interface QualityData {
  entries: PredictionQualityEntry[];
  stats: PredictionQualityStats;
}

const QualityPage = () => {
  const [qualityData, setQualityData] = useState<QualityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchQualityData()
  }, [])

  const fetchQualityData = async () => {
    try {
      setLoading(true)
      const url = buildApiUrl('/prediction-quality')
      console.log('Fetching quality data from:', url)
      
      const response = await axios.get(url)
      setQualityData(response.data)
      setError(null)
    } catch (err) {
      console.error('Fehler beim Laden der Qualitätsdaten:', err)
      setError('Fehler beim Laden der Daten. Bitte versuchen Sie es später erneut.')
    } finally {
      setLoading(false)
    }
  }

  const getHitTypeIcon = (hitType: string) => {
    switch (hitType) {
      case 'exact_match':
        return '🎯'
      case 'tendency_match':
        return '✅'
      case 'miss':
        return '❌'
      default:
        return '❓'
    }
  }

  const getHitTypeText = (hitType: string) => {
    switch (hitType) {
      case 'exact_match':
        return 'Volltreffer'
      case 'tendency_match':
        return 'Tendenz richtig'
      case 'miss':
        return 'Fehlschlag'
      default:
        return 'Unbekannt'
    }
  }

  const getHitTypeColor = (hitType: string) => {
    switch (hitType) {
      case 'exact_match':
        return 'text-green-700 bg-green-100'
      case 'tendency_match':
        return 'text-blue-700 bg-blue-100'
      case 'miss':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600'
    if (score >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (loading) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-8">Vorhersagequalität</h1>
        <p>Lade Qualitätsdaten...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-8">Vorhersagequalität</h1>
        <div className="text-red-600">
          <p>{error}</p>
          <button 
            onClick={fetchQualityData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    )
  }

  if (!qualityData || !qualityData.stats) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-8">Vorhersagequalität</h1>
        <p>Keine Qualitätsdaten verfügbar.</p>
      </div>
    )
  }

  const { entries, stats } = qualityData

  return (
    <div>
      <h1 className="text-2xl font-bold mb-8 text-center">Vorhersagequalität</h1>
      
      {/* Statistik-Übersicht */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Gesamtstatistik</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="card text-center">
            <h3 className="font-semibold text-gray-600">Gesamt</h3>
            <p className="text-2xl font-bold">{stats.total_predictions}</p>
            <p className="text-sm text-gray-500">Vorhersagen</p>
          </div>
          
          <div className="card text-center">
            <h3 className="font-semibold text-green-600">Volltreffer</h3>
            <p className="text-2xl font-bold text-green-600">{stats.exact_matches}</p>
            <p className="text-sm text-gray-500">{formatPercentage(stats.exact_match_rate)}</p>
          </div>
          
          <div className="card text-center">
            <h3 className="font-semibold text-blue-600">Tendenz richtig</h3>
            <p className="text-2xl font-bold text-blue-600">{stats.tendency_matches}</p>
            <p className="text-sm text-gray-500">{formatPercentage(stats.tendency_match_rate)}</p>
          </div>
          
          <div className="card text-center">
            <h3 className="font-semibold text-red-600">Fehlschläge</h3>
            <p className="text-2xl font-bold text-red-600">{stats.misses}</p>
            <p className="text-sm text-gray-500">{formatPercentage(1 - stats.overall_accuracy)}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card text-center">
            <h3 className="font-semibold text-gray-600">Gesamtgenauigkeit</h3>
            <p className={`text-3xl font-bold ${getScoreColor(stats.overall_accuracy)}`}>
              {formatPercentage(stats.overall_accuracy)}
            </p>
            <p className="text-sm text-gray-500">Tendenz oder besser</p>
          </div>
          
          <div className="card text-center">
            <h3 className="font-semibold text-gray-600">Qualitätsscore</h3>
            <p className={`text-3xl font-bold ${getScoreColor(stats.quality_score)}`}>
              {formatPercentage(stats.quality_score)}
            </p>
            <p className="text-sm text-gray-500">Gewichteter Score (3:1)</p>
          </div>
        </div>
      </div>

      {/* Detaillierte Ergebnisse */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Detaillierte Ergebnisse</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Spiel</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Spieltag</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Vorhersage</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Tatsächlich</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Ergebnis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {entries.map((entry, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{entry.match.home_team.short_name}</span>
                      <span className="text-gray-500 mx-2">vs</span>
                      <span className="font-medium">{entry.match.away_team.short_name}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(entry.match.date).toLocaleDateString('de-DE')}
                    </div>
                  </td>
                  
                  <td className="px-4 py-3 text-center">
                    <span className="text-sm font-medium">{entry.match.matchday}</span>
                  </td>
                  
                  <td className="px-4 py-3 text-center">
                    <span className="font-mono text-lg">{entry.predicted_score}</span>
                  </td>
                  
                  <td className="px-4 py-3 text-center">
                    <span className="font-mono text-lg font-bold">{entry.actual_score}</span>
                  </td>
                  
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getHitTypeColor(entry.hit_type)}`}>
                      <span className="mr-1">{getHitTypeIcon(entry.hit_type)}</span>
                      {getHitTypeText(entry.hit_type)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {entries.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>Noch keine abgeschlossenen Spiele für die Qualitätsanalyse verfügbar.</p>
            <p className="text-sm mt-2">Daten werden nach vollständigen Spieltagen aktualisiert.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default QualityPage