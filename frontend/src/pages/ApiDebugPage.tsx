import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ApiDebugPage: React.FC = () => {
  const [apiUrl, setApiUrl] = useState('');
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [testStatus, setTestStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    // Bestimme die API-URL (kopiert aus api.ts)
    const getApiUrl = (): string => {
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
    };

    setApiUrl(getApiUrl());
  }, []);

  const testConnection = async (endpoint: string, label: string) => {
    setLoading(true);
    setErrors([]);
    
    try {
      console.log(`Testing ${label}: ${apiUrl}${endpoint}`);
      const response = await axios.get(`${apiUrl}${endpoint}`, {
        timeout: 30000, // 30 Sekunden Timeout
      });
      
      if (endpoint === '/health') {
        setHealthStatus({
          status: 'success',
          data: response.data,
          timestamp: new Date().toISOString()
        });
      } else {
        setTestStatus({
          status: 'success',
          data: response.data,
          timestamp: new Date().toISOString()
        });
      }
      
      console.log(`${label} Response:`, response.data);
    } catch (error: any) {
      const errorInfo = {
        status: 'error',
        message: error.message,
        timestamp: new Date().toISOString(),
        details: {}
      };

      if (axios.isAxiosError(error)) {
        errorInfo.details = {
          status: error.response?.status,
          statusText: error.response?.statusText,
          url: error.config?.url,
          timeout: error.code === 'ECONNABORTED'
        };
      }

      if (endpoint === '/health') {
        setHealthStatus(errorInfo);
      } else {
        setTestStatus(errorInfo);
      }

      setErrors(prev => [...prev, `${label}: ${error.message}`]);
      console.error(`${label} Error:`, error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">API Debug Tool</h1>
      
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Konfiguration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <strong>API URL:</strong> {apiUrl}
          </div>
          <div>
            <strong>Frontend URL:</strong> {window.location.origin}
          </div>
          <div>
            <strong>Environment:</strong> {import.meta.env.MODE}
          </div>
          <div>
            <strong>VITE_API_URL:</strong> {import.meta.env.VITE_API_URL || 'nicht gesetzt'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Health Check</h2>
          <button 
            onClick={() => testConnection('/health', 'Health Check')}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Test Health Check'}
          </button>
          
          {healthStatus && (
            <div className={`mt-4 p-4 rounded ${healthStatus.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              <strong>Status:</strong> {healthStatus.status}<br/>
              <strong>Zeit:</strong> {healthStatus.timestamp}<br/>
              {healthStatus.data && (
                <>
                  <strong>Response:</strong>
                  <pre className="mt-2 text-sm">{JSON.stringify(healthStatus.data, null, 2)}</pre>
                </>
              )}
              {healthStatus.details && (
                <>
                  <strong>Details:</strong>
                  <pre className="mt-2 text-sm">{JSON.stringify(healthStatus.details, null, 2)}</pre>
                </>
              )}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">API Test</h2>
          <button 
            onClick={() => testConnection('/api/test', 'API Test')}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Test API Endpoint'}
          </button>
          
          {testStatus && (
            <div className={`mt-4 p-4 rounded ${testStatus.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              <strong>Status:</strong> {testStatus.status}<br/>
              <strong>Zeit:</strong> {testStatus.timestamp}<br/>
              {testStatus.data && (
                <>
                  <strong>Response:</strong>
                  <pre className="mt-2 text-sm">{JSON.stringify(testStatus.data, null, 2)}</pre>
                </>
              )}
              {testStatus.details && (
                <>
                  <strong>Details:</strong>
                  <pre className="mt-2 text-sm">{JSON.stringify(testStatus.details, null, 2)}</pre>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {errors.length > 0 && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Fehler:</strong>
          <ul className="mt-2">
            {errors.map((error, index) => (
              <li key={index} className="list-disc list-inside">{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-gray-100 rounded-lg p-6 mt-6">
        <h2 className="text-xl font-semibold mb-4">Debugging-Hinweise</h2>
        <ul className="space-y-2 text-sm">
          <li>• Öffnen Sie die Browser-Konsole (F12) für detaillierte Logs</li>
          <li>• Health Check sollte {`{"status": "online"}`} zurückgeben</li>
          <li>• API Test sollte eine Erfolgs-Nachricht zurückgeben</li>
          <li>• Bei CORS-Fehlern: Backend-Konfiguration prüfen</li>
          <li>• Bei Timeout: Backend möglicherweise nicht erreichbar (Free Tier Spin-Down)</li>
          <li>• Bei 404: Falscher API-URL oder Backend nicht deployed</li>
        </ul>
      </div>
    </div>
  );
};

export default ApiDebugPage;