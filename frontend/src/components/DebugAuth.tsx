import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function DebugAuth() {
  const { user, isLoading, isAuthenticated, error } = useAuth();
  const [apiStatus, setApiStatus] = useState<any>({});
  
  useEffect(() => {
    checkAPIStatus();
  }, []);
  
  const checkAPIStatus = async () => {
    try {
      const token = localStorage.getItem('aurora_access_token');
      
      // Check health
      const healthResponse = await fetch('http://localhost:8001/health');
      const healthData = await healthResponse.json();
      
      // Check auth status
      let authStatus = 'No token';
      if (token) {
        const meResponse = await fetch('http://localhost:8001/api/users/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        authStatus = meResponse.ok ? 'Valid' : `Invalid (${meResponse.status})`;
      }
      
      setApiStatus({
        health: healthData,
        authStatus,
        token: token ? token.substring(0, 20) + '...' : 'None'
      });
    } catch (error) {
      setApiStatus({ error: error.toString() });
    }
  };
  
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f0f0f0', 
      borderRadius: '8px',
      margin: '20px',
      fontFamily: 'monospace'
    }}>
      <h2>🔍 Debug Information</h2>
      
      <h3>Auth Context:</h3>
      <pre>{JSON.stringify({
        isLoading,
        isAuthenticated,
        user,
        error
      }, null, 2)}</pre>
      
      <h3>Local Storage:</h3>
      <pre>{JSON.stringify({
        access_token: localStorage.getItem('aurora_access_token')?.substring(0, 20) + '...',
        refresh_token: localStorage.getItem('aurora_refresh_token')?.substring(0, 20) + '...'
      }, null, 2)}</pre>
      
      <h3>API Status:</h3>
      <pre>{JSON.stringify(apiStatus, null, 2)}</pre>
      
      <button 
        onClick={() => window.location.reload()}
        style={{
          padding: '10px 20px',
          backgroundColor: '#4A90E2',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          marginTop: '10px'
        }}
      >
        Refresh Page
      </button>
      
      <button 
        onClick={() => {
          localStorage.clear();
          window.location.reload();
        }}
        style={{
          padding: '10px 20px',
          backgroundColor: '#ff6b6b',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          marginTop: '10px',
          marginLeft: '10px'
        }}
      >
        Clear Storage & Reload
      </button>
    </div>
  );
}