import { useEffect, useState } from 'react'
import axios from 'axios'

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

interface MatchResult {
  match: Match;
  home_goals: number;
  away_goals: number;
  home_xg: number;
  away_xg: number;
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

// API Service Configuration
// In der Produktionsumgebung sollte VITE_API_URL über Umgebungsvariablen gesetzt werden
const getApiUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Fallback für Entwicklung und basierend auf aktueller Umgebung
  if (window.location.hostname === 'localhost') {
    return '/api';
  }
  
  // Für GCP Deployment - anpassen je nach Setup
  if (window.location.hostname.includes('appspot.com') || 
      window.location.hostname.includes('run.app')) {
    // Standardmäßig nehmen wir an, dass die API unter /api erreichbar ist
    // wenn Backend und Frontend auf derselben Domain gehostet sind
    return '/api';
    
    // Alternativ können wir die vollständige URL des Backends verwenden
    // return 'https://backend-service-xxxxxx.an.r.appspot.com';
  }
  
  // Fallback
  return '/api';
}

const API_URL = getApiUrl();

export const fetchNextMatchday = async (): Promise<Match[]> => {
  try {
    const response = await axios.get(`${API_URL}/next-matchday`)
    return response.data
  } catch (error) {
    console.error('Fehler beim Abrufen des nächsten Spieltags:', error)
    throw error
  }
}

export const fetchPredictions = async (matchday: number): Promise<Prediction[]> => {
  try {
    const response = await axios.get(`${API_URL}/predictions/${matchday}`)
    return response.data
  } catch (error) {
    console.error(`Fehler beim Abrufen der Vorhersagen für Spieltag ${matchday}:`, error)
    throw error
  }
}

export const fetchTeamForm = async (teamId: number): Promise<number> => {
  try {
    const response = await axios.get(`${API_URL}/team/${teamId}/form`)
    return response.data.form
  } catch (error) {
    console.error(`Fehler beim Abrufen der Form für Team ${teamId}:`, error)
    throw error
  }
}

export const fetchTeamMatches = async (teamId: number): Promise<MatchResult[]> => {
  try {
    const response = await axios.get(`${API_URL}/team/${teamId}/matches`)
    return response.data
  } catch (error) {
    console.error(`Fehler beim Abrufen der letzten Spiele für Team ${teamId}:`, error)
    throw error
  }
}

// Custom Hooks
export const useNextMatchday = () => {
  const [data, setData] = useState<Match[] | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getNextMatchday = async () => {
      try {
        setLoading(true)
        const matchData = await fetchNextMatchday()
        setData(matchData)
        setError(null)
      } catch (err) {
        setError('Fehler beim Laden der Spieldaten.')
      } finally {
        setLoading(false)
      }
    }

    getNextMatchday()
  }, [])

  return { data, loading, error }
}

export const usePredictions = (matchday: number) => {
  const [data, setData] = useState<Prediction[] | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getPredictions = async () => {
      try {
        setLoading(true)
        const predictionData = await fetchPredictions(matchday)
        setData(predictionData)
        setError(null)
      } catch (err) {
        setError('Fehler beim Laden der Vorhersagen.')
      } finally {
        setLoading(false)
      }
    }

    getPredictions()
  }, [matchday])

  return { data, loading, error }
}

export const useTeamMatches = (teamId: number) => {
  const [data, setData] = useState<MatchResult[] | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getTeamMatches = async () => {
      if (!teamId) return
      
      try {
        setLoading(true)
        const matchData = await fetchTeamMatches(teamId)
        setData(matchData)
        setError(null)
      } catch (err) {
        setError('Fehler beim Laden der Team-Spiele.')
      } finally {
        setLoading(false)
      }
    }

    getTeamMatches()
  }, [teamId])

  return { data, loading, error }
}
