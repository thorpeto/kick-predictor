import { useState, useEffect } from 'react'
import { useUpcomingMatches } from '../services/api'

// Typdefinitionen werden aus der API importiert
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

const HomePage = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Verwenden des benutzerdefinierten Hooks für kommende Spiele
  const { data: upcomingData, loading: matchesLoading, error: matchesError } = useUpcomingMatches()

  // Aktualisiere den Ladezustand wenn der Hook fertig ist
  useEffect(() => {
    if (!matchesLoading) {
      setLoading(false)
    }
    if (matchesError) {
      setError('Fehler beim Laden der Daten. Bitte versuchen Sie es später erneut.')
    }
  }, [matchesLoading, matchesError])

  return (
    <div>
      <section className="text-center mb-12">
        <h1 className="mb-4">Willkommen bei Kick Predictor</h1>
        <p className="text-xl max-w-3xl mx-auto">
          Dein Tool für datengestützte Vorhersagen zu Bundesliga-Spielergebnissen basierend auf aktuellen Formkurven und historischen Daten.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div className="card">
          <h2 className="text-bundesliga-red mb-4">Präzise Vorhersagen</h2>
          <p>
            Unser Algorithmus analysiert die letzten 6 Wochen der Bundesliga und berücksichtigt dabei Tore, Expected Goals und weitere Faktoren, um präzise Vorhersagen zu treffen.
          </p>
        </div>
        <div className="card">
          <h2 className="text-bundesliga-red mb-4">Form-Basierte Analyse</h2>
          <p>
            Unsere Formkurven zeigen dir, welche Teams aktuell in Top-Form sind und wie sich ihre Leistung in den letzten Wochen entwickelt hat.
          </p>
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-center mb-6">
          {upcomingData ? `Spieltag ${upcomingData.matchday}` : 'Kommender Spieltag'}
        </h2>
        {loading ? (
          <p className="text-center">Lade Spieltag-Daten...</p>
        ) : error ? (
          <p className="text-center text-red-600">{error}</p>
        ) : upcomingData && upcomingData.matches && upcomingData.matches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {upcomingData.matches.map((match: Match) => (
              <div key={match.id} className="card">
                <div className="flex justify-between items-center">
                  <div className="font-bold">{match.home_team.name}</div>
                  <div className="text-gray-600">vs.</div>
                  <div className="font-bold text-right">{match.away_team.name}</div>
                </div>
                <div className="text-center text-gray-500 mt-2">
                  {new Date(match.date).toLocaleString('de-DE', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center">Keine Spieldaten verfügbar.</p>
        )}
      </section>

      <section className="text-center">
        <h2 className="mb-4">Mach dich bereit für den kommenden Spieltag</h2>
        <p className="mb-6">
          Wirf einen Blick auf unsere aktuellen Vorhersagen und entdecke, welche Teams die besten Gewinnchancen haben.
        </p>
        <a href="/predictions" className="btn btn-primary">Zu den Vorhersagen</a>
      </section>
    </div>
  )
}

export default HomePage
