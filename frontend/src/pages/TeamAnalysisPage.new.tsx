import { useState, useEffect } from 'react'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { Line } from 'react-chartjs-2'
import { fetchTeamForm, useTeamMatches } from '../services/api'

// Chart.js registrieren
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

// Typdefinitionen
interface Team {
  id: number;
  name: string;
  short_name: string;
  logo_url?: string;
}

interface TeamData {
  team: Team;
  form: number;
  lastMatches: any[];
  stats: {
    goalsScored: number;
    goalsConceded: number;
    xGFor: string;
    avgPossession: string;
  };
}

const TeamAnalysisPage = () => {
  // Liste der Teams (später durch API-Aufruf ersetzen)
  const [teams, setTeams] = useState<Team[]>([
    { id: 1, name: 'FC Bayern München', short_name: 'FCB' },
    { id: 2, name: 'Borussia Dortmund', short_name: 'BVB' },
    { id: 3, name: 'RB Leipzig', short_name: 'RBL' },
    { id: 4, name: 'Bayer Leverkusen', short_name: 'B04' },
    { id: 5, name: 'Borussia Mönchengladbach', short_name: 'BMG' },
    { id: 6, name: 'VfL Wolfsburg', short_name: 'WOB' },
    { id: 7, name: 'Eintracht Frankfurt', short_name: 'SGE' },
    { id: 8, name: 'VfB Stuttgart', short_name: 'VFB' },
  ])
  const [selectedTeamId, setSelectedTeamId] = useState<number>(1)
  const [teamForm, setTeamForm] = useState<number | null>(null)
  const [teamData, setTeamData] = useState<TeamData | null>(null)
  const [formLoading, setFormLoading] = useState<boolean>(false)
  const [formError, setFormError] = useState<string | null>(null)

  // Hole Spieldaten mit dem useTeamMatches Hook
  const { data: matchesData, loading: matchesLoading, error: matchesError } = useTeamMatches(selectedTeamId)

  // Hole die Form-Daten separat
  useEffect(() => {
    const getTeamForm = async () => {
      if (!selectedTeamId) return

      try {
        setFormLoading(true)
        const form = await fetchTeamForm(selectedTeamId)
        setTeamForm(form)
        setFormError(null)
      } catch (err) {
        console.error('Fehler beim Abrufen der Team-Form:', err)
        setFormError('Fehler beim Laden der Form-Daten')
      } finally {
        setFormLoading(false)
      }
    }

    getTeamForm()
  }, [selectedTeamId])

  // Verarbeite die erhaltenen Daten
  useEffect(() => {
    if (teamForm === null) return

    const team = teams.find(t => t.id === selectedTeamId) || {
      id: selectedTeamId,
      name: 'Unbekanntes Team',
      short_name: 'UNK'
    }

    // Wenn keine Spieldaten vorhanden sind, zeige nur die Form an
    if (!matchesData || matchesData.length === 0) {
      setTeamData({
        team,
        form: teamForm,
        lastMatches: [],
        stats: {
          goalsScored: 0,
          goalsConceded: 0,
          xGFor: '0.0',
          avgPossession: '0.0'
        }
      });
      return;
    }

    // Verarbeite die Spieldaten
    const processedMatches = matchesData.map(match => {
      const isHome = match.match.home_team.id === selectedTeamId
      
      return {
        matchday: match.match.matchday,
        date: new Date(match.match.date).toLocaleDateString('de-DE'),
        opponent: isHome ? match.match.away_team.name : match.match.home_team.name,
        isHome,
        goalsScored: isHome ? match.home_goals : match.away_goals,
        goalsConceded: isHome ? match.away_goals : match.home_goals,
        result: isHome 
          ? (match.home_goals > match.away_goals ? 'W' : match.home_goals < match.away_goals ? 'L' : 'D')
          : (match.away_goals > match.home_goals ? 'W' : match.away_goals < match.home_goals ? 'L' : 'D'),
        xG: isHome ? match.home_xg.toFixed(1) : match.away_xg.toFixed(1),
        possession: isHome ? match.home_possession : match.away_possession
      }
    }).sort((a, b) => a.matchday - b.matchday) // Sortiere nach Spieltag

    // Berechne die Statistiken
    const goalsScored = processedMatches.reduce((sum, match) => sum + match.goalsScored, 0)
    const goalsConceded = processedMatches.reduce((sum, match) => sum + match.goalsConceded, 0)
    const xGFor = processedMatches.reduce((sum, match) => sum + parseFloat(match.xG), 0).toFixed(1)
    const avgPossession = (processedMatches.reduce((sum, match) => sum + match.possession, 0) / processedMatches.length).toFixed(1)

    // Setze die Teamdaten
    setTeamData({
      team,
      form: teamForm,
      lastMatches: processedMatches,
      stats: {
        goalsScored,
        goalsConceded,
        xGFor,
        avgPossession
      }
    })
  }, [matchesData, teamForm, selectedTeamId, teams])

  const handleTeamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
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

  // Bestimme den Ladezustand
  const isLoading = matchesLoading || formLoading
  const hasError = matchesError || formError
  const errorMessage = matchesError || formError || ''

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
          disabled={isLoading}
        >
          {teams.map(team => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>
      </div>
      
      {isLoading ? (
        <div className="text-center">
          <p>Lade Team-Daten...</p>
        </div>
      ) : hasError ? (
        <div className="text-center text-red-600">
          <p>{errorMessage}</p>
        </div>
      ) : teamData ? (
        <div>
          <div className="card mb-8">
            <h2 className="text-xl font-bold mb-4">{teamData.team.name} - Formübersicht</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-semibold mb-2">Aktuelle Form: {(teamData.form * 100).toFixed(0)}%</h3>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-bundesliga-red h-4 rounded-full" 
                    style={{ width: `${teamData.form * 100}%` }}
                  ></div>
                </div>
                
                <h3 className="font-semibold mt-6 mb-2">Letzte {teamData.lastMatches.length} Spiele:</h3>
                {teamData.lastMatches.length > 0 ? (
                  <div className="grid grid-cols-6 gap-2">
                    {teamData.lastMatches.map((match, index) => (
                      <div 
                        key={index} 
                        className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-white ${
                          match.result === 'W' ? 'bg-green-600' : 
                          match.result === 'D' ? 'bg-yellow-500' : 
                          'bg-red-600'
                        }`}
                        title={`${match.isHome ? 'Heim' : 'Auswärts'} gegen ${match.opponent}: ${match.goalsScored}:${match.goalsConceded}`}
                      >
                        {match.result}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 italic">
                    Noch keine Spiele in dieser Saison. Nächster Spieltag: 3
                  </div>
                )}
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Statistiken {teamData.lastMatches.length > 0 ? `(letzte ${teamData.lastMatches.length} Spiele)` : ''}</h3>
                {teamData.lastMatches.length > 0 ? (
                  <ul className="space-y-2">
                    <li>Erzielte Tore: <span className="font-bold">{teamData.stats.goalsScored}</span></li>
                    <li>Gegentore: <span className="font-bold">{teamData.stats.goalsConceded}</span></li>
                    <li>Expected Goals (xG): <span className="font-bold">{teamData.stats.xGFor}</span></li>
                    <li>Durchschnittlicher Ballbesitz: <span className="font-bold">{teamData.stats.avgPossession}%</span></li>
                  </ul>
                ) : (
                  <div className="text-gray-500 italic">
                    Keine Statistiken verfügbar.
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="card">
            <h3 className="font-semibold mb-4">Tore vs. Expected Goals (xG){teamData.lastMatches.length > 0 ? ` - Letzte ${teamData.lastMatches.length} Spiele` : ''}</h3>
            {teamData.lastMatches.length > 0 ? (
              <div className="h-80">
                <Line 
                  data={getChartData() as any} 
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
            ) : (
              <div className="text-center py-8 text-gray-500 italic">
                Keine Spieldaten vorhanden, um ein Diagramm anzuzeigen.
              </div>
            )}
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
