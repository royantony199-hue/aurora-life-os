import { useState } from 'react';
import { UltimateChatInterface } from './UltimateChatInterface';
import { SimpleCalendarView } from './SimpleCalendarView';
import { SimpleGoalsDashboard } from './SimpleGoalsDashboard';
import { SimpleMoodTracker } from './SimpleMoodTracker';
import { SimpleProfileSettings } from './SimpleProfileSettings';
import { AuthPage } from './AuthPage';
import { ErrorBoundary } from './ErrorBoundary';
import { useAuth } from '../contexts/AuthContext';
import { DebugAuth } from './DebugAuth';

type TabType = 'chat' | 'calendar' | 'goals' | 'mood' | 'profile';

interface TabConfig {
  id: TabType;
  label: string;
  icon: string;
  component: React.ComponentType;
}

export function UltimateMobileApp() {
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [notificationCount, setNotificationCount] = useState(3);
  const { isLoading, isAuthenticated } = useAuth();

  const tabs: TabConfig[] = [
    { id: 'chat', label: 'Chat', icon: '💬', component: UltimateChatInterface },
    { id: 'calendar', label: 'Calendar', icon: '📅', component: SimpleCalendarView },
    { id: 'goals', label: 'Goals', icon: '🎯', component: SimpleGoalsDashboard },
    { id: 'mood', label: 'Mood', icon: '❤️', component: SimpleMoodTracker },
    { id: 'profile', label: 'Profile', icon: '👤', component: SimpleProfileSettings },
  ];

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div className="ultimate-app-container">
        <div className="app-gradient-bg" />
        <div className="ultimate-loading">
          <div className="aurora-logo">
            🌟
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: '600', margin: '16px 0 24px' }}>
            Aurora Life OS
          </h2>
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading your AI companion...</p>
        </div>
      </div>
    );
  }

  // Show authentication page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || UltimateChatInterface;
  const activeTabInfo = tabs.find(tab => tab.id === activeTab);

  const getTabDisplayName = (tab: TabType) => {
    const names = {
      chat: 'Aurora Chat',
      calendar: 'Calendar',
      goals: 'Goals',
      mood: 'Mood Tracker',
      profile: 'Profile'
    };
    return names[tab] || 'Aurora';
  };

  return (
    <div className="ultimate-app-container">
      <div className="app-gradient-bg" />
      
      {/* Ultimate Header */}
      <div className="ultimate-header">
        <div className="header-left">
          <div className="aurora-logo">
            🌟
          </div>
          <div className="header-title">
            <h1 className="app-title">
              {getTabDisplayName(activeTab)}
            </h1>
            <p className="app-subtitle">Aurora Life OS</p>
          </div>
        </div>
        
        <div className="header-actions">
          <button 
            className="header-btn"
            onClick={() => setNotificationCount(0)}
            style={{ position: 'relative' }}
          >
            🔔
            {notificationCount > 0 && (
              <div className="notification-badge">
                {notificationCount > 9 ? '9+' : notificationCount}
              </div>
            )}
          </button>
          <button className="header-btn">
            ⚙️
          </button>
        </div>
      </div>

      {/* Ultimate Content */}
      <div className="ultimate-content">
        {/* Debug Component - REMOVE AFTER DEBUGGING */}
        <DebugAuth />
        <ErrorBoundary>
          <ActiveComponent />
        </ErrorBoundary>
      </div>

      {/* Ultimate Bottom Navigation */}
      <nav className="ultimate-bottom-nav">
        <div className="nav-container">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
            >
              <div className="nav-icon">{tab.icon}</div>
              <span className="nav-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}