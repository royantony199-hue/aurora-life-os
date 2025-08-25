import { useState, useEffect } from 'react';
import { Plus, Target, TrendingUp, CheckCircle2 } from 'lucide-react';
import { goalsAPI } from '../services/api';

interface Goal {
  id: number;
  title: string;
  description: string;
  progress: number;
  target_date: string;
  status: 'active' | 'completed' | 'paused';
  category: string;
  priority: string;
  created_at: string;
  updated_at: string;
}

export function UltimateGoalsDashboard() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const overallProgress = goals.length > 0 
    ? Math.round(goals.reduce((acc, goal) => acc + goal.progress, 0) / goals.length) 
    : 0;

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      setIsLoading(true);
      const response = await goalsAPI.getGoals();
      setGoals(response.goals || response || []);
    } catch (error) {
      console.error('Failed to load goals:', error);
      setGoals([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#52C41A';
      case 'active': return '#4A90E2';
      case 'paused': return '#FAAD14';
      default: return '#8C8C8C';
    }
  };

  const getCategoryEmoji = (category: string) => {
    const emojis: Record<string, string> = {
      'learning': '📚',
      'health': '💪',
      'personal': '🌟',
      'career': '💼',
      'financial': '💰',
      'relationship': '❤️',
      'other': '🎯'
    };
    return emojis[category.toLowerCase()] || '🎯';
  };

  if (isLoading) {
    return (
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">🎯</div>
          <div>
            <div className="card-title">Goals</div>
            <div className="card-subtitle">Loading your goals...</div>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 16px' }}></div>
          <p style={{ color: '#718096' }}>Loading goals...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Goals Overview Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">🎯</div>
          <div>
            <div className="card-title">Your Goals</div>
            <div className="card-subtitle">Track progress & achieve dreams</div>
          </div>
        </div>
        
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-value">{goals.length}</div>
            <div className="stat-label">Total Goals</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{overallProgress}%</div>
            <div className="stat-label">Progress</div>
          </div>
        </div>

        <button 
          className="ultimate-btn"
          onClick={() => {/* Handle add goal action */}}
          style={{ marginTop: '16px' }}
        >
          <Plus size={20} style={{ marginRight: '8px' }} />
          Add New Goal
        </button>
      </div>

      {/* Goals List */}
      {goals.length > 0 ? (
        <div className="ultimate-card">
          <div className="card-header">
            <div className="card-icon">📋</div>
            <div>
              <div className="card-title">Active Goals</div>
              <div className="card-subtitle">{goals.filter(g => g.status === 'active').length} active goals</div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {goals.map((goal) => (
              <div
                key={goal.id}
                style={{
                  background: 'rgba(102, 126, 234, 0.05)',
                  border: '1px solid rgba(102, 126, 234, 0.1)',
                  borderRadius: '16px',
                  padding: '16px',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div style={{ fontSize: '24px' }}>{getCategoryEmoji(goal.category)}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <h3 style={{ 
                        margin: 0, 
                        fontSize: '16px', 
                        fontWeight: '600', 
                        color: '#1a202c' 
                      }}>
                        {goal.title}
                      </h3>
                      <div
                        style={{
                          background: getStatusColor(goal.status),
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: '500',
                          padding: '4px 8px',
                          borderRadius: '8px'
                        }}
                      >
                        {goal.status}
                      </div>
                    </div>
                    
                    <p style={{ 
                      margin: '0 0 12px 0', 
                      fontSize: '14px', 
                      color: '#718096',
                      lineHeight: '1.4'
                    }}>
                      {goal.description}
                    </p>

                    {/* Progress Bar */}
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', color: '#718096' }}>Progress</span>
                        <span style={{ fontSize: '12px', fontWeight: '600', color: '#667eea' }}>
                          {goal.progress}%
                        </span>
                      </div>
                      <div style={{
                        width: '100%',
                        height: '8px',
                        background: 'rgba(102, 126, 234, 0.1)',
                        borderRadius: '4px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${goal.progress}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                          borderRadius: '4px',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: '#718096' }}>
                      <span>📅 {goal.category}</span>
                      {goal.target_date && (
                        <span>🎯 Due: {new Date(goal.target_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="ultimate-card">
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎯</div>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: '600', color: '#1a202c' }}>
              No Goals Yet
            </h3>
            <p style={{ margin: '0 0 24px 0', fontSize: '14px', color: '#718096' }}>
              Create your first goal to start tracking your progress
            </p>
            <button 
              className="ultimate-btn"
              onClick={() => {/* Handle create first goal action */}}
            >
              <Target size={20} style={{ marginRight: '8px' }} />
              Create Your First Goal
            </button>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">⚡</div>
          <div>
            <div className="card-title">Quick Actions</div>
            <div className="card-subtitle">Goal management tools</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <button 
            className="ultimate-btn-secondary"
            onClick={() => {/* Handle view analytics action */}}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <TrendingUp size={16} />
            Analytics
          </button>
          <button 
            className="ultimate-btn-secondary"
            onClick={() => {/* Handle view completed goals action */}}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <CheckCircle2 size={16} />
            Completed
          </button>
        </div>
      </div>
    </div>
  );
}