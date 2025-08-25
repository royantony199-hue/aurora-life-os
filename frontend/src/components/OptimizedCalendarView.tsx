import React, { memo, useCallback, useMemo, Suspense } from 'react';
import { CalendarProvider, useCalendar } from '../contexts/CalendarContext';
import { OptimizedCalendarEventList } from './calendar/OptimizedCalendarEventList';
import { useOptimizedCallback } from '../hooks/useOptimizedCallback';
import { CalendarEvent, ChatMessage } from './calendar/types';

// Lazy load heavy components
const AIEventForm = React.lazy(() => import('./calendar/AIEventForm').then(module => ({ default: module.AIEventForm })));
const AICalendarChat = React.lazy(() => import('./calendar/AICalendarChat').then(module => ({ default: module.AICalendarChat })));
const RoutineSettingsModal = React.lazy(() => import('./calendar/RoutineSettingsModal').then(module => ({ default: module.RoutineSettingsModal })));

// Memoized header component
const CalendarHeader = memo<{
  selectedDate: string;
  onDateChange: (date: string) => void;
  onSyncCalendar: () => void;
  onOpenAIPlanner: () => void;
  onOpenAIChat: () => void;
  onOpenRoutineSettings: () => void;
  onBulkSchedule: () => void;
  onOptimizeWeek: () => void;
  isLoading?: boolean;
}>(({
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
});

CalendarHeader.displayName = 'CalendarHeader';

// Loading fallback component
const LoadingFallback = memo(() => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px'
  }}>
    <div style={{
      width: '40px',
      height: '40px',
      border: '3px solid #e5e7eb',
      borderTop: '3px solid #4A90E2',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    }} />
  </div>
));

LoadingFallback.displayName = 'LoadingFallback';

