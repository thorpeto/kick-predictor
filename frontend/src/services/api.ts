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
  home_goals_last_14: number;
  away_goals_last_14: number;
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

interface MatchdayInfo {
  current_matchday: number;
  next_matchday: number;
  predictions_available_until: number;
  season: string;
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
  // 1. Explizit gesetzte VITE_API_URL hat höchste Priorität
  if (import.meta.env.VITE_API_URL) {
    console.log('Using VITE_API_URL:', import.meta.env.VITE_API_URL);
    return import.meta.env.VITE_API_URL;
  }
  
  // 2. Lokale Entwicklung
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('Using localhost backend');
    return 'http://localhost:8000';
  }
  
  // 3. Google Cloud Run deployment
  if (window.location.hostname.includes('run.app')) {
    console.log('Using Google Cloud Run backend URL');
    return 'https://kick-predictor-backend-nbdweu6ika-ew.a.run.app';
  }
  
  // 4. Render.com Deployment - direkte Backend-URL verwenden
  if (window.location.hostname.includes('onrender.com')) {
    console.log('Using Render backend URL');
    return 'https://kick-predictor-backend.onrender.com';
  }
  
  // 5. Fallback für nginx-Proxy (Docker Compose)
  console.log('Using nginx proxy');
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

export { buildApiUrl };

// Configure axios defaults for better Render.com compatibility
axios.defaults.timeout = 30000; // 30 seconds
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add request interceptor for debugging
axios.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
axios.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error(`API Error: ${error.response.status} ${error.response.statusText} - ${error.config?.url}`);
    } else if (error.request) {
      console.error('API Network Error:', error.message, '- URL:', error.config?.url);
    } else {
      console.error('API Setup Error:', error.message);
    }
    return Promise.reject(error);
  }
);

console.log('API Base configured as:', getApiBase());

export const fetchNextMatchday = async (): Promise<Match[]> => {
  try {
    const url = buildApiUrl('/next-matchday');
    console.log('Fetching next matchday from:', url);
    const response = await axios.get(url)
    console.log('Next matchday response:', response.data);
    
    // Backend gibt jetzt { matchday, season, matches } zurück
    if (response.data && response.data.matches) {
      return response.data.matches;
    }
    
    return [];
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

export const fetchUpcomingMatches = async (): Promise<{ matches: Match[], matchday: number }> => {
  try {
    const url = buildApiUrl('/next-matchday');
    console.log('Fetching upcoming matches from:', url);
    const response = await axios.get(url)
    console.log('Next matchday response:', response.data);
    
    // Backend gibt jetzt das erwartete Format zurück: { matchday, season, matches }
    if (response.data && response.data.matches) {
      return {
        matches: response.data.matches,
        matchday: response.data.matchday || 1
      };
    }
    
    // Fallback falls keine Matches
    console.log('No matches found in response, returning empty');
    return { matches: [], matchday: response.data.matchday || 1 };
  } catch (error) {
    console.error('Fehler beim Abrufen der kommenden Spiele:', error);
    return { matches: [], matchday: 1 };
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
    return response.data.details.form_percentage
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
    
    // Backend liefert andere Struktur - mappen wir sie
    return response.data.map((item: any, index: number) => ({
      position: item.position || index + 1,
      team: {
        id: item.team_id || 0,
        name: item.team_name || 'Unknown',
        short_name: item.shortname || 'UNK',
        logo_url: item.team_icon_url
      },
      matches_played: item.games || 0,
      wins: item.wins || 0,
      draws: item.draws || 0,
      losses: item.losses || 0,
      goals_for: item.goals_for || 0,
      goals_against: item.goals_against || 0,
      goal_difference: item.goal_difference || 0,
      points: item.points || 0
    }));
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

export const fetchMatchdayInfo = async (): Promise<MatchdayInfo> => {
  try {
    const url = buildApiUrl('/matchday-info');
    console.log('Fetching matchday info from:', url);
    const response = await axios.get(url)
    console.log('Matchday info response:', response.data);
    
    // Fallback wenn Backend andere Struktur liefert
    if (Array.isArray(response.data) && response.data.length > 0) {
      const firstMatchday = response.data[0];
      return {
        current_matchday: firstMatchday.matchday || 1,
        next_matchday: firstMatchday.matchday ? firstMatchday.matchday + 1 : 2,
        predictions_available_until: firstMatchday.matchday || 1,
        season: firstMatchday.season || "2025"
      };
    }
    
    return response.data
  } catch (error) {
    console.error('Fehler beim Abrufen der Spieltag-Informationen:', error)
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

export const useMatchdayInfo = () => {
  const [data, setData] = useState<MatchdayInfo | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getMatchdayInfo = async () => {
      try {
        setLoading(true)
        const info = await fetchMatchdayInfo()
        setData(info)
        setError(null)
      } catch (err) {
        setError('Fehler beim Laden der Spieltag-Informationen.')
      } finally {
        setLoading(false)
      }
    }

    getMatchdayInfo()
  }, [])

  return { data, loading, error }
}

export const useUpcomingMatches = () => {
  const [data, setData] = useState<{ matches: Match[], matchday: number } | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getUpcomingMatches = async () => {
      try {
        setLoading(true)
        const result = await fetchUpcomingMatches()
        setData(result)
        setError(null)
      } catch (err) {
        setError('Fehler beim Laden der kommenden Spiele.')
      } finally {
        setLoading(false)
      }
    }

    getUpcomingMatches()
  }, [])

  return { data, loading, error }
}
