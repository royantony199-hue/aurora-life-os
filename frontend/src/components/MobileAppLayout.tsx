import { useState } from 'react';
import { ChatInterface } from './ChatInterface';
import { CalendarView } from './CalendarView';
import { GoalsDashboard } from './GoalsDashboard';
import { MoodTracker } from './MoodTracker';
import { ProfileSettings } from './ProfileSettings';
import { AuthPage } from './AuthPage';
import { ErrorBoundary } from './ErrorBoundary';
import { useAuth } from '../contexts/AuthContext';

type TabType = 'chat' | 'calendar' | 'goals' | 'mood' | 'profile';

interface TabConfig {
  id: TabType;
  label: string;
  icon: string;
  component: React.ComponentType;
}

export function MobileAppLayout() {
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const { isLoading, isAuthenticated } = useAuth();

  const tabs: TabConfig[] = [
    { id: 'chat', label: 'Chat', icon: '💬', component: ChatInterface },
    { id: 'calendar', label: 'Calendar', icon: '📅', component: CalendarView },
    { id: 'goals', label: 'Goals', icon: '🎯', component: GoalsDashboard },
    { id: 'mood', label: 'Mood', icon: '❤️', component: MoodTracker },
    { id: 'profile', label: 'Profile', icon: '👤', component: ProfileSettings },
  ];

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div className="mobile-app-container">
        <div className="mobile-loading-screen">
          <div className="mobile-loading-content">
            <div className="mobile-auth-logo">
              <span>🌟</span>
            </div>
            <h2 className="mobile-loading-title">Aurora Life OS</h2>
            <div className="mobile-loading-spinner"></div>
            <p className="mobile-loading-text">Loading your AI companion...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show authentication page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || ChatInterface;
  const activeTabInfo = tabs.find(tab => tab.id === activeTab);

  return (
    <div className="mobile-app-container">
      {/* Mobile Header */}
      <div className="mobile-app-header">
        <div className="mobile-header-content">
          <div className="mobile-card-icon">
            <span style={{ fontSize: '18px' }}>🌟</span>
          </div>
          <div className="mobile-header-text">
            <h1 className="mobile-header-title">
              {activeTabInfo?.label || 'Aurora'}
            </h1>
            <p className="mobile-header-subtitle">Your AI life companion</p>
          </div>
        </div>
        <div className="mobile-header-actions">
          <button className="mobile-notification-btn">
            <span>🔔</span>
          </button>
        </div>
      </div>

      {/* Mobile Content */}
      <div className="mobile-app-content">
        <ErrorBoundary>
          <ActiveComponent />
        </ErrorBoundary>
      </div>

      {/* Bottom Navigation */}
      <nav className="mobile-bottom-navigation">
        <div className="mobile-bottom-nav-container">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`mobile-nav-item ${activeTab === tab.id ? 'active' : ''}`}
            >
              <div className="mobile-nav-icon">{tab.icon}</div>
              <span className="mobile-nav-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}