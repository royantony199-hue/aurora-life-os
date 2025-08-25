import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function SimpleProfileSettings() {
  const { user, logout } = useAuth();
  const [darkMode, setDarkMode] = useState(false);
  const [calendarConnected, setCalendarConnected] = useState(false);
  const [checkingConnection, setCheckingConnection] = useState(false);
  const [notifications, setNotifications] = useState({
    dailyCheckins: true,
    goalReminders: true,
    moodInsights: false,
    weeklyReports: true
  });

  useEffect(() => {
    checkCalendarConnection();
  }, []);

  const checkCalendarConnection = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/calendar/connection-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setCalendarConnected(data.google_calendar_connected || false);
      }
    } catch (error) {
      console.error('Failed to check calendar connection:', error);
      setCalendarConnected(false);
    }
  };

  const handleCalendarConnect = async () => {
    try {
      setCheckingConnection(true);
      
      if (calendarConnected) {
        // Disconnect calendar
        const response = await fetch('http://localhost:8001/api/calendar/disconnect', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
          },
        });
        
        if (response.ok) {
          setCalendarConnected(false);
          alert('Google Calendar disconnected successfully!');
        } else {
          alert('Failed to disconnect calendar');
        }
      } else {
        // Connect calendar - get auth URL first then redirect
        const response = await fetch('http://localhost:8001/api/calendar/connect-google', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.auth_url) {
            window.location.href = data.auth_url;
          } else {
            alert('Failed to get Google OAuth URL');
          }
        } else {
          alert('Failed to connect to Google Calendar');
        }
      }
    } catch (error) {
      console.error('Calendar connection error:', error);
      alert('Failed to manage calendar connection');
    } finally {
      setCheckingConnection(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const userStats = {
    daysActive: 28,
    goalsCompleted: 3,
    avgMood: 7.2,
    streakDays: 12
  };

  const getUserInitials = (username: string) => {
    if (!username) return 'AU';
    return username.charAt(0).toUpperCase();
  };

  const toggleNotification = (key: keyof typeof notifications) => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div style={{ 
      height: '100%', 
      background: '#F5F7FA', 
      overflowY: 'auto',
      paddingBottom: '100px'
    }}>
      {/* Header */}
      <div style={{
        background: 'white',
        borderBottom: '1px solid #D9D9D9',
        padding: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '24px',
            fontWeight: '600',
            boxShadow: '0 4px 16px rgba(102, 126, 234, 0.4)'
          }}>
            {getUserInitials(user?.username || '')}
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ 
              margin: '0 0 4px 0', 
              fontSize: '20px', 
              fontWeight: '600', 
              color: '#262626' 
            }}>
              {user?.username || 'Aurora User'}
            </h2>
            <p style={{ 
              margin: '0 0 8px 0', 
              fontSize: '14px', 
              color: '#8C8C8C' 
            }}>
              {user?.email || 'demo@aurora.com'}
            </p>
            <div style={{
              background: 'rgba(82, 196, 26, 0.1)',
              color: '#52C41A',
              fontSize: '12px',
              fontWeight: '500',
              padding: '4px 8px',
              borderRadius: '8px',
              display: 'inline-block'
            }}>
              Demo Mode
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '16px' }}>
        {/* Stats Card */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>📊</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              Your Progress
            </h2>
          </div>

          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '16px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#4A90E2', margin: '0 0 4px 0' }}>
                {userStats.daysActive}
              </div>
              <div style={{ fontSize: '14px', color: '#8C8C8C' }}>Days Active</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#52C41A', margin: '0 0 4px 0' }}>
                {userStats.goalsCompleted}
              </div>
              <div style={{ fontSize: '14px', color: '#8C8C8C' }}>Goals Done</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#FAAD14', margin: '0 0 4px 0' }}>
                {userStats.avgMood}
              </div>
              <div style={{ fontSize: '14px', color: '#8C8C8C' }}>Avg Mood</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#722ED1', margin: '0 0 4px 0' }}>
                {userStats.streakDays}
              </div>
              <div style={{ fontSize: '14px', color: '#8C8C8C' }}>Day Streak</div>
            </div>
          </div>
        </div>

        {/* App Settings */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>⚙️</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              App Settings
            </h2>
          </div>

          {/* Dark Mode Toggle */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px',
            background: 'rgba(102, 126, 234, 0.05)',
            borderRadius: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '20px' }}>{darkMode ? '🌙' : '☀️'}</span>
              <div>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                  Dark Mode
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: '#8C8C8C' }}>
                  Switch to dark theme
                </p>
              </div>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              style={{
                width: '48px',
                height: '28px',
                background: darkMode ? '#4A90E2' : '#E5E7EB',
                borderRadius: '14px',
                border: 'none',
                cursor: 'pointer',
                position: 'relative',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{
                width: '20px',
                height: '20px',
                background: 'white',
                borderRadius: '10px',
                position: 'absolute',
                top: '4px',
                left: darkMode ? '24px' : '4px',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
              }} />
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>🔔</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              Notifications
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {Object.entries(notifications).map(([key, value]) => {
              const labels = {
                dailyCheckins: { title: 'Daily Check-ins', desc: 'Remind me to log my mood daily' },
                goalReminders: { title: 'Goal Reminders', desc: 'Notify about upcoming deadlines' },
                moodInsights: { title: 'Mood Insights', desc: 'Weekly mood pattern insights' },
                weeklyReports: { title: 'Weekly Reports', desc: 'Summary of achievements and progress' }
              };
              
              const label = labels[key as keyof typeof labels];
              
              return (
                <div
                  key={key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px',
                    background: value ? 'rgba(74, 144, 226, 0.05)' : 'rgba(229, 231, 235, 0.5)',
                    borderRadius: '12px',
                    border: `1px solid ${value ? 'rgba(74, 144, 226, 0.1)' : 'rgba(229, 231, 235, 0.5)'}`
                  }}
                >
                  <div>
                    <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                      {label.title}
                    </p>
                    <p style={{ margin: 0, fontSize: '12px', color: '#8C8C8C' }}>
                      {label.desc}
                    </p>
                  </div>
                  <button
                    onClick={() => toggleNotification(key as keyof typeof notifications)}
                    style={{
                      width: '44px',
                      height: '24px',
                      background: value ? '#4A90E2' : '#E5E7EB',
                      borderRadius: '12px',
                      border: 'none',
                      cursor: 'pointer',
                      position: 'relative',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{
                      width: '16px',
                      height: '16px',
                      background: 'white',
                      borderRadius: '8px',
                      position: 'absolute',
                      top: '4px',
                      left: value ? '24px' : '4px',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
                    }} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Menu Items */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>📱</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              More Options
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Calendar Integration - Functional */}
            <button
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px',
                background: 'none',
                border: calendarConnected ? '1px solid rgba(82, 196, 26, 0.3)' : '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '12px',
                cursor: checkingConnection ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left',
                opacity: checkingConnection ? 0.7 : 1
              }}
              onClick={handleCalendarConnect}
              disabled={checkingConnection}
            >
              <div style={{
                width: '40px',
                height: '40px',
                background: calendarConnected ? 'rgba(82, 196, 26, 0.15)' : 'rgba(140, 140, 140, 0.15)',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px'
              }}>
                📅
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                  Calendar Integration
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: calendarConnected ? '#52C41A' : '#8C8C8C' }}>
                  {checkingConnection ? 'Processing...' : 
                   calendarConnected ? 'Google Calendar connected' : 'Connect Google Calendar'}
                </p>
              </div>
              <div style={{ 
                fontSize: '16px', 
                color: calendarConnected ? '#52C41A' : '#8C8C8C',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {calendarConnected ? '✓' : '→'}
              </div>
            </button>

            {/* Privacy & Security */}
            <button
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px',
                background: 'none',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
              onClick={() => alert('Privacy & Security settings coming soon!')}
            >
              <div style={{
                width: '40px',
                height: '40px',
                background: 'rgba(74, 144, 226, 0.15)',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px'
              }}>
                🛡️
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                  Privacy & Security
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: '#8C8C8C' }}>
                  Manage your data and privacy
                </p>
              </div>
              <div style={{ fontSize: '16px', color: '#8C8C8C' }}>→</div>
            </button>

            {/* Help & Support */}
            <button
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px',
                background: 'none',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
              onClick={() => alert('Help & Support: Contact us at support@aurora.ai or check our documentation at docs.aurora.ai')}
            >
              <div style={{
                width: '40px',
                height: '40px',
                background: 'rgba(250, 173, 20, 0.15)',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px'
              }}>
                ❓
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                  Help & Support
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: '#8C8C8C' }}>
                  Get help and contact support
                </p>
              </div>
              <div style={{ fontSize: '16px', color: '#8C8C8C' }}>→</div>
            </button>
          </div>
        </div>

        {/* Aurora AI Card */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(114, 46, 209, 0.1) 100%)',
          border: '1px solid rgba(102, 126, 234, 0.2)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>🤖</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              Aurora AI Preferences
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.5)',
              border: '1px solid rgba(102, 126, 234, 0.1)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <p style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                Coaching Style
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: '#8C8C8C' }}>
                Supportive and encouraging
              </p>
            </div>
            <div style={{
              background: 'rgba(255, 255, 255, 0.5)',
              border: '1px solid rgba(102, 126, 234, 0.1)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <p style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '500', color: '#262626' }}>
                Check-in Frequency
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: '#8C8C8C' }}>
                Daily at 9:00 AM
              </p>
            </div>
          </div>

          <button 
            onClick={() => alert('Aurora AI Customization:\n\n🤖 Coaching Style: Supportive and encouraging\n⏰ Check-in Frequency: Daily at 9:00 AM\n🎯 Focus Areas: Goal achievement and productivity\n💪 Motivation Level: High energy, action-oriented\n\nCustomization options coming soon!')}
            style={{
              width: '100%',
              marginTop: '16px',
              padding: '12px',
              background: 'rgba(74, 144, 226, 0.1)',
              color: '#4A90E2',
              border: '1px solid rgba(74, 144, 226, 0.2)',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            ⚙️ Customize Aurora
          </button>
        </div>

        {/* Sign Out */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px',
              background: 'rgba(255, 77, 79, 0.05)',
              border: '1px solid rgba(255, 77, 79, 0.2)',
              borderRadius: '12px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              color: '#FF4D4F'
            }}
          >
            <span style={{ fontSize: '20px' }}>🚪</span>
            <div style={{ textAlign: 'left' }}>
              <p style={{ margin: 0, fontSize: '14px', fontWeight: '500' }}>
                Sign Out
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: '#FF4D4F', opacity: 0.7 }}>
                Sign out of your account
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}