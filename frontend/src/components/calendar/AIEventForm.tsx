import React from 'react';
import { AICalendarFormData, Goal } from './types';

interface AIEventFormProps {
  isVisible: boolean;
  formData: AICalendarFormData;
  goals: Goal[];
  onFormChange: (data: Partial<AICalendarFormData>) => void;
  onSubmit: () => void;
  onClose: () => void;
}

export const AIEventForm: React.FC<AIEventFormProps> = ({
  isVisible,
  formData,
  goals,
  onFormChange,
  onSubmit,
  onClose
}) => {
  if (!isVisible) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '500px',
        maxHeight: '80%',
        overflowY: 'auto',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px 24px 0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h3 style={{ margin: '0', fontSize: '20px', color: '#333' }}>
            🤖 AI Event Planner
          </h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#999'
            }}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
          <p style={{ 
            color: '#666', 
            fontSize: '14px', 
            marginBottom: '24px',
            lineHeight: '1.4'
          }}>
            Create an event and let AI find the optimal time in your schedule.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Title */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                Event Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => onFormChange({ title: e.target.value })}
                placeholder="e.g., 'Learn guitar basics'"
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Description */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => onFormChange({ description: e.target.value })}
                placeholder="Provide more details to help AI create better tasks..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>

            {/* Duration and Priority */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '14px', 
                  fontWeight: '500', 
                  marginBottom: '6px',
                  color: '#333'
                }}>
                  Duration (minutes)
                </label>
                <input
                  type="number"
                  min="15"
                  max="480"
                  value={formData.duration_minutes}
                  onChange={(e) => onFormChange({ duration_minutes: parseInt(e.target.value) || 60 })}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                />
              </div>

              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '14px', 
                  fontWeight: '500', 
                  marginBottom: '6px',
                  color: '#333'
                }}>
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => onFormChange({ priority: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                </select>
              </div>
            </div>

            {/* Event Type and Goal */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '14px', 
                  fontWeight: '500', 
                  marginBottom: '6px',
                  color: '#333'
                }}>
                  Event Type
                </label>
                <select
                  value={formData.event_type}
                  onChange={(e) => onFormChange({ event_type: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="task">Task</option>
                  <option value="learning">Learning</option>
                  <option value="exercise">Exercise</option>
                  <option value="meeting">Meeting</option>
                  <option value="personal">Personal</option>
                  <option value="work">Work</option>
                </select>
              </div>

              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '14px', 
                  fontWeight: '500', 
                  marginBottom: '6px',
                  color: '#333'
                }}>
                  Related Goal
                </label>
                <select
                  value={formData.goal_id || ''}
                  onChange={(e) => onFormChange({ 
                    goal_id: e.target.value ? parseInt(e.target.value) : undefined 
                  })}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="">No specific goal</option>
                  {goals.map(goal => (
                    <option key={goal.id} value={goal.id}>
                      {goal.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end',
            marginTop: '32px',
            paddingTop: '20px',
            borderTop: '1px solid #eee'
          }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '12px 20px',
                backgroundColor: '#f5f5f5',
                color: '#666',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!formData.title.trim()}
              style={{
                padding: '12px 24px',
                backgroundColor: formData.title.trim() ? '#4A90E2' : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: formData.title.trim() ? 'pointer' : 'not-allowed',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              🤖 Create with AI
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};