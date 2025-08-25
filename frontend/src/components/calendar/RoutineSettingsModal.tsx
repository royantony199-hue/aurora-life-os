import React, { useState } from 'react';
import { RoutineSettings } from './types';

interface RoutineSettingsModalProps {
  isVisible: boolean;
  settings: RoutineSettings;
  onSave: (settings: RoutineSettings) => void;
  onClose: () => void;
}

export const RoutineSettingsModal: React.FC<RoutineSettingsModalProps> = ({
  isVisible,
  settings,
  onSave,
  onClose
}) => {
  const [localSettings, setLocalSettings] = useState<RoutineSettings>(settings);

  if (!isVisible) return null;

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  const handleChange = (key: keyof RoutineSettings, value: string | number) => {
    setLocalSettings(prev => ({
      ...prev,
      [key]: value
    }));
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
            ⚙️ Daily Routine Settings
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

        {/* Settings Form */}
        <div style={{ padding: '24px' }}>
          <p style={{ 
            color: '#666', 
            fontSize: '14px', 
            marginBottom: '24px',
            lineHeight: '1.4'
          }}>
            Configure your daily routine so the AI can schedule tasks around your existing commitments.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Sleep Schedule */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                🌅 Wake Up Time
              </label>
              <input
                type="time"
                value={localSettings.wake_up_time}
                onChange={(e) => handleChange('wake_up_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
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
                🌙 Sleep Time
              </label>
              <input
                type="time"
                value={localSettings.sleep_time}
                onChange={(e) => handleChange('sleep_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Work Schedule */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                🏢 Work Start
              </label>
              <input
                type="time"
                value={localSettings.work_start}
                onChange={(e) => handleChange('work_start', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
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
                🏠 Work End
              </label>
              <input
                type="time"
                value={localSettings.work_end}
                onChange={(e) => handleChange('work_end', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Meals */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                🍽️ Lunch Time
              </label>
              <input
                type="time"
                value={localSettings.lunch_time}
                onChange={(e) => handleChange('lunch_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
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
                🍝 Dinner Time
              </label>
              <input
                type="time"
                value={localSettings.dinner_time}
                onChange={(e) => handleChange('dinner_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Fitness */}
            <div style={{ gridColumn: 'span 2' }}>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                💪 Gym Time
              </label>
              <input
                type="time"
                value={localSettings.gym_time}
                onChange={(e) => handleChange('gym_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Productivity Settings */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '6px',
                color: '#333'
              }}>
                ⏱️ Break Duration (minutes)
              </label>
              <input
                type="number"
                min="5"
                max="60"
                value={localSettings.break_duration}
                onChange={(e) => handleChange('break_duration', parseInt(e.target.value) || 15)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
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
                🎯 Focus Block (minutes)
              </label>
              <input
                type="number"
                min="30"
                max="180"
                value={localSettings.focus_block_duration}
                onChange={(e) => handleChange('focus_block_duration', parseInt(e.target.value) || 120)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
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
              onClick={onClose}
              style={{
                padding: '10px 20px',
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
              onClick={handleSave}
              style={{
                padding: '10px 20px',
                backgroundColor: '#4A90E2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};