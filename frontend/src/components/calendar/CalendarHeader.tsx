import React from 'react';

interface CalendarHeaderProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  onSyncCalendar: () => void;
  onOpenAIPlanner: () => void;
  onOpenAIChat: () => void;
  onOpenRoutineSettings: () => void;
  onBulkSchedule: () => void;
  onOptimizeWeek: () => void;
  isLoading?: boolean;
}

export const CalendarHeader: React.FC<CalendarHeaderProps> = ({
  selectedDate,
  onDateChange,
  onSyncCalendar,
  onOpenAIPlanner,
  onOpenAIChat,
  onOpenRoutineSettings,
  onBulkSchedule,
  onOptimizeWeek,
  isLoading = false
}) => {
  return (
    <div style={{
      backgroundColor: '#ffffff',
      padding: '24px',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      marginBottom: '24px'
    }}>
      {/* Header Title */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h1 style={{
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#333',
          margin: '0',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          📅 Your Calendar
          {isLoading && (
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid #e5e7eb',
              borderTop: '2px solid #4A90E2',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
          )}
        </h1>
        
        <button
          onClick={onSyncCalendar}
          style={{
            padding: '8px 16px',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          🔄 Sync Google Calendar
        </button>
      </div>

      {/* Date Selector */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{
          display: 'block',
          fontSize: '14px',
          fontWeight: '500',
          color: '#666',
          marginBottom: '8px'
        }}>
          Select Date
        </label>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => onDateChange(e.target.value)}
          style={{
            padding: '10px 12px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '14px',
            backgroundColor: '#f9f9f9'
          }}
        />
      </div>

      {/* Action Buttons Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '12px'
      }}>
        <button
          onClick={onOpenAIPlanner}
          style={{
            padding: '12px 16px',
            backgroundColor: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          🤖 AI Event Planner
        </button>

        <button
          onClick={onOpenAIChat}
          style={{
            padding: '12px 16px',
            backgroundColor: '#f093fb',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          💬 AI Calendar Assistant
        </button>

        <button
          onClick={onOpenRoutineSettings}
          style={{
            padding: '12px 16px',
            backgroundColor: '#ff9a9e',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          ⚙️ Routine Settings
        </button>

        <button
          onClick={onBulkSchedule}
          style={{
            padding: '12px 16px',
            backgroundColor: '#a8edea',
            color: '#333',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          📋 Schedule from Goals
        </button>

        <button
          onClick={onOptimizeWeek}
          style={{
            padding: '12px 16px',
            backgroundColor: '#ffecd2',
            color: '#333',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
        >
          🔧 Optimize Week
        </button>
      </div>
    </div>
  );
};