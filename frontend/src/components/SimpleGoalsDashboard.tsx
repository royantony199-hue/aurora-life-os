import { useState, useEffect } from 'react';
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

export function SimpleGoalsDashboard() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    category: 'personal',
    priority: 'medium' as 'low' | 'medium' | 'high',
    target_date: ''
  });

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

  const handleAddGoal = async () => {
    
    if (!newGoal.title.trim()) {
      alert('Please enter a goal title');
      return;
    }

    try {
      
      // Prepare the goal data with proper format
      const goalData = {
        title: newGoal.title.trim(),
        description: newGoal.description.trim() || undefined,
        category: newGoal.category, // This should already match the enum
        target_date: newGoal.target_date ? new Date(newGoal.target_date).toISOString() : undefined
      };
      const result = await goalsAPI.createGoal(goalData);
      
      setNewGoal({
        title: '',
        description: '',
        category: 'personal',
        priority: 'medium',
        target_date: ''
      });
      setShowAddGoal(false);
      await loadGoals();
      alert('Goal created successfully!');
    } catch (error) {
      console.error('Failed to create goal:', error);
      
      let errorMessage = 'Unknown error';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data) {
        errorMessage = JSON.stringify(error.response.data);
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`Failed to create goal: ${errorMessage}`);
    }
  };

  const updateGoalProgress = async (goalId: number, newProgress: number) => {
    try {
      await goalsAPI.updateGoal(goalId, { progress: newProgress });
      await loadGoals();
    } catch (error) {
      console.error('Failed to update goal:', error);
    }
  };

  const handleDeleteGoal = async (goalId: number, goalTitle: string) => {
    if (confirm(`Are you sure you want to delete "${goalTitle}"?`)) {
      try {
        await goalsAPI.deleteGoal(goalId);
        await loadGoals();
        alert('Goal deleted successfully!');
      } catch (error) {
        console.error('Failed to delete goal:', error);
        alert('Failed to delete goal');
      }
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
      <div style={{ 
        height: '100%', 
        background: '#F5F7FA', 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid #E5E7EB',
            borderTop: '3px solid #4A90E2',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p style={{ color: '#8C8C8C' }}>Loading goals...</p>
        </div>
      </div>
    );
  }

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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ 
              fontSize: '20px', 
              fontWeight: '500', 
              color: '#262626',
              margin: '0 0 4px 0'
            }}>
              Your Goals
            </h1>
            <p style={{ 
              fontSize: '14px', 
              color: '#8C8C8C',
              margin: 0
            }}>
              Track progress & achieve dreams
            </p>
          </div>
          <button 
            onClick={() => setShowAddGoal(!showAddGoal)}
            style={{
              background: '#4A90E2',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '20px'
            }}
          >
            +
          </button>
        </div>

        {/* Overall Progress */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(74, 144, 226, 0.1) 0%, rgba(114, 46, 209, 0.1) 100%)',
          borderRadius: '12px',
          padding: '16px',
          marginTop: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: '14px', fontWeight: '500', color: '#262626', margin: '0 0 4px 0' }}>
                Overall Progress
              </p>
              <p style={{ fontSize: '28px', fontWeight: '700', color: '#4A90E2', margin: 0 }}>
                {overallProgress}%
              </p>
            </div>
            <div style={{ fontSize: '48px' }}>🎯</div>
          </div>
        </div>
      </div>

      <div style={{ padding: '16px' }}>
        {/* Add Goal Form */}
        {showAddGoal && (
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}>
            <h3 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: '0 0 16px 0'
            }}>
              Add New Goal
            </h3>
            
            <input
              type="text"
              placeholder="Goal title"
              value={newGoal.title}
              onChange={(e) => setNewGoal({...newGoal, title: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D9D9D9',
                borderRadius: '8px',
                marginBottom: '12px',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            
            <textarea
              placeholder="Description (optional)"
              value={newGoal.description}
              onChange={(e) => setNewGoal({...newGoal, description: e.target.value})}
              rows={3}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D9D9D9',
                borderRadius: '8px',
                marginBottom: '12px',
                fontSize: '14px',
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'inherit'
              }}
            />
            
            <select
              value={newGoal.category}
              onChange={(e) => setNewGoal({...newGoal, category: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D9D9D9',
                borderRadius: '8px',
                marginBottom: '12px',
                fontSize: '14px',
                outline: 'none'
              }}
            >
              <option value="personal">Personal</option>
              <option value="health">Health</option>
              <option value="learning">Learning</option>
              <option value="career">Career</option>
              <option value="financial">Financial</option>
              <option value="relationship">Relationship</option>
              <option value="other">Other</option>
            </select>

            <input
              type="date"
              value={newGoal.target_date}
              onChange={(e) => setNewGoal({...newGoal, target_date: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D9D9D9',
                borderRadius: '8px',
                marginBottom: '16px',
                fontSize: '14px',
                outline: 'none'
              }}
            />

            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                onClick={handleAddGoal}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#4A90E2',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Add Goal
              </button>
              <button 
                onClick={() => setShowAddGoal(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#F5F7FA',
                  color: '#8C8C8C',
                  border: '1px solid #D9D9D9',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Goals List */}
        {goals.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {goals.map((goal) => (
              <div
                key={goal.id}
                style={{
                  background: 'white',
                  borderRadius: '12px',
                  padding: '20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ fontSize: '24px' }}>{getCategoryEmoji(goal.category)}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <h3 style={{ 
                        margin: 0, 
                        fontSize: '16px', 
                        fontWeight: '600', 
                        color: '#262626',
                        flex: 1
                      }}>
                        {goal.title}
                      </h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          background: getStatusColor(goal.status),
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: '500',
                          padding: '4px 8px',
                          borderRadius: '8px'
                        }}>
                          {goal.status}
                        </div>
                        <button
                          onClick={() => handleDeleteGoal(goal.id, goal.title)}
                          style={{
                            background: 'rgba(255, 77, 79, 0.1)',
                            color: '#FF4D4F',
                            border: '1px solid rgba(255, 77, 79, 0.2)',
                            borderRadius: '6px',
                            width: '30px',
                            height: '30px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            fontSize: '16px'
                          }}
                          title="Delete goal"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                    
                    {goal.description && (
                      <p style={{ 
                        margin: '0 0 12px 0', 
                        fontSize: '14px', 
                        color: '#8C8C8C',
                        lineHeight: '1.4'
                      }}>
                        {goal.description}
                      </p>
                    )}

                    {/* Progress Bar */}
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', color: '#8C8C8C' }}>Progress</span>
                        <span style={{ fontSize: '12px', fontWeight: '600', color: '#4A90E2' }}>
                          {goal.progress}%
                        </span>
                      </div>
                      <div style={{
                        width: '100%',
                        height: '8px',
                        background: '#E5E7EB',
                        borderRadius: '4px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${goal.progress}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #4A90E2 0%, #722ED1 100%)',
                          borderRadius: '4px',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>

                    {/* Progress Controls */}
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
                      <button 
                        onClick={() => updateGoalProgress(goal.id, Math.max(0, goal.progress - 10))}
                        style={{
                          width: '30px',
                          height: '30px',
                          background: '#F5F7FA',
                          border: '1px solid #D9D9D9',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '16px'
                        }}
                      >
                        -
                      </button>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="5"
                        value={goal.progress}
                        onChange={(e) => updateGoalProgress(goal.id, parseInt(e.target.value))}
                        style={{
                          flex: 1,
                          height: '8px',
                          borderRadius: '4px',
                          background: '#E5E7EB',
                          outline: 'none',
                          appearance: 'none',
                          cursor: 'pointer'
                        }}
                      />
                      <button 
                        onClick={() => updateGoalProgress(goal.id, Math.min(100, goal.progress + 10))}
                        style={{
                          width: '30px',
                          height: '30px',
                          background: '#F5F7FA',
                          border: '1px solid #D9D9D9',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '16px'
                        }}
                      >
                        +
                      </button>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: '#8C8C8C' }}>
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
        ) : (
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '40px 20px',
            textAlign: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎯</div>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: '600', color: '#262626' }}>
              No Goals Yet
            </h3>
            <p style={{ margin: '0 0 24px 0', fontSize: '14px', color: '#8C8C8C' }}>
              Create your first goal to start tracking your progress
            </p>
            <button 
              onClick={() => setShowAddGoal(true)}
              style={{
                padding: '12px 24px',
                background: '#4A90E2',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Create Your First Goal
            </button>
          </div>
        )}
      </div>
    </div>
  );
}