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

interface TableEntry {
  position: number;
  team: Team;
  matches_played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
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

const getApiBase = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  if (window.location.hostname.includes('onrender.com')) {
    return 'https://kick-predictor-backend.onrender.com';
  }
  return '/api';
}

const buildApiUrl = (endpoint: string): string => {
  const base = getApiBase();
  // Wenn base mit http beginnt, dann Endpunkt mit /api/... ergänzen
  if (base.startsWith('http')) {
    return `${base}/api${endpoint}`;
  }
  // Sonst (z.B. /api) einfach anhängen
  return `${base}${endpoint}`;
}

console.log('API Base configured as:', getApiBase());

export const fetchNextMatchday = async (): Promise<Match[]> => {
  try {
    const url = buildApiUrl('/next-matchday');
    console.log('Fetching next matchday from:', url);
    const response = await axios.get(url)
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
    const url = buildApiUrl(`/predictions/${matchday}`);
    console.log('Fetching predictions from:', url);
    const response = await axios.get(url)
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
    const url = buildApiUrl(`/team/${teamId}/form`);
    const response = await axios.get(url)
    return response.data.form
  } catch (error) {
    console.error(`Fehler beim Abrufen der Form für Team ${teamId}:`, error)
    throw error
  }
}

export const fetchTeamMatches = async (teamId: number): Promise<MatchResult[]> => {
  try {
    const url = buildApiUrl(`/team/${teamId}/matches`);
    const response = await axios.get(url)
    return response.data
  } catch (error) {
    console.error(`Fehler beim Abrufen der letzten Spiele für Team ${teamId}:`, error)
    throw error
  }
}

export const fetchCurrentTable = async (): Promise<TableEntry[]> => {
  try {
    const url = buildApiUrl('/table');
    console.log('Fetching table from:', url);
    const response = await axios.get(url)
    console.log('Table response:', response.data);
    return response.data
  } catch (error) {
    console.error('Fehler beim Abrufen der Tabelle:', error)
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

export const useCurrentTable = () => {
  const [data, setData] = useState<TableEntry[] | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getCurrentTable = async () => {
      try {
        setLoading(true)
        const tableData = await fetchCurrentTable()
        setData(tableData)
        setError(null)
      } catch (err) {
        setError('Fehler beim Laden der Tabelle.')
      } finally {
        setLoading(false)
      }
    }

    getCurrentTable()
  }, [])

  return { data, loading, error }
}
