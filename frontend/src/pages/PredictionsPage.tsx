import { useState, useEffect } from 'react'
import axios from 'axios'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'react-chartjs-2'
import { usePredictions, useMatchdayInfo } from '../services/api'

// Chart.js registrieren
ChartJS.register(ArcElement, Tooltip, Legend)

// Typdefinitionen hinzufügen
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

interface FormFactor {
  home_form: number;
  away_form: number;
  home_xg_last_6: number;
  away_xg_last_6: number;
}

interface Prediction {
  match: Match;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  predicted_score: string;
  form_factors: FormFactor;
}

const PredictionsPage = () => {
  const { data: matchdayInfo, loading: matchdayLoading, error: matchdayError } = useMatchdayInfo()
  
  // Initialer Spieltag: verwende aktuellen Spieltag oder 3 als Fallback
  const [matchday, setMatchday] = useState(3)
  
  // Aktualisiere den Default-Spieltag wenn matchdayInfo geladen wurde
  useEffect(() => {
    if (matchdayInfo && !matchdayLoading) {
      setMatchday(matchdayInfo.current_matchday)
    }
  }, [matchdayInfo, matchdayLoading])
  
  // Verwenden des benutzerdefinierten Hooks für die Vorhersagen
  const { data: predictions, loading, error } = usePredictions(matchday)

  // Generiere Optionen für das Dropdown
  const generateMatchdayOptions = () => {
    if (!matchdayInfo) return []
    
    const options = []
    const maxMatchday = 34 // Bundesliga hat 34 Spieltage
    
    for (let i = 1; i <= maxMatchday; i++) {
      const isAvailable = i <= matchdayInfo.predictions_available_until
      
      let label = `Spieltag ${i}`
      if (!isAvailable) label += ' - nicht verfügbar'
      
      options.push({
        value: i,
        label,
        disabled: !isAvailable
      })
    }
    
    return options
  }

  const handleMatchdayChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedMatchday = parseInt(event.target.value)
    setMatchday(selectedMatchday)
  }

  const getPieChartData = (prediction: Prediction) => {
    return {
      labels: ['Heimsieg', 'Unentschieden', 'Auswärtssieg'],
      datasets: [
        {
          data: [
            prediction.home_win_prob * 100, 
            prediction.draw_prob * 100, 
            prediction.away_win_prob * 100
          ],
          backgroundColor: [
            'rgba(0, 30, 80, 0.8)',  // Dunkelblau (Heimsieg)
            'rgba(128, 128, 128, 0.8)',  // Grau (Unentschieden)
            'rgba(210, 5, 21, 0.8)'  // Rot (Auswärtssieg)
          ],
          borderColor: [
            'rgba(0, 30, 80, 1)',
            'rgba(128, 128, 128, 1)',
            'rgba(210, 5, 21, 1)'
          ],
          borderWidth: 1,
        },
      ],
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Bundesliga Vorhersagen</h1>
        
        {matchdayLoading ? (
          <div className="text-sm text-gray-500">Lade Spieltag-Info...</div>
        ) : matchdayError ? (
          <div className="text-sm text-red-500">Fehler beim Laden der Spieltag-Info</div>
        ) : (
          <div className="flex items-center gap-4">
            <label htmlFor="matchday-select" className="text-sm font-medium">
              Spieltag auswählen:
            </label>
            <select
              id="matchday-select"
              value={matchday}
              onChange={handleMatchdayChange}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {generateMatchdayOptions().map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  className={option.disabled ? 'text-gray-400' : ''}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <h2 className="text-center mb-6 text-lg text-gray-600">
        Vorhersagen für Spieltag {matchday}
        {matchdayInfo && matchday > matchdayInfo.predictions_available_until && (
          <span className="block text-sm text-red-500 mt-1">
            Vorhersagen noch nicht verfügbar
          </span>
        )}
      </h2>

      {loading ? (
        <div className="text-center">
          <p>Lade Vorhersagen...</p>
        </div>
      ) : error ? (
        <div className="text-center text-red-600">
          <p>{error}</p>
        </div>
      ) : matchdayInfo && matchday > matchdayInfo.predictions_available_until ? (
        <div className="text-center text-gray-600">
          <div className="bg-gray-100 rounded-lg p-8">
            <h3 className="text-xl font-semibold mb-2">Vorhersagen noch nicht verfügbar</h3>
            <p>Vorhersagen sind nur bis Spieltag {matchdayInfo.predictions_available_until} verfügbar.</p>
            <p className="text-sm mt-2">
              Saison: {matchdayInfo.season}
            </p>
          </div>
        </div>
      ) : predictions && predictions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {predictions.map((prediction, index) => (
            <div key={index} className="card">
              <div className="flex justify-between items-center mb-4">
                <div className="font-bold text-lg">{prediction.match.home_team.name}</div>
                <div className="text-2xl font-bold text-gray-700">vs</div>
                <div className="font-bold text-lg text-right">{prediction.match.away_team.name}</div>
              </div>
              
              <div className="mb-4">
                <h3 className="text-center mb-2">Wahrscheinlichkeiten</h3>
                <div className="h-64">
                  <Pie data={getPieChartData(prediction)} options={{ maintainAspectRatio: false }} />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 className="font-semibold mb-1">Vorhergesagtes Ergebnis:</h4>
                  <p className="text-2xl font-bold text-center">{prediction.predicted_score}</p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Favorisiertes Team:</h4>
                  <p className="text-center">
                    {prediction.home_win_prob > prediction.away_win_prob 
                      ? prediction.match.home_team.name 
                      : prediction.away_win_prob > prediction.home_win_prob 
                        ? prediction.match.away_team.name 
                        : "Unentschieden"}
                  </p>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Formfaktoren:</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p><span className="font-medium">Form {prediction.match.home_team.name}:</span> {prediction.form_factors.home_form.toFixed(1)}%</p>
                    <p><span className="font-medium">Tore letzte 14 Spiele:</span> {prediction.form_factors.home_goals_last_14}</p>
                  </div>
                  <div>
                    <p><span className="font-medium">Form {prediction.match.away_team.name}:</span> {prediction.form_factors.away_form.toFixed(1)}%</p>
                    <p><span className="font-medium">Tore letzte 14 Spiele:</span> {prediction.form_factors.away_goals_last_14}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center">
          <p>Keine Vorhersagen für diesen Spieltag verfügbar.</p>
        </div>
      )}
    </div>
  )
}

export default PredictionsPage
