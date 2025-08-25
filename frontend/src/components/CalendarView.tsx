import React, { useState, useCallback } from 'react';
import { CalendarHeader } from './calendar/CalendarHeader';
import { CalendarEventList } from './calendar/CalendarEventList';
import { AIEventForm } from './calendar/AIEventForm';
import { AICalendarChat } from './calendar/AICalendarChat';
import { RoutineSettingsModal } from './calendar/RoutineSettingsModal';
import { CalendarErrorBoundary } from './CalendarErrorBoundary';
import { useCalendarData } from './calendar/hooks/useCalendarData';
import { useLocalStorage } from './calendar/hooks/useLocalStorage';
import { CalendarEvent, AICalendarFormData, RoutineSettings, ChatMessage } from './calendar/types';

const defaultFormData: AICalendarFormData = {
  title: '',
  description: '',
  duration_minutes: 60,
  event_type: 'task',
  priority: 'medium',
  goal_id: undefined
};

const defaultRoutineSettings: RoutineSettings = {
  wake_up_time: '07:00',
  sleep_time: '23:00',
  gym_time: '18:00',
  lunch_time: '13:00',
  dinner_time: '20:00',
  work_start: '09:00',
  work_end: '18:00',
  break_duration: 15,
  focus_block_duration: 120
};

export function CalendarView() {
  // State management
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showAIPlanner, setShowAIPlanner] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [showRoutineSettings, setShowRoutineSettings] = useState(false);
  const [aiPlannerData, setAiPlannerData] = useState<AICalendarFormData>(defaultFormData);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  
  // Persistent settings
  const [routineSettings, setRoutineSettings] = useLocalStorage('routineSettings', defaultRoutineSettings);

  // Custom hooks for data management
  const {
    events,
    goals,
    isLoading,
    syncWithGoogle,
    createEvent,
    updateEvent,
    deleteEvent,
    bulkScheduleFromGoals,
    optimizeWeek
  } = useCalendarData(selectedDate);

  // Event handlers
  const handleEditEvent = useCallback(async (event: CalendarEvent) => {
    const newTitle = prompt('Edit event title:', event.title);
    if (newTitle && newTitle.trim() && newTitle !== event.title) {
      const result = await updateEvent(event.id, {
        title: newTitle.trim(),
        description: event.description,
        start_time: event.start_time,
        end_time: event.end_time,
        event_type: event.event_type,
        priority: event.priority,
        goal_id: event.goal_id
      });
      
      if (result.success) {
        alert('Event updated successfully!');
      } else {
        alert('Failed to update event');
      }
    }
  }, [updateEvent]);

  const handleDeleteEvent = useCallback(async (eventId: number) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      const result = await deleteEvent(eventId);
      
      if (result.success) {
        alert('Event deleted successfully!');
      } else {
        alert('Failed to delete event');
      }
    }
  }, [deleteEvent]);

  const handleSyncCalendar = useCallback(async () => {
    const result = await syncWithGoogle();
    if (result.success) {
      alert('Calendar synced successfully!');
    } else {
      alert('Failed to sync calendar');
    }
  }, [syncWithGoogle]);

  const handleBulkSchedule = useCallback(async () => {
    const result = await bulkScheduleFromGoals();
    if (result.success) {
      alert('Goals scheduled successfully!');
    } else {
      alert('Failed to schedule from goals');
    }
  }, [bulkScheduleFromGoals]);

  const handleOptimizeWeek = useCallback(async () => {
    const result = await optimizeWeek();
    if (result.success) {
      alert('Week optimized successfully!');
    } else {
      alert('Failed to optimize weekly schedule');
    }
  }, [optimizeWeek]);

  const handleCreateEvent = useCallback(async () => {
    if (!aiPlannerData.title.trim()) return;

    const result = await createEvent(aiPlannerData);
    
    if (result.success) {
      alert('Event created and scheduled successfully!');
      setAiPlannerData(defaultFormData);
      setShowAIPlanner(false);
    } else {
      alert('Failed to create event');
    }
  }, [aiPlannerData, createEvent]);

  const handleSendMessage = useCallback(async (message: string) => {
    // Add user message to chat history
    const userMessage: ChatMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);

    // Add thinking message
    const thinkingMessage: ChatMessage = { 
      role: 'assistant', 
      content: '🤖 Analyzing your request and determining what calendar action to take...' 
    };
    setChatHistory(prev => [...prev, thinkingMessage]);

    try {
      const response = await fetch('http://localhost:8001/api/ai-calendar/intelligent-calendar-assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify({
          user_request: message,
          user_context: `Daily Routine Context:
- Wake up: ${routineSettings.wake_up_time}
- Sleep: ${routineSettings.sleep_time} 
- Gym: ${routineSettings.gym_time}
- Lunch: ${routineSettings.lunch_time}
- Dinner: ${routineSettings.dinner_time}
- Work: ${routineSettings.work_start}-${routineSettings.work_end}
- Break duration: ${routineSettings.break_duration} minutes
- Focus block: ${routineSettings.focus_block_duration} minutes`,
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
- ⏰ Avoided your gym (${routineSettings.gym_time}) and meal times
- 🧠 Optimized around your work hours (${routineSettings.work_start}-${routineSettings.work_end})
- 📈 Sequential scheduling with 15-min buffers
- 🎯 Each task includes detailed step-by-step instructions

💡 **Next Steps:** Check your calendar - everything is perfectly timed around your routine!`;
        } else {
          responseContent = result.message || 'Task completed successfully!';
        }
        
        // Update the last message (remove thinking message and add response)
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            role: 'assistant',
            content: responseContent
          };
          return newHistory;
        });

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
  }, [routineSettings]);

  const handleFormChange = useCallback((changes: Partial<AICalendarFormData>) => {
    setAiPlannerData(prev => ({ ...prev, ...changes }));
  }, []);

  return (
    <CalendarErrorBoundary>
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
            selectedDate={selectedDate}
            onDateChange={setSelectedDate}
            onSyncCalendar={handleSyncCalendar}
            onOpenAIPlanner={() => setShowAIPlanner(true)}
            onOpenAIChat={() => setShowAIChat(true)}
            onOpenRoutineSettings={() => setShowRoutineSettings(true)}
            onBulkSchedule={handleBulkSchedule}
            onOptimizeWeek={handleOptimizeWeek}
            isLoading={isLoading}
          />

          <CalendarEventList
            events={events}
            goals={goals}
            selectedDate={selectedDate}
            onEditEvent={handleEditEvent}
            onDeleteEvent={handleDeleteEvent}
          />

          {/* Modals */}
          <AIEventForm
            isVisible={showAIPlanner}
            formData={aiPlannerData}
            goals={goals}
            onFormChange={handleFormChange}
            onSubmit={handleCreateEvent}
            onClose={() => setShowAIPlanner(false)}
          />

          <AICalendarChat
            isVisible={showAIChat}
            chatHistory={chatHistory}
            onSendMessage={handleSendMessage}
            routineSettings={routineSettings}
            onClose={() => setShowAIChat(false)}
          />

          <RoutineSettingsModal
            isVisible={showRoutineSettings}
            settings={routineSettings}
            onSave={setRoutineSettings}
            onClose={() => setShowRoutineSettings(false)}
          />
        </div>
      </div>
    </CalendarErrorBoundary>
  );
}