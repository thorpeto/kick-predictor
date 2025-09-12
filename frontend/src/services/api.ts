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
  // Zuerst prüfen, ob eine explizite API-URL gesetzt ist
  if (import.meta.env.VITE_API_URL) {
    console.log('Using VITE_API_URL:', import.meta.env.VITE_API_URL);
    return import.meta.env.VITE_API_URL;
  }
  
  // Für lokale Entwicklung
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('Using local development API URL');
    return 'http://localhost:8000';  // Direkte Verbindung zum Backend
  }
  
  // Für Render.com Deployment
  if (window.location.hostname.includes('onrender.com')) {
    const backendUrl = 'https://kick-predictor-backend.onrender.com';
    console.log('Using Render.com backend URL:', backendUrl);
    return backendUrl;
  }
  
  // Für GCP Deployment - anpassen je nach Setup
  if (window.location.hostname.includes('appspot.com') || 
      window.location.hostname.includes('run.app')) {
    console.log('Using GCP deployment with relative URL');
    return '/api';
  }
  
  // Fallback - versuche relative URL
  console.log('Using fallback relative URL');
  return '/api';
}

const API_URL = getApiUrl();

// Debug-Information für die Entwicklung
console.log('API_URL configured as:', API_URL);

export const fetchNextMatchday = async (): Promise<Match[]> => {
  try {
    console.log('Fetching next matchday from:', `${API_URL}/next-matchday`);
    const response = await axios.get(`${API_URL}/next-matchday`)
    console.log('Next matchday response:', response.data);
    return response.data
  } catch (error) {
    console.error('Fehler beim Abrufen des nächsten Spieltags:', error)
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        url: error.config?.url
      });
    }
    throw error
  }
}

export const fetchPredictions = async (matchday: number): Promise<Prediction[]> => {
  try {
    console.log('Fetching predictions from:', `${API_URL}/predictions/${matchday}`);
    const response = await axios.get(`${API_URL}/predictions/${matchday}`)
    console.log('Predictions response:', response.data);
    return response.data
  } catch (error) {
    console.error(`Fehler beim Abrufen der Vorhersagen für Spieltag ${matchday}:`, error)
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        url: error.config?.url
      });
    }
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
