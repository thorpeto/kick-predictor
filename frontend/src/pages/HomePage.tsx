import { useState, useEffect } from 'react'
import axios from 'axios'

const HomePage = () => {
  const [nextMatchday, setNextMatchday] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchNextMatchday = async () => {
      try {
        setLoading(true)
        const response = await axios.get('/api/next-matchday')
        setNextMatchday(response.data)
        setError(null)
      } catch (err) {
        console.error('Fehler beim Abrufen des nächsten Spieltags:', err)
        setError('Fehler beim Laden der Daten. Bitte versuchen Sie es später erneut.')
      } finally {
        setLoading(false)
      }
    }

    fetchNextMatchday()
  }, [])

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
            Unser Algorithmus analysiert die letzten 6 Wochen der Bundesliga und berücksichtigt dabei Tore, Expected Goals, Ballbesitz und weitere Faktoren, um präzise Vorhersagen zu treffen.
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
        <h2 className="text-center mb-6">Der nächste Spieltag</h2>
        {loading ? (
          <p className="text-center">Lade Spieltag-Daten...</p>
        ) : error ? (
          <p className="text-center text-red-600">{error}</p>
        ) : nextMatchday && nextMatchday.matches ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {nextMatchday.matches.map((match, index) => (
              <div key={index} className="card">
                <div className="flex justify-between items-center">
                  <div className="font-bold">{match.home}</div>
                  <div className="text-gray-600">vs.</div>
                  <div className="font-bold text-right">{match.away}</div>
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
        <h2 className="mb-4">Mach dich bereit für den nächsten Spieltag</h2>
        <p className="mb-6">
          Wirf einen Blick auf unsere aktuellen Vorhersagen und entdecke, welche Teams die besten Gewinnchancen haben.
        </p>
        <a href="/predictions" className="btn btn-primary">Zu den Vorhersagen</a>
      </section>
    </div>
  )
}

export default HomePage
