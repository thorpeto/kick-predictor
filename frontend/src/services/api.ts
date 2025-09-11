import { useEffect, useState } from 'react'
import axios from 'axios'

interface Match {
  id: number;
  home_team: {
    id: number;
    name: string;
    short_name: string;
  };
  away_team: {
    id: number;
    name: string;
    short_name: string;
  };
  date: string;
  matchday: number;
  season: string;
}

interface FormFactor {
  home_form: number;
  away_form: number;
  home_xg_last_6: number;
  away_xg_last_6: number;
  home_possession_avg: number;
  away_possession_avg: number;
}

interface Prediction {
  match: Match;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  predicted_score: string;
  form_factors: FormFactor;
}

// API Service
const API_URL = '/api'

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
