import { useState, useEffect } from 'react'
import axios from 'axios'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { Line } from 'react-chartjs-2'

// Chart.js registrieren
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const TeamAnalysisPage = () => {
  const [teams, setTeams] = useState([
    { id: 1, name: 'FC Bayern München', short_name: 'FCB' },
    { id: 2, name: 'Borussia Dortmund', short_name: 'BVB' },
    { id: 3, name: 'RB Leipzig', short_name: 'RBL' },
    { id: 4, name: 'Bayer Leverkusen', short_name: 'B04' },
    // Weitere Teams hier
  ])
  const [selectedTeamId, setSelectedTeamId] = useState(1)
  const [teamData, setTeamData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchTeamData = async () => {
      if (!selectedTeamId) return

      try {
        setLoading(true)
        
        // Hier würde eine API-Anfrage gemacht werden
        // Für Beispielzwecke generieren wir Mock-Daten
        const mockData = generateMockTeamData(selectedTeamId)
        
        setTeamData(mockData)
        setError(null)
      } catch (err) {
        console.error('Fehler beim Abrufen der Team-Daten:', err)
        setError('Fehler beim Laden der Team-Daten. Bitte versuchen Sie es später erneut.')
      } finally {
        setLoading(false)
      }
    }

    fetchTeamData()
  }, [selectedTeamId])

  const generateMockTeamData = (teamId) => {
    const team = teams.find(t => t.id === teamId)
    
    // Mock-Daten für die letzten 6 Spieltage
    const lastMatches = Array.from({ length: 6 }, (_, i) => {
      const isHome = Math.random() > 0.5
      const opponent = teams.find(t => t.id !== teamId && Math.random() > 0.7) || 
                      teams.find(t => t.id !== teamId)
      
      const goalsScored = Math.floor(Math.random() * 4)
      const goalsConceded = Math.floor(Math.random() * 3)
      
      return {
        matchday: 34 - 5 + i, // Beispiel: Spieltage 29-34
        opponent: opponent.name,
        isHome,
        goalsScored,
        goalsConceded,
        result: goalsScored > goalsConceded ? 'W' : goalsScored < goalsConceded ? 'L' : 'D',
        xG: (Math.random() * 3).toFixed(1),
        possession: Math.floor(Math.random() * 30 + 40) // 40-70%
      }
    })
    
    return {
      team,
      lastMatches,
      form: (Math.random() * 0.4 + 0.5).toFixed(2), // 50-90%
      stats: {
        goalsScored: lastMatches.reduce((sum, match) => sum + match.goalsScored, 0),
        goalsConceded: lastMatches.reduce((sum, match) => sum + match.goalsConceded, 0),
        xGFor: lastMatches.reduce((sum, match) => sum + parseFloat(match.xG), 0).toFixed(1),
        avgPossession: (lastMatches.reduce((sum, match) => sum + match.possession, 0) / 6).toFixed(1)
      }
    }
  }

  const handleTeamChange = (e) => {
    setSelectedTeamId(Number(e.target.value))
  }

  // Chartdaten für Tore und xG
  const getChartData = () => {
    if (!teamData) return null
    
    const labels = teamData.lastMatches.map(match => `ST ${match.matchday}`)
    
    return {
      labels,
      datasets: [
        {
          label: 'Erzielte Tore',
          data: teamData.lastMatches.map(match => match.goalsScored),
          borderColor: 'rgb(0, 30, 80)',
          backgroundColor: 'rgba(0, 30, 80, 0.5)',
        },
        {
          label: 'Expected Goals (xG)',
          data: teamData.lastMatches.map(match => match.xG),
          borderColor: 'rgb(210, 5, 21)',
          backgroundColor: 'rgba(210, 5, 21, 0.5)',
        },
      ],
    }
  }

  return (
    <div>
      <h1 className="text-center mb-8">Team-Analyse</h1>
      
      <div className="mb-8">
        <label htmlFor="team-select" className="block mb-2 font-medium">
          Team auswählen:
        </label>
        <select
          id="team-select"
          className="w-full max-w-md p-2 border border-gray-300 rounded"
          value={selectedTeamId}
          onChange={handleTeamChange}
        >
          {teams.map(team => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>
      </div>
      
      {loading ? (
        <div className="text-center">
          <p>Lade Team-Daten...</p>
        </div>
      ) : error ? (
        <div className="text-center text-red-600">
          <p>{error}</p>
        </div>
      ) : teamData ? (
        <div>
          <div className="card mb-8">
            <h2 className="text-xl font-bold mb-4">{teamData.team.name} - Formübersicht</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-semibold mb-2">Aktuelle Form: {(parseFloat(teamData.form) * 100).toFixed(0)}%</h3>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-bundesliga-red h-4 rounded-full" 
                    style={{ width: `${parseFloat(teamData.form) * 100}%` }}
                  ></div>
                </div>
                
                <h3 className="font-semibold mt-6 mb-2">Letzte 6 Spiele:</h3>
                <div className="grid grid-cols-6 gap-2">
                  {teamData.lastMatches.map((match, index) => (
                    <div 
                      key={index} 
                      className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-white ${
                        match.result === 'W' ? 'bg-green-600' : 
                        match.result === 'D' ? 'bg-yellow-500' : 
                        'bg-red-600'
                      }`}
                    >
                      {match.result}
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Statistiken (letzte 6 Spiele)</h3>
                <ul className="space-y-2">
                  <li>Erzielte Tore: <span className="font-bold">{teamData.stats.goalsScored}</span></li>
                  <li>Gegentore: <span className="font-bold">{teamData.stats.goalsConceded}</span></li>
                  <li>Expected Goals (xG): <span className="font-bold">{teamData.stats.xGFor}</span></li>
                  <li>Durchschnittlicher Ballbesitz: <span className="font-bold">{teamData.stats.avgPossession}%</span></li>
                </ul>
              </div>
            </div>
          </div>
          
          <div className="card">
            <h3 className="font-semibold mb-4">Tore vs. Expected Goals (xG) - Letzte 6 Spiele</h3>
            <div className="h-80">
              <Line 
                data={getChartData()} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true
                    }
                  }
                }} 
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <p>Bitte wählen Sie ein Team aus.</p>
        </div>
      )}
    </div>
  )
}

export default TeamAnalysisPage