// Main calendar component (optimized)
const OptimizedCalendarViewInner = memo(() => {
  const { state, dispatch, ...actions } = useCalendar();
  const [chatHistory, setChatHistory] = React.useState<ChatMessage[]>([]);

  // Memoized handlers to prevent unnecessary re-renders
  const handleEditEvent = useOptimizedCallback(async (event: CalendarEvent) => {
    const newTitle = prompt('Edit event title:', event.title);
    if (newTitle && newTitle.trim() && newTitle !== event.title) {
      const success = await actions.updateEvent(event.id, {
        title: newTitle.trim(),
        description: event.description,
        start_time: event.start_time,
        end_time: event.end_time,
        event_type: event.event_type,
        priority: event.priority,
        goal_id: event.goal_id
      });
      
      if (success) {
        alert('Event updated successfully!');
      } else {
        alert('Failed to update event');
      }
    }
  }, [actions.updateEvent]);

  const handleDeleteEvent = useOptimizedCallback(async (eventId: number) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      const success = await actions.deleteEvent(eventId);
      
      if (success) {
        alert('Event deleted successfully!');
      } else {
        alert('Failed to delete event');
      }
    }
  }, [actions.deleteEvent]);

  const handleSyncCalendar = useOptimizedCallback(async () => {
    const success = await actions.syncWithGoogle();
    if (success) {
      alert('Calendar synced successfully!');
    } else {
      alert('Failed to sync calendar');
    }
  }, [actions.syncWithGoogle]);

  const handleBulkSchedule = useOptimizedCallback(async () => {
    const success = await actions.bulkScheduleFromGoals();
    if (success) {
      alert('Goals scheduled successfully!');
    } else {
      alert('Failed to schedule from goals');
    }
  }, [actions.bulkScheduleFromGoals]);

  const handleOptimizeWeek = useOptimizedCallback(async () => {
    const success = await actions.optimizeWeek();
    if (success) {
      alert('Week optimized successfully!');
    } else {
      alert('Failed to optimize weekly schedule');
    }
  }, [actions.optimizeWeek]);

  const handleDateChange = useOptimizedCallback((date: string) => {
    dispatch({ type: 'SET_SELECTED_DATE', payload: date });
  }, [dispatch]);

  const handleSendMessage = useOptimizedCallback(async (message: string) => {
    const userMessage: ChatMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);

    const thinkingMessage: ChatMessage = { 
      role: 'assistant', 
      content: '🤖 Analyzing your request and determining what calendar action to take...' 
    };
    setChatHistory(prev => [...prev, thinkingMessage]);

    try {
      const token = localStorage.getItem('aurora_access_token');
      const response = await fetch('http://localhost:8001/api/ai-calendar/intelligent-calendar-assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_request: message,
          user_context: `Daily Routine Context:
- Wake up: ${state.routineSettings.wake_up_time}
- Sleep: ${state.routineSettings.sleep_time} 
- Gym: ${state.routineSettings.gym_time}
- Lunch: ${state.routineSettings.lunch_time}
- Dinner: ${state.routineSettings.dinner_time}
- Work: ${state.routineSettings.work_start}-${state.routineSettings.work_end}
- Break duration: ${state.routineSettings.break_duration} minutes
- Focus block: ${state.routineSettings.focus_block_duration} minutes`,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        let responseContent = '';

        if (result.scheduled_events) {
          responseContent = `✅ **Successfully Created and Scheduled!**

${result.message}

📅 **Your New Events:**
${result.scheduled_events.map((event: any) => 
  `• **${event.title}** - ${event.start_time.substring(11, 16)} (${event.duration_minutes} min)`
).join('\n')}

🎯 **What I Did:**
- ⏰ Avoided your gym (${state.routineSettings.gym_time}) and meal times
- 🧠 Optimized around your work hours (${state.routineSettings.work_start}-${state.routineSettings.work_end})
- 📈 Sequential scheduling with 15-min buffers
- 🎯 Each task includes detailed step-by-step instructions

💡 **Next Steps:** Check your calendar - everything is perfectly timed around your routine!`;
        } else {
          responseContent = result.message || 'Task completed successfully!';
        }
        
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            role: 'assistant',
            content: responseContent
          };
          return newHistory;
        });

        // Reload calendar data
        await actions.loadCalendarData();

      } else {
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            role: 'assistant',
            content: '❌ I had trouble processing your request. Please try again with a more specific request.'
          };
          return newHistory;
        });
      }
    } catch (error) {
      setChatHistory(prev => {
        const newHistory = [...prev];
        newHistory[newHistory.length - 1] = {
          role: 'assistant',
          content: '❌ I had trouble creating new tasks. Please try again with a more specific request.'
        };
        return newHistory;
      });
    }
  }, [state.routineSettings, actions.loadCalendarData]);

  // Memoized form data
  const defaultFormData = useMemo(() => ({
    title: '',
    description: '',
    duration_minutes: 60,
    event_type: 'task',
    priority: 'medium',
    goal_id: undefined
  }), []);

  const [aiPlannerData, setAiPlannerData] = React.useState(defaultFormData);

  const handleCreateEvent = useOptimizedCallback(async () => {
    if (!aiPlannerData.title.trim()) return;

    const success = await actions.createEvent(aiPlannerData);
    
    if (success) {
      alert('Event created and scheduled successfully!');
      setAiPlannerData(defaultFormData);
      dispatch({ type: 'SHOW_AI_PLANNER', payload: false });
    } else {
      alert('Failed to create event');
    }
  }, [aiPlannerData, actions.createEvent, defaultFormData, dispatch]);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f5f7fa',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <CalendarHeader
          selectedDate={state.selectedDate}
          onDateChange={handleDateChange}
          onSyncCalendar={handleSyncCalendar}
          onOpenAIPlanner={() => dispatch({ type: 'SHOW_AI_PLANNER', payload: true })}
          onOpenAIChat={() => dispatch({ type: 'SHOW_AI_CHAT', payload: true })}
          onOpenRoutineSettings={() => dispatch({ type: 'SHOW_ROUTINE_SETTINGS', payload: true })}
          onBulkSchedule={handleBulkSchedule}
          onOptimizeWeek={handleOptimizeWeek}
          isLoading={state.isLoading}
        />

        <OptimizedCalendarEventList
          events={state.events}
          goals={state.goals}
          selectedDate={state.selectedDate}
          onEditEvent={handleEditEvent}
          onDeleteEvent={handleDeleteEvent}
        />

        {/* Lazy loaded modals */}
        <Suspense fallback={<LoadingFallback />}>
          {state.showAIPlanner && (
            <AIEventForm
              isVisible={state.showAIPlanner}
              formData={aiPlannerData}
              goals={state.goals}
              onFormChange={(changes) => setAiPlannerData(prev => ({ ...prev, ...changes }))}
              onSubmit={handleCreateEvent}
              onClose={() => dispatch({ type: 'SHOW_AI_PLANNER', payload: false })}
            />
          )}

          {state.showAIChat && (
            <AICalendarChat
              isVisible={state.showAIChat}
              chatHistory={chatHistory}
              onSendMessage={handleSendMessage}
              routineSettings={state.routineSettings}
              onClose={() => dispatch({ type: 'SHOW_AI_CHAT', payload: false })}
            />
          )}

          {state.showRoutineSettings && (
            <RoutineSettingsModal
              isVisible={state.showRoutineSettings}
              settings={state.routineSettings}
              onSave={(settings) => dispatch({ type: 'SET_ROUTINE_SETTINGS', payload: settings })}
              onClose={() => dispatch({ type: 'SHOW_ROUTINE_SETTINGS', payload: false })}
            />
          )}
        </Suspense>

        {/* Error display */}
        {state.error && (
          <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: '#fee',
            color: '#c33',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid #fcc',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            zIndex: 1000,
            maxWidth: '400px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{state.error}</span>
              <button
                onClick={() => dispatch({ type: 'RESET_ERROR' })}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#c33',
                  cursor: 'pointer',
                  fontSize: '16px',
                  marginLeft: '12px'
                }}
              >
                ×
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

OptimizedCalendarViewInner.displayName = 'OptimizedCalendarViewInner';

// Main exported component with provider
export const OptimizedCalendarView = memo(() => {
  return (
    <CalendarProvider>
      <OptimizedCalendarViewInner />
    </CalendarProvider>
  );
});

OptimizedCalendarView.displayName = 'OptimizedCalendarView';