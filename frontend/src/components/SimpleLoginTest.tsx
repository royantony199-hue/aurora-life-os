import React, { useState } from 'react';

export function SimpleLoginTest() {
  const [result, setResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const testDirectLogin = async () => {
    setIsLoading(true);
    setResult('Testing login...');
    
    try {
      const response = await fetch('http://localhost:8001/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: 'testuser',
          password: 'password123'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('aurora_access_token', data.access_token);
        localStorage.setItem('aurora_refresh_token', data.refresh_token);
        setResult('✅ Login successful! Tokens saved. Refreshing page...');
        
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        const errorData = await response.text();
        setResult(`❌ Login failed: ${response.status} - ${errorData}`);
      }
    } catch (error) {
      setResult(`❌ Network error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const clearTokens = () => {
    localStorage.clear();
    setResult('🗑️ Tokens cleared');
  };

  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#f9f9f9',
      borderRadius: '8px',
      margin: '20px',
      textAlign: 'center'
    }}>
      <h3>🔧 Login Test Tool</h3>
      <p>If normal login isn't working, try this direct method:</p>
      
      <button
        onClick={testDirectLogin}
        disabled={isLoading}
        style={{
          padding: '12px 24px',
          backgroundColor: '#4A90E2',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          fontSize: '14px',
          margin: '10px'
        }}
      >
        {isLoading ? '⏳ Testing...' : '🔐 Direct Login Test'}
      </button>
      
      <button
        onClick={clearTokens}
        style={{
          padding: '12px 24px',
          backgroundColor: '#ff6b6b',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px',
          margin: '10px'
        }}
      >
        🗑️ Clear Tokens
      </button>

      {result && (
        <div style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: result.includes('✅') ? '#d4edda' : '#f8d7da',
          color: result.includes('✅') ? '#155724' : '#721c24',
          borderRadius: '4px',
          whiteSpace: 'pre-wrap'
        }}>
          {result}
        </div>
      )}
      
      <hr style={{ margin: '20px 0' }} />
      
      <div style={{ fontSize: '12px', color: '#666', textAlign: 'left' }}>
        <strong>Debug Info:</strong><br/>
        API URL: http://localhost:8001<br/>
        Frontend URL: {window.location.origin}<br/>
        Stored Token: {localStorage.getItem('aurora_access_token') ? 'Yes' : 'No'}<br/>
        Current Time: {new Date().toISOString()}
      </div>
    </div>
  );
}