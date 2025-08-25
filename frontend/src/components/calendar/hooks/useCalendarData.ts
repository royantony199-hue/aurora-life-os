import { useState, useEffect, useCallback } from 'react';
import { CalendarEvent, Goal } from '../types';

export const useCalendarData = (selectedDate: string) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadCalendarData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Load events for selected date
      const eventsResponse = await fetch(`http://localhost:8001/api/calendar/events?start_date=${selectedDate}&end_date=${selectedDate}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });
      
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        setEvents(eventsData);
      }

      // Load goals
      const goalsResponse = await fetch('http://localhost:8001/api/goals/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });
      
      if (goalsResponse.ok) {
        const goalsData = await goalsResponse.json();
        setGoals(goalsData);
      }
    } catch (error) {
      console.error('Failed to load calendar data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    loadCalendarData();
  }, [loadCalendarData]);

  const syncWithGoogle = useCallback(async () => {
    try {
      const syncResponse = await fetch('http://localhost:8001/api/calendar/sync', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });

      if (syncResponse.ok) {
        await loadCalendarData(); // Reload data after sync
        return { success: true };
      } else {
        throw new Error('Failed to sync with Google Calendar');
      }
    } catch (error) {
      console.error('Failed to sync with Google Calendar:', error);
      return { success: false, error };
    }
  }, [loadCalendarData]);

  const createEvent = useCallback(async (eventData: any) => {
    try {
      const response = await fetch('http://localhost:8001/api/ai-calendar/smart-create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify(eventData),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload data after creating event
        return { success: true };
      } else {
        throw new Error('Failed to create event');
      }
    } catch (error) {
      console.error('Failed to create event:', error);
      return { success: false, error };
    }
  }, [loadCalendarData]);

  const updateEvent = useCallback(async (eventId: number, eventData: any) => {
    try {
      const response = await fetch(`http://localhost:8001/api/calendar/events/${eventId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify(eventData),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload data after updating event
        return { success: true };
      } else {
        throw new Error('Failed to update event');
      }
    } catch (error) {
      console.error('Failed to update event:', error);
      return { success: false, error };
    }
  }, [loadCalendarData]);

  const deleteEvent = useCallback(async (eventId: number) => {
    try {
      const response = await fetch(`http://localhost:8001/api/calendar/events/${eventId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
      });

      if (response.ok) {
        await loadCalendarData(); // Reload data after deleting event
        return { success: true };
      } else {
        throw new Error('Failed to delete event');
      }
    } catch (error) {
      console.error('Failed to delete event:', error);
      return { success: false, error };
    }
  }, [loadCalendarData]);

  const bulkScheduleFromGoals = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8001/api/ai-calendar/bulk-schedule-from-goals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify({ days_ahead: 7 }),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload data after bulk scheduling
        return { success: true };
      } else {
        throw new Error('Failed to bulk schedule from goals');
      }
    } catch (error) {
      console.error('Failed to bulk schedule from goals:', error);
      return { success: false, error };
    }
  }, [loadCalendarData]);

  const optimizeWeek = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8001/api/ai-calendar/weekly-optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aurora_access_token')}`,
        },
        body: JSON.stringify({ week_start_date: selectedDate }),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload data after optimization
        return { success: true };
      } else {
        throw new Error('Failed to optimize week');
      }
    } catch (error) {
      console.error('Failed to optimize week:', error);
      return { success: false, error };
    }
  }, [loadCalendarData, selectedDate]);

  return {
    events,
    goals,
    isLoading,
    loadCalendarData,
    syncWithGoogle,
    createEvent,
    updateEvent,
    deleteEvent,
    bulkScheduleFromGoals,
    optimizeWeek
  };
};