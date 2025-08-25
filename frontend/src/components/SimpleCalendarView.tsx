import { useState, useEffect } from 'react';

interface CalendarEvent {
  id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  event_type: string;
  priority: string;
  goal_id?: number;
}

interface Goal {
  id: number;
  title: string;
  category: string;
  status: string;
}

export function SimpleCalendarView() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAIPlanner, setShowAIPlanner] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [showRoutineSettings, setShowRoutineSettings] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [aiPlannerData, setAiPlannerData] = useState({
    title: '',
    description: '',
    duration_minutes: 60,
    event_type: 'task',
    priority: 'medium',
    goal_id: undefined as number | undefined
  });
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: string, content: string}[]>([]);
  const [routineSettings, setRoutineSettings] = useState({
    wake_up_time: '07:00',
    sleep_time: '23:00',
    gym_time: '18:00',
    lunch_time: '13:00',
    dinner_time: '20:00',
    work_start: '09:00',
    work_end: '18:00',
    break_duration: 15,
    focus_block_duration: 120
  });

  useEffect(() => {
    loadCalendarData();
    loadGoals();
  }, [selectedDate]);

  const loadCalendarData = async () => {
    try {
      setIsLoading(true);
      
      // First, try to sync Google Calendar events
      try {
        const syncResponse = await fetch('http://localhost:8001/api/calendar/sync', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
          },
        });
        if (syncResponse.ok) {
          const syncResult = await syncResponse.json();
          // Google Calendar sync successful
        } else {
          // Google Calendar sync not available or failed
        }
      } catch (syncError) {
        // Google Calendar sync error - continuing with local events
      }
      
      // Then load all events (both local and synced)
      const response = await fetch(`http://localhost:8001/api/calendar/events?start_date=${selectedDate}&end_date=${selectedDate}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        // Transform the API response to match our interface
        const transformedEvents: CalendarEvent[] = data.map((event: any) => ({
          id: event.id,
          title: event.title,
          description: event.description || '',
          start_time: event.start_time,
          end_time: event.end_time,
          event_type: event.event_type,
          priority: event.priority || 'medium',
          goal_id: event.goal_id
        }));
        setEvents(transformedEvents);
      } else {
        console.error('Failed to fetch events:', response.status);
        setEvents([]);
      }
    } catch (error) {
      console.error('Failed to load calendar events:', error);
      setEvents([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadGoals = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/goals/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setGoals(data || []);
      }
    } catch (error) {
      console.error('Failed to load goals:', error);
      setGoals([]);
    }
  };

  const handleAISchedule = async () => {
    
    if (!aiPlannerData.title.trim()) {
      alert('Please enter a task title');
      return;
    }

    try {
      const response = await fetch('http://localhost:8001/api/ai-calendar/smart-create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify({
          ...aiPlannerData,
          goal_id: aiPlannerData.goal_id || undefined
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert('Event scheduled successfully by AI!');
        setAiPlannerData({
          title: '',
          description: '',
          duration_minutes: 60,
          event_type: 'task',
          priority: 'medium',
          goal_id: undefined
        });
        setShowAIPlanner(false);
        await loadCalendarData();
      } else {
        throw new Error('Failed to schedule event');
      }
    } catch (error) {
      console.error('Failed to create AI event:', error);
      alert('Failed to schedule event with AI');
    }
  };

  const handleDeleteEvent = async (eventId: number, eventTitle: string) => {
    if (confirm(`Are you sure you want to delete "${eventTitle}"?\n\nThis will remove the event from both Aurora Life OS and your Google Calendar.`)) {
      try {
        const response = await fetch(`http://localhost:8001/api/calendar/events/${eventId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
          },
        });

        if (response.ok) {
          const result = await response.json();
          if (result.google_deleted) {
            alert('✅ Event deleted successfully from both Aurora and Google Calendar!');
          } else if (result.google_error) {
            alert(`⚠️ Event deleted from Aurora, but Google Calendar sync failed: ${result.google_error}`);
          } else {
            alert('✅ Event deleted successfully!');
          }
          await loadCalendarData();
        } else {
          const errorText = await response.text();
          throw new Error(errorText || 'Failed to delete event');
        }
      } catch (error) {
        console.error('Failed to delete event:', error);
        alert(`❌ Failed to delete event: ${error.message}`);
      }
    }
  };

  const handleEditEvent = async (event: CalendarEvent) => {
    const newTitle = prompt('Edit event title:', event.title);
    if (newTitle && newTitle.trim() && newTitle !== event.title) {
      try {
        const response = await fetch(`http://localhost:8001/api/calendar/events/${event.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
          },
          body: JSON.stringify({
            title: newTitle.trim(),
            description: event.description,
            start_time: event.start_time,
            end_time: event.end_time,
            event_type: event.event_type,
            priority: event.priority,
            goal_id: event.goal_id
          }),
        });

        if (response.ok) {
          alert('Event updated successfully!');
          await loadCalendarData();
        } else {
          throw new Error('Failed to update event');
        }
      } catch (error) {
        console.error('Failed to update event:', error);
        alert('Failed to update event');
      }
    }
  };

  const handleBulkScheduleFromGoals = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/ai-calendar/bulk-schedule-from-goals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify({
          days_ahead: 7
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`🎯 AI Goal Scheduler Success!\n\nScheduled ${result.scheduled_events.length} work sessions for ${result.goals_processed} goals.\n\nThe AI has optimally placed these sessions based on your calendar availability and goal priorities.`);
        await loadCalendarData();
      } else {
        const error = await response.text();
        alert(`Failed to schedule goal work sessions: ${error}`);
      }
    } catch (error) {
      console.error('Failed to bulk schedule from goals:', error);
      alert('Failed to schedule goal work sessions');
    }
  };

  const handleOptimizeWeek = async () => {
    try {
      // Get Monday of current week
      const today = new Date();
      const monday = new Date(today);
      monday.setDate(today.getDate() - today.getDay() + 1);
      const mondayStr = monday.toISOString().split('T')[0];

      const response = await fetch('http://localhost:8001/api/ai-calendar/weekly-optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify({
          week_start_date: mondayStr
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`📊 Weekly Optimization Complete!\n\nProductivity Score: ${result.productivity_score || 'N/A'}\nGoal Alignment: ${result.goal_alignment_score || 'N/A'}\n\nAI has analyzed your week and provided optimization suggestions for better goal achievement.`);
      } else {
        const error = await response.text();
        alert(`Failed to optimize week: ${error}`);
      }
    } catch (error) {
      console.error('Failed to optimize week:', error);
      alert('Failed to optimize weekly schedule');
    }
  };

  const handleSendMessage = async () => {
    if (!chatMessage.trim()) return;
    
    const userMessage = chatMessage;
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);
    
    try {
      // Add AI's thinking message
      setChatHistory(prev => [...prev, { role: 'assistant', content: '🤖 Analyzing your request and determining what calendar action to take...' }]);
      
      // Use the new intelligent calendar assistant endpoint
      const response = await fetch('http://localhost:8001/api/ai-calendar/intelligent-calendar-assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token') || 'demo_token'}`,
        },
        body: JSON.stringify({
          user_request: userMessage,
          user_context: `Daily Routine Context:
- Wake up: ${routineSettings.wake_up_time}
- Sleep: ${routineSettings.sleep_time} 
- Gym: ${routineSettings.gym_time}
- Lunch: ${routineSettings.lunch_time}
- Dinner: ${routineSettings.dinner_time}
- Work hours: ${routineSettings.work_start} - ${routineSettings.work_end}
- Preferred focus blocks: ${routineSettings.focus_block_duration} minutes
- Break duration: ${routineSettings.break_duration} minutes`
        }),
      });

      if (response.ok) {
        const result = await response.json();
        
        // Handle different types of responses based on the action taken
        let responseContent = '';
        
        if (result.scheduled_events && result.scheduled_events.length > 0) {
          // Creating new tasks
          const eventsText = result.scheduled_events.map((event, idx) => 
            `${idx + 1}. **${event.title}** (${event.duration_minutes} min) - ${event.start_time.split('T')[1].substring(0,5)}`
          ).join('\n');
          
          responseContent = `🎯 **Task Breakdown & Scheduling Complete!**

📋 **Your Request:** "${userMessage}"

🤖 **AI Strategy:** ${result.strategy_note || 'Broke down your goal into actionable tasks'}

📅 **Scheduled ${result.scheduled_events.length} Events:**
${eventsText}

✅ **Smart Scheduling:**
- ⏰ Avoided your gym (${routineSettings.gym_time}) and meal times
- 🧠 Optimized around your work hours (${routineSettings.work_start}-${routineSettings.work_end})
- 📈 Sequential scheduling with 15-min buffers
- 🎯 Each task includes detailed step-by-step instructions

💡 **Next Steps:** Check your calendar - everything is perfectly timed around your routine!`;
        } else if (result.events_by_date) {
          // Viewing schedule
          const totalEvents = Object.values(result.events_by_date).flat().length;
          responseContent = `📅 **Your Schedule Overview**

${result.message}

📊 **Schedule Statistics:**
${result.insights?.join('\n') || ''}

💡 **Suggestions:**
${result.suggestions?.join('\n') || 'Your schedule looks good!'}`;
        } else if (result.event_id) {
          // Event modification (edit/reschedule/delete)
          responseContent = `✅ **Calendar Update Complete!**

${result.message}

${result.changes ? `🔄 **Changes Made:**
${Object.entries(result.changes).map(([key, value]) => `- ${key}: ${value}`).join('\n')}` : ''}

${result.freed_time ? `⏰ **Freed Time:** ${result.freed_time.duration_minutes} minutes starting at ${result.freed_time.start_time?.substring(11, 16)}` : ''}

${result.recommendations?.length > 0 ? `💡 **Recommendations:**
${result.recommendations.join('\n')}` : ''}`;
        } else if (result.optimizations) {
          // Schedule optimization
          responseContent = `🔧 **Schedule Optimization Analysis**

${result.message}

${result.ai_insights?.priority_changes?.length > 0 ? `🎯 **Priority Changes Recommended:**
${result.ai_insights.priority_changes.join('\n')}` : ''}

${result.action_items?.length > 0 ? `📋 **Action Items:**
${result.action_items.join('\n')}` : ''}`;
        } else {
          // Generic success message
          responseContent = result.message || 'Action completed successfully!';
        }
        
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            role: 'assistant',
            content: responseContent
          };
          return newHistory;
        });
        
        // Refresh calendar if events were modified
        if (result.scheduled_events || result.event_id || result.freed_time) {
          await loadCalendarData();
        }
        
      } else {
        const errorData = await response.text();
        setChatHistory(prev => {
          const newHistory = [...prev];
          newHistory[newHistory.length - 1] = {
            role: 'assistant',
            content: `❌ I encountered an issue processing your request. 

**Error:** ${errorData}

💡 **Try being more specific**, like:
- "I need to focus on lead generation today"
- "Move my gym session to 4 PM"  
- "Cancel the client call tomorrow"
- "What's my schedule for today?"
- "Reschedule the presentation prep"`
          };
          return newHistory;
        });
      }
    } catch (error) {
      console.error('AI chat error:', error);
      setChatHistory(prev => {
        const newHistory = [...prev];
        newHistory[newHistory.length - 1] = {
          role: 'assistant',
          content: `❌ **Connection Error**

I couldn't process your request right now. Please try again.

If the issue persists, try simpler requests like:
- "Schedule 2 hours for lead generation"
- "Help me plan my sales activities"
- "Block time for client outreach"`
        };
        return newHistory;
      });
    }
  };

  const handleSaveRoutineSettings = async () => {
    try {
      // For now, save to localStorage. Later can be saved to backend
      localStorage.setItem('aurora_routine_settings', JSON.stringify(routineSettings));
      alert('✅ Routine settings saved! AI will now consider these times when scheduling your tasks.');
    } catch (error) {
      console.error('Failed to save routine settings:', error);
      alert('❌ Failed to save routine settings');
    }
  };

  // Load routine settings on component mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('aurora_routine_settings');
      if (saved) {
        setRoutineSettings(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load routine settings:', error);
    }
  }, []);

  const formatTime = (dateTime: string) => {
    return new Date(dateTime).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getEventTypeEmoji = (type: string) => {
    const emojis: Record<string, string> = {
      'meeting': '🤝',
      'task': '📋',
      'focus': '🎯',
      'break': '☕',
      'workout': '💪',
      'learning': '📚',
      'creative': '🎨'
    };
    return emojis[type] || '📅';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF4D4F';
      case 'medium': return '#FAAD14';
      case 'low': return '#52C41A';
      default: return '#8C8C8C';
    }
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
          <p style={{ color: '#8C8C8C' }}>Loading calendar...</p>
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
              AI Calendar
            </h1>
            <p style={{ 
              fontSize: '14px', 
              color: '#8C8C8C',
              margin: 0
            }}>
              Let AI optimize your schedule
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button 
              onClick={() => setShowAIPlanner(!showAIPlanner)}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              🤖 AI Schedule
            </button>
            <button 
              onClick={() => setShowAIChat(!showAIChat)}
              style={{
                background: showAIChat ? 'linear-gradient(135deg, #52C41A 0%, #389E0D 100%)' : 'rgba(82, 196, 26, 0.1)',
                color: showAIChat ? 'white' : '#52C41A',
                border: showAIChat ? 'none' : '1px solid rgba(82, 196, 26, 0.3)',
                borderRadius: '12px',
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              💬 AI Chat
            </button>
            <button 
              onClick={loadCalendarData}
              style={{
                background: 'linear-gradient(135deg, #1890FF 0%, #096DD9 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              📅 Sync Google
            </button>
            <button 
              onClick={() => setShowRoutineSettings(!showRoutineSettings)}
              style={{
                background: showRoutineSettings ? 'linear-gradient(135deg, #FAAD14 0%, #D48806 100%)' : 'rgba(250, 173, 20, 0.1)',
                color: showRoutineSettings ? 'white' : '#FAAD14',
                border: showRoutineSettings ? 'none' : '1px solid rgba(250, 173, 20, 0.3)',
                borderRadius: '12px',
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              ⚙️ Routine
            </button>
          </div>
        </div>

        {/* Date Selector */}
        <div style={{ marginTop: '16px' }}>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #D9D9D9',
              borderRadius: '8px',
              fontSize: '14px',
              outline: 'none'
            }}
          />
        </div>
      </div>

      <div style={{ padding: '16px' }}>
        {/* AI Chat Interface */}
        {showAIChat && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(56, 158, 13, 0.1) 100%)',
            border: '1px solid rgba(82, 196, 26, 0.2)',
            borderRadius: '16px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '16px'
            }}>
              <span style={{ fontSize: '20px' }}>💬</span>
              <h3 style={{ 
                fontSize: '18px', 
                fontWeight: '600',
                color: '#262626',
                margin: 0
              }}>
                AI Calendar Assistant
              </h3>
            </div>
            
            <p style={{ 
              fontSize: '14px', 
              color: '#8C8C8C', 
              margin: '0 0 16px 0',
              lineHeight: '1.4'
            }}>
              Tell me your goal and I'll break it down into specific actionable tasks and schedule them strategically around your routine.
            </p>
            
            {/* Chat History */}
            <div style={{
              maxHeight: '200px',
              overflowY: 'auto',
              marginBottom: '16px',
              padding: '12px',
              background: 'rgba(255, 255, 255, 0.7)',
              borderRadius: '12px',
              border: '1px solid rgba(82, 196, 26, 0.15)'
            }}>
              {chatHistory.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#8C8C8C', fontSize: '14px' }}>
                  Start a conversation with your AI calendar assistant...
                </div>
              ) : (
                chatHistory.map((msg, idx) => (
                  <div key={idx} style={{
                    marginBottom: '12px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: msg.role === 'user' 
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                      : 'rgba(82, 196, 26, 0.1)',
                    color: msg.role === 'user' ? 'white' : '#262626',
                    fontSize: '14px',
                    lineHeight: '1.4'
                  }}>
                    <strong>{msg.role === 'user' ? '🙋‍♂️ You: ' : '🤖 AI: '}</strong>
                    {msg.content}
                  </div>
                ))
              )}
            </div>
            
            {/* Chat Input */}
            <div style={{ display: 'flex', gap: '12px' }}>
              <input
                type="text"
                placeholder="e.g., 'I need to focus on lead generation today' or 'Help me build a content strategy'"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid rgba(82, 196, 26, 0.3)',
                  borderRadius: '8px',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <button 
                onClick={handleSendMessage}
                disabled={!chatMessage.trim()}
                style={{
                  padding: '12px 20px',
                  background: chatMessage.trim() 
                    ? 'linear-gradient(135deg, #52C41A 0%, #389E0D 100%)' 
                    : 'rgba(140, 140, 140, 0.2)',
                  color: chatMessage.trim() ? 'white' : '#8C8C8C',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: chatMessage.trim() ? 'pointer' : 'not-allowed'
                }}
              >
                Send 💬
              </button>
            </div>
          </div>
        )}

        {/* Daily Routine Settings */}
        {showRoutineSettings && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(250, 173, 20, 0.1) 0%, rgba(212, 136, 6, 0.1) 100%)',
            border: '1px solid rgba(250, 173, 20, 0.2)',
            borderRadius: '16px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '16px'
            }}>
              <span style={{ fontSize: '20px' }}>⚙️</span>
              <h3 style={{ 
                fontSize: '18px', 
                fontWeight: '600',
                color: '#262626',
                margin: 0
              }}>
                Daily Routine Settings
              </h3>
            </div>
            
            <p style={{ 
              fontSize: '14px', 
              color: '#8C8C8C', 
              margin: '0 0 16px 0',
              lineHeight: '1.4'
            }}>
              Help AI understand your daily routine so it can schedule tasks at optimal times.
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Wake Up Time</label>
                <input
                  type="time"
                  value={routineSettings.wake_up_time}
                  onChange={(e) => setRoutineSettings({...routineSettings, wake_up_time: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Sleep Time</label>
                <input
                  type="time"
                  value={routineSettings.sleep_time}
                  onChange={(e) => setRoutineSettings({...routineSettings, sleep_time: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Gym Time</label>
                <input
                  type="time"
                  value={routineSettings.gym_time}
                  onChange={(e) => setRoutineSettings({...routineSettings, gym_time: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Lunch Time</label>
                <input
                  type="time"
                  value={routineSettings.lunch_time}
                  onChange={(e) => setRoutineSettings({...routineSettings, lunch_time: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Dinner Time</label>
                <input
                  type="time"
                  value={routineSettings.dinner_time}
                  onChange={(e) => setRoutineSettings({...routineSettings, dinner_time: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Work Hours</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    type="time"
                    value={routineSettings.work_start}
                    onChange={(e) => setRoutineSettings({...routineSettings, work_start: e.target.value})}
                    style={{
                      flex: 1,
                      padding: '10px',
                      border: '1px solid rgba(250, 173, 20, 0.3)',
                      borderRadius: '8px',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  />
                  <span style={{ color: '#8C8C8C', fontSize: '14px' }}>to</span>
                  <input
                    type="time"
                    value={routineSettings.work_end}
                    onChange={(e) => setRoutineSettings({...routineSettings, work_end: e.target.value})}
                    style={{
                      flex: 1,
                      padding: '10px',
                      border: '1px solid rgba(250, 173, 20, 0.3)',
                      borderRadius: '8px',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  />
                </div>
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Break Duration (minutes)</label>
                <select
                  value={routineSettings.break_duration}
                  onChange={(e) => setRoutineSettings({...routineSettings, break_duration: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                >
                  <option value={10}>10 minutes</option>
                  <option value={15}>15 minutes</option>
                  <option value={20}>20 minutes</option>
                  <option value={30}>30 minutes</option>
                </select>
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#262626', marginBottom: '6px' }}>Focus Block (minutes)</label>
                <select
                  value={routineSettings.focus_block_duration}
                  onChange={(e) => setRoutineSettings({...routineSettings, focus_block_duration: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(250, 173, 20, 0.3)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                >
                  <option value={60}>1 hour</option>
                  <option value={90}>1.5 hours</option>
                  <option value={120}>2 hours</option>
                  <option value={180}>3 hours</option>
                </select>
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                onClick={handleSaveRoutineSettings}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'linear-gradient(135deg, #FAAD14 0%, #D48806 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                ⚙️ Save Routine Settings
              </button>
              <button 
                onClick={() => setShowRoutineSettings(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'rgba(140, 140, 140, 0.1)',
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

        {/* AI Planner Form */}
        {showAIPlanner && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
            border: '1px solid rgba(102, 126, 234, 0.2)',
            borderRadius: '16px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '16px'
            }}>
              <span style={{ fontSize: '20px' }}>🤖</span>
              <h3 style={{ 
                fontSize: '18px', 
                fontWeight: '600',
                color: '#262626',
                margin: 0
              }}>
                AI Task Scheduler
              </h3>
            </div>
            
            <input
              type="text"
              placeholder="What do you need to work on?"
              value={aiPlannerData.title}
              onChange={(e) => setAiPlannerData({...aiPlannerData, title: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid rgba(102, 126, 234, 0.3)',
                borderRadius: '8px',
                marginBottom: '12px',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            
            <textarea
              placeholder="Any additional details? (optional)"
              value={aiPlannerData.description}
              onChange={(e) => setAiPlannerData({...aiPlannerData, description: e.target.value})}
              rows={3}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid rgba(102, 126, 234, 0.3)',
                borderRadius: '8px',
                marginBottom: '12px',
                fontSize: '14px',
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'inherit'
              }}
            />
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <select
                value={aiPlannerData.duration_minutes}
                onChange={(e) => setAiPlannerData({...aiPlannerData, duration_minutes: parseInt(e.target.value)})}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                  borderRadius: '8px',
                  fontSize: '14px',
                  outline: 'none'
                }}
              >
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
                <option value={90}>1.5 hours</option>
                <option value={120}>2 hours</option>
                <option value={180}>3 hours</option>
              </select>

              <select
                value={aiPlannerData.priority}
                onChange={(e) => setAiPlannerData({...aiPlannerData, priority: e.target.value})}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                  borderRadius: '8px',
                  fontSize: '14px',
                  outline: 'none'
                }}
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
              </select>
            </div>

            {goals.length > 0 && (
              <select
                value={aiPlannerData.goal_id || ''}
                onChange={(e) => setAiPlannerData({...aiPlannerData, goal_id: e.target.value ? parseInt(e.target.value) : undefined})}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  fontSize: '14px',
                  outline: 'none'
                }}
              >
                <option value="">No goal association</option>
                {goals.map(goal => (
                  <option key={goal.id} value={goal.id}>
                    🎯 {goal.title}
                  </option>
                ))}
              </select>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                onClick={handleAISchedule}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                🤖 Let AI Schedule This
              </button>
              <button 
                onClick={() => setShowAIPlanner(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'rgba(140, 140, 140, 0.1)',
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

        {/* Today's Schedule */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>📅</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              {new Date(selectedDate).toLocaleDateString('en-US', { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric' 
              })}
            </h2>
          </div>

          {events.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {events.map((event) => (
                <div
                  key={event.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '16px',
                    background: 'rgba(102, 126, 234, 0.05)',
                    borderRadius: '12px',
                    border: `2px solid ${getPriorityColor(event.priority)}33`
                  }}
                >
                  <div style={{ fontSize: '24px' }}>{getEventTypeEmoji(event.event_type)}</div>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ 
                      margin: '0 0 4px 0', 
                      fontSize: '16px', 
                      fontWeight: '600', 
                      color: '#262626' 
                    }}>
                      {event.title}
                    </h3>
                    {event.description && (
                      <p style={{ 
                        margin: '0 0 8px 0', 
                        fontSize: '14px', 
                        color: '#8C8C8C',
                        lineHeight: '1.4'
                      }}>
                        {event.description}
                      </p>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: '#8C8C8C' }}>
                      <span>🕐 {formatTime(event.start_time)} - {formatTime(event.end_time)}</span>
                      <span style={{ 
                        background: getPriorityColor(event.priority),
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: '500'
                      }}>
                        {event.priority.toUpperCase()}
                      </span>
                      {/* @ts-ignore */}
                      {event.is_synced && (
                        <span style={{ 
                          background: '#52C41A',
                          color: 'white',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '10px',
                          fontWeight: '500',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '2px'
                        }}>
                          📅 SYNCED
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <button
                      onClick={() => handleEditEvent(event)}
                      style={{
                        background: 'rgba(74, 144, 226, 0.1)',
                        color: '#4A90E2',
                        border: '1px solid rgba(74, 144, 226, 0.2)',
                        borderRadius: '6px',
                        padding: '6px 12px',
                        fontSize: '12px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleDeleteEvent(event.id, event.title)}
                      style={{
                        background: 'rgba(255, 77, 79, 0.1)',
                        color: '#FF4D4F',
                        border: '1px solid rgba(255, 77, 79, 0.2)',
                        borderRadius: '6px',
                        padding: '6px 12px',
                        fontSize: '12px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📅</div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: '600', color: '#262626' }}>
                No Events Scheduled
              </h3>
              <p style={{ margin: '0 0 24px 0', fontSize: '14px', color: '#8C8C8C' }}>
                Use AI to schedule your tasks automatically
              </p>
              <button 
                onClick={() => setShowAIPlanner(true)}
                style={{
                  padding: '12px 24px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                🤖 Start AI Scheduling
              </button>
            </div>
          )}
        </div>

        {/* AI Goal-Based Daily Scheduler */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(114, 46, 209, 0.1) 100%)',
          border: '1px solid rgba(82, 196, 26, 0.2)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>🎯</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              Daily Goal Scheduler
            </h2>
          </div>

          <p style={{ fontSize: '14px', color: '#8C8C8C', margin: '0 0 16px 0' }}>
            Let AI automatically schedule work sessions for your active goals based on your calendar availability.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button 
              onClick={handleBulkScheduleFromGoals}
              style={{
                width: '100%',
                padding: '14px',
                background: 'linear-gradient(135deg, #52C41A 0%, #722ED1 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              🤖 Schedule Goal Work Sessions
            </button>

            <button 
              onClick={handleOptimizeWeek}
              style={{
                width: '100%',
                padding: '12px',
                background: 'rgba(82, 196, 26, 0.1)',
                color: '#52C41A',
                border: '1px solid rgba(82, 196, 26, 0.3)',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              📊 Optimize This Week
            </button>
          </div>
        </div>

        {/* AI Insights */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          border: '1px solid rgba(102, 126, 234, 0.2)',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '20px' }}>🤖</span>
            <h2 style={{ 
              fontSize: '18px', 
              fontWeight: '600',
              color: '#262626',
              margin: 0
            }}>
              AI Schedule Insights
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.5)',
              borderRadius: '12px',
              padding: '12px'
            }}>
              <p style={{ fontSize: '14px', color: '#262626', margin: 0 }}>
                <strong>Optimal Focus Time:</strong> Your peak productivity hours are 9-11 AM. AI will prioritize important tasks during this window.
              </p>
            </div>
            <div style={{
              background: 'rgba(255, 255, 255, 0.5)',
              borderRadius: '12px',
              padding: '12px'
            }}>
              <p style={{ fontSize: '14px', color: '#262626', margin: 0 }}>
                <strong>Goal Progress:</strong> You have {goals.length} active goals. AI can automatically schedule tasks to help you achieve them faster.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}