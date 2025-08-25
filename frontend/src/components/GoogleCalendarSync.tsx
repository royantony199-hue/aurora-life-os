import React, { useState, useEffect } from 'react';
import { calendarAPI, aiCalendarAPI } from '../services/api';

interface GoogleCalendarSyncProps {
  onSync?: () => void;
}

export function GoogleCalendarSync({ onSync }: GoogleCalendarSyncProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('');

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const response = await calendarAPI.getConnectionStatus();
      setIsConnected(response.google_calendar_connected);
      setConnectionStatus(response.message || '');
    } catch (error) {
      console.error('Error checking Google Calendar connection:', error);
      setIsConnected(false);
    }
  };

  const connectToGoogle = async () => {
    setIsConnecting(true);
    try {
      const response = await calendarAPI.connectGoogle();
      if (response.auth_url) {
        // Open Google OAuth in new window
        window.open(response.auth_url, 'google-auth', 'width=500,height=600');
        
        // Poll for connection status
        const checkAuth = setInterval(async () => {
          const status = await calendarAPI.getConnectionStatus();
          if (status.google_calendar_connected) {
            setIsConnected(true);
            setConnectionStatus('Connected successfully!');
            clearInterval(checkAuth);
            setIsConnecting(false);
          }
        }, 2000);
        
        // Stop polling after 60 seconds
        setTimeout(() => clearInterval(checkAuth), 60000);
      }
    } catch (error) {
      console.error('Error connecting to Google Calendar:', error);
      setIsConnecting(false);
    }
  };

  const syncCalendar = async () => {
    setIsSyncing(true);
    try {
      await calendarAPI.syncWithGoogle();
      setConnectionStatus('Sync completed successfully!');
      if (onSync) {
        onSync();
      }
    } catch (error) {
      console.error('Error syncing calendar:', error);
      setConnectionStatus('Sync failed. Please try again.');
    } finally {
      setIsSyncing(false);
    }
  };

  const generateAISchedule = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      await aiCalendarAPI.generateSchedule(today);
      setConnectionStatus('AI schedule generated!');
      if (onSync) {
        onSync();
      }
    } catch (error) {
      console.error('Error generating AI schedule:', error);
      setConnectionStatus('AI schedule generation failed.');
    }
  };

  return (
    <div className="mobile-card">
      <div className="flex items-center gap-3 mb-4">
        <div className="mobile-card-icon">
          <span style={{ fontSize: '18px' }}>📅</span>
        </div>
        <div>
          <h3 className="mobile-card-title">Google Calendar</h3>
          <p className="text-xs text-gray-500">Sync and AI optimization</p>
        </div>
      </div>

      <div className="space-y-3">
        {/* Connection Status */}
        <div className={`p-3 rounded-lg ${isConnected ? 'bg-green-100' : 'bg-yellow-100'}`}>
          <div className="flex items-center gap-2">
            <span className="text-lg">{isConnected ? '✅' : '⚠️'}</span>
            <div>
              <p className="text-sm font-medium">
                {isConnected ? 'Connected' : 'Not Connected'}
              </p>
              {connectionStatus && (
                <p className="text-xs text-gray-600">{connectionStatus}</p>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          {!isConnected ? (
            <button
              onClick={connectToGoogle}
              disabled={isConnecting}
              className="mobile-button"
            >
              {isConnecting ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Connecting...
                </>
              ) : (
                <>
                  🔗 Connect Google Calendar
                </>
              )}
            </button>
          ) : (
            <>
              <button
                onClick={syncCalendar}
                disabled={isSyncing}
                className="mobile-button"
              >
                {isSyncing ? (
                  <>
                    <span className="animate-spin mr-2">⏳</span>
                    Syncing...
                  </>
                ) : (
                  <>
                    🔄 Sync Calendar
                  </>
                )}
              </button>
              
              <button
                onClick={generateAISchedule}
                className="mobile-button"
                style={{ background: 'linear-gradient(135deg, #722ED1 0%, #4A90E2 100%)' }}
              >
                🤖 Generate AI Schedule
              </button>
            </>
          )}
        </div>

        {/* Feature List */}
        {isConnected && (
          <div className="bg-blue-50 p-3 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">✨ Available Features:</h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Two-way calendar synchronization</li>
              <li>• AI-powered schedule optimization</li>
              <li>• Goal-based time allocation</li>
              <li>• Meeting link auto-extraction</li>
              <li>• Energy pattern analysis</li>
              <li>• Productivity insights</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}