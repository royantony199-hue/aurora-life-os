import { useState } from 'react';
import { Settings, Bell, Calendar, Shield, HelpCircle, LogOut, Moon, Sun, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export function UltimateProfileSettings() {
  const { user, logout } = useAuth();
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState({
    dailyCheckins: true,
    goalReminders: true,
    moodInsights: false,
    weeklyReports: true
  });

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
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Profile Header Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">👤</div>
          <div>
            <div className="card-title">Profile</div>
            <div className="card-subtitle">Manage your account</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
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
              color: '#1a202c' 
            }}>
              {user?.username || 'Aurora User'}
            </h2>
            <p style={{ 
              margin: '0 0 8px 0', 
              fontSize: '14px', 
              color: '#718096' 
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

        <button className="ultimate-btn-secondary">
          <User size={16} style={{ marginRight: '8px' }} />
          Edit Profile
        </button>
      </div>

      {/* Stats Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">📊</div>
          <div>
            <div className="card-title">Your Progress</div>
            <div className="card-subtitle">Activity overview</div>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-value">{userStats.daysActive}</div>
            <div className="stat-label">Days Active</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{userStats.goalsCompleted}</div>
            <div className="stat-label">Goals Done</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{userStats.avgMood}</div>
            <div className="stat-label">Avg Mood</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{userStats.streakDays}</div>
            <div className="stat-label">Day Streak</div>
          </div>
        </div>
      </div>

      {/* Settings Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">⚙️</div>
          <div>
            <div className="card-title">App Settings</div>
            <div className="card-subtitle">Customize your experience</div>
          </div>
        </div>

        {/* Dark Mode Toggle */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px',
          background: 'rgba(102, 126, 234, 0.05)',
          borderRadius: '12px',
          marginBottom: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {darkMode ? <Moon size={20} color="#667eea" /> : <Sun size={20} color="#FAAD14" />}
            <div>
              <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>
                Dark Mode
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: '#718096' }}>
                Switch to dark theme
              </p>
            </div>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            style={{
              width: '48px',
              height: '28px',
              background: darkMode ? '#667eea' : '#E5E7EB',
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

      {/* Notifications Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">🔔</div>
          <div>
            <div className="card-title">Notifications</div>
            <div className="card-subtitle">Manage your alerts</div>
          </div>
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
                  background: value ? 'rgba(102, 126, 234, 0.05)' : 'rgba(113, 128, 150, 0.05)',
                  borderRadius: '12px',
                  border: `1px solid ${value ? 'rgba(102, 126, 234, 0.1)' : 'rgba(113, 128, 150, 0.1)'}`
                }}
              >
                <div>
                  <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>
                    {label.title}
                  </p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#718096' }}>
                    {label.desc}
                  </p>
                </div>
                <button
                  onClick={() => toggleNotification(key as keyof typeof notifications)}
                  style={{
                    width: '44px',
                    height: '24px',
                    background: value ? '#667eea' : '#E5E7EB',
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

      {/* Menu Items Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">📱</div>
          <div>
            <div className="card-title">More Options</div>
            <div className="card-subtitle">Additional settings</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[
            { icon: Calendar, label: 'Calendar Integration', desc: 'Google Calendar connected', color: '#52C41A' },
            { icon: Shield, label: 'Privacy & Security', desc: 'Manage your data and privacy', color: '#667eea' },
            { icon: HelpCircle, label: 'Help & Support', desc: 'Get help and contact support', color: '#FAAD14' }
          ].map((item, index) => (
            <button
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px',
                background: 'none',
                border: '1px solid rgba(102, 126, 234, 0.1)',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
              onClick={() => {/* Handle ${item.label} action */}}
            >
              <div style={{
                width: '40px',
                height: '40px',
                background: `${item.color}15`,
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <item.icon size={20} color={item.color} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>
                  {item.label}
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: '#718096' }}>
                  {item.desc}
                </p>
              </div>
              <div style={{ fontSize: '16px', color: '#718096' }}>→</div>
            </button>
          ))}
        </div>
      </div>

      {/* Aurora AI Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">🤖</div>
          <div>
            <div className="card-title">Aurora AI Preferences</div>
            <div className="card-subtitle">Customize your AI companion</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{
            background: 'rgba(102, 126, 234, 0.05)',
            border: '1px solid rgba(102, 126, 234, 0.1)',
            borderRadius: '12px',
            padding: '16px'
          }}>
            <p style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>
              Coaching Style
            </p>
            <p style={{ margin: 0, fontSize: '12px', color: '#718096' }}>
              Supportive and encouraging
            </p>
          </div>
          <div style={{
            background: 'rgba(102, 126, 234, 0.05)',
            border: '1px solid rgba(102, 126, 234, 0.1)',
            borderRadius: '12px',
            padding: '16px'
          }}>
            <p style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>
              Check-in Frequency
            </p>
            <p style={{ margin: 0, fontSize: '12px', color: '#718096' }}>
              Daily at 9:00 AM
            </p>
          </div>
        </div>

        <button className="ultimate-btn-secondary" style={{ marginTop: '16px' }}>
          <Settings size={16} style={{ marginRight: '8px' }} />
          Customize Aurora
        </button>
      </div>

      {/* Sign Out Card */}
      <div className="ultimate-card">
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
          <LogOut size={20} />
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
  );
}