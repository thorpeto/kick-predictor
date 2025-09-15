import React, { useState, useEffect } from 'react';
import { buildApiUrl } from '../services/api';
import axios from 'axios';

interface DebugInfo {
  hostname: string;
  location: string;
  viteApiUrl: string;
  computedApiBase: string;
  backendHealth: string;
  backendError?: string;
}

const DebugPage: React.FC = () => {
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const gatherDebugInfo = async () => {
      const info: DebugInfo = {
        hostname: window.location.hostname,
        location: window.location.href,
        viteApiUrl: import.meta.env.VITE_API_URL || 'undefined',
        computedApiBase: getApiBase(),
        backendHealth: 'checking...'
      };

      try {
        const healthUrl = buildApiUrl('/health');
        console.log('Testing health endpoint:', healthUrl);
        const response = await axios.get(healthUrl, { timeout: 10000 });
        info.backendHealth = JSON.stringify(response.data);
      } catch (error) {
        console.error('Health check failed:', error);
        if (axios.isAxiosError(error)) {
          info.backendError = `${error.message} (${error.response?.status || 'no response'})`;
        } else {
          info.backendError = String(error);
        }
        info.backendHealth = 'failed';
      }

      setDebugInfo(info);
      setLoading(false);
    };

    gatherDebugInfo();
  }, []);

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
  };

  const testEndpoints = async () => {
    const endpoints = ['/health', '/table', '/matchday-info'];
    
    for (const endpoint of endpoints) {
      try {
        const url = buildApiUrl(endpoint);
        console.log(`Testing ${endpoint}:`, url);
        const response = await axios.get(url, { timeout: 5000 });
        console.log(`✅ ${endpoint}:`, response.status, response.data);
      } catch (error) {
        console.error(`❌ ${endpoint}:`, error);
      }
    }
  };

  if (loading) {
    return <div className="p-8">Loading debug info...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Debug Information</h1>
      
      {debugInfo && (
        <div className="space-y-6">
          <div className="bg-gray-100 p-4 rounded">
            <h2 className="text-xl font-semibold mb-3">Environment Info</h2>
            <div className="space-y-2 font-mono text-sm">
              <div><strong>Hostname:</strong> {debugInfo.hostname}</div>
              <div><strong>Location:</strong> {debugInfo.location}</div>
              <div><strong>VITE_API_URL:</strong> {debugInfo.viteApiUrl}</div>
              <div><strong>Computed API Base:</strong> {debugInfo.computedApiBase}</div>
            </div>
          </div>

          <div className="bg-gray-100 p-4 rounded">
            <h2 className="text-xl font-semibold mb-3">Backend Health</h2>
            <div className="font-mono text-sm">
              <div><strong>Status:</strong> {debugInfo.backendHealth}</div>
              {debugInfo.backendError && (
                <div className="text-red-600 mt-2">
                  <strong>Error:</strong> {debugInfo.backendError}
                </div>
              )}
            </div>
          </div>

          <div className="bg-gray-100 p-4 rounded">
            <h2 className="text-xl font-semibold mb-3">Test URLs</h2>
            <div className="space-y-2 font-mono text-sm">
              <div><strong>Health:</strong> {buildApiUrl('/health')}</div>
              <div><strong>Table:</strong> {buildApiUrl('/table')}</div>
              <div><strong>Matchday Info:</strong> {buildApiUrl('/matchday-info')}</div>
            </div>
          </div>

          <button 
            onClick={testEndpoints}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Test All Endpoints (Check Console)
          </button>
        </div>
      )}
    </div>
  );
};

export default DebugPage;