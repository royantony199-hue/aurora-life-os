import React, { createContext, useContext, useReducer, useCallback, useEffect, ReactNode } from 'react';
import { CalendarEvent, Goal, RoutineSettings } from '../components/calendar/types';

// State interface
interface CalendarState {
  // Data
  events: CalendarEvent[];
  goals: Goal[];
  
  // UI State
  isLoading: boolean;
  selectedDate: string;
  
  // Modal States
  showAIPlanner: boolean;
  showAIChat: boolean;
  showRoutineSettings: boolean;
  
  // Settings
  routineSettings: RoutineSettings;
  
  // Error State
  error: string | null;
}

// Actions
type CalendarAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_EVENTS'; payload: CalendarEvent[] }
  | { type: 'SET_GOALS'; payload: Goal[] }
  | { type: 'SET_SELECTED_DATE'; payload: string }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SHOW_AI_PLANNER'; payload: boolean }
  | { type: 'SHOW_AI_CHAT'; payload: boolean }
  | { type: 'SHOW_ROUTINE_SETTINGS'; payload: boolean }
  | { type: 'SET_ROUTINE_SETTINGS'; payload: RoutineSettings }
  | { type: 'ADD_EVENT'; payload: CalendarEvent }
  | { type: 'UPDATE_EVENT'; payload: { id: number; event: Partial<CalendarEvent> } }
  | { type: 'DELETE_EVENT'; payload: number }
  | { type: 'RESET_ERROR' };

// Initial state
const initialState: CalendarState = {
  events: [],
  goals: [],
  isLoading: false,
  selectedDate: new Date().toISOString().split('T')[0],
  showAIPlanner: false,
  showAIChat: false,
  showRoutineSettings: false,
  routineSettings: {
    wake_up_time: '07:00',
    sleep_time: '23:00',
    gym_time: '18:00',
    lunch_time: '13:00',
    dinner_time: '20:00',
    work_start: '09:00',
    work_end: '18:00',
    break_duration: 15,
    focus_block_duration: 120
  },
  error: null
};

// Reducer
function calendarReducer(state: CalendarState, action: CalendarAction): CalendarState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
      
    case 'SET_EVENTS':
      return { ...state, events: action.payload, isLoading: false, error: null };
      
    case 'SET_GOALS':
      return { ...state, goals: action.payload };
      
    case 'SET_SELECTED_DATE':
      return { ...state, selectedDate: action.payload };
      
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
      
    case 'SHOW_AI_PLANNER':
      return { ...state, showAIPlanner: action.payload };
      
    case 'SHOW_AI_CHAT':
      return { ...state, showAIChat: action.payload };
      
    case 'SHOW_ROUTINE_SETTINGS':
      return { ...state, showRoutineSettings: action.payload };
      
    case 'SET_ROUTINE_SETTINGS':
      return { ...state, routineSettings: action.payload };
      
    case 'ADD_EVENT':
      return { 
        ...state, 
        events: [...state.events, action.payload].sort((a, b) => 
          new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        )
      };
      
    case 'UPDATE_EVENT':
      return {
        ...state,
        events: state.events.map(event =>
          event.id === action.payload.id
            ? { ...event, ...action.payload.event }
            : event
        )
      };
      
    case 'DELETE_EVENT':
      return {
        ...state,
        events: state.events.filter(event => event.id !== action.payload)
      };
      
    case 'RESET_ERROR':
      return { ...state, error: null };
      
    default:
      return state;
  }
}

// Context
interface CalendarContextType {
  state: CalendarState;
  dispatch: React.Dispatch<CalendarAction>;
  
  // Actions
  loadCalendarData: () => Promise<void>;
  createEvent: (eventData: any) => Promise<boolean>;
  updateEvent: (id: number, eventData: any) => Promise<boolean>;
  deleteEvent: (id: number) => Promise<boolean>;
  syncWithGoogle: () => Promise<boolean>;
  bulkScheduleFromGoals: () => Promise<boolean>;
  optimizeWeek: () => Promise<boolean>;
}

const CalendarContext = createContext<CalendarContextType | undefined>(undefined);

// Provider component
interface CalendarProviderProps {
  children: ReactNode;
}

export const CalendarProvider: React.FC<CalendarProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(calendarReducer, initialState);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('routineSettings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        dispatch({ type: 'SET_ROUTINE_SETTINGS', payload: settings });
      } catch (error) {
        console.error('Failed to load routine settings:', error);
      }
    }
  }, []);

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('routineSettings', JSON.stringify(state.routineSettings));
  }, [state.routineSettings]);

  // API Helper function
  const apiCall = useCallback(async (
    url: string, 
    options: RequestInit = {}
  ): Promise<Response> => {
    const token = localStorage.getItem('aurora_access_token');
    return fetch(`http://localhost:8001${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });
  }, []);

  // Load calendar data
  const loadCalendarData = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      // Load events
      const eventsResponse = await apiCall(
        `/api/calendar/events?start_date=${state.selectedDate}&end_date=${state.selectedDate}`
      );
      
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        dispatch({ type: 'SET_EVENTS', payload: eventsData });
      } else {
        throw new Error('Failed to load events');
      }

      // Load goals
      const goalsResponse = await apiCall('/api/goals/');
      if (goalsResponse.ok) {
        const goalsData = await goalsResponse.json();
        dispatch({ type: 'SET_GOALS', payload: goalsData });
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load calendar data';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
    }
  }, [state.selectedDate, apiCall]);

  // Create event
  const createEvent = useCallback(async (eventData: any): Promise<boolean> => {
    try {
      const response = await apiCall('/api/ai-calendar/smart-create', {
        method: 'POST',
        body: JSON.stringify(eventData),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload data
        return true;
      } else {
        throw new Error('Failed to create event');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create event';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return false;
    }
  }, [apiCall, loadCalendarData]);

  // Update event
  const updateEvent = useCallback(async (id: number, eventData: any): Promise<boolean> => {
    try {
      const response = await apiCall(`/api/calendar/events/${id}`, {
        method: 'PUT',
        body: JSON.stringify(eventData),
      });

      if (response.ok) {
        dispatch({ type: 'UPDATE_EVENT', payload: { id, event: eventData } });
        return true;
      } else {
        throw new Error('Failed to update event');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update event';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return false;
    }
  }, [apiCall]);

  // Delete event
  const deleteEvent = useCallback(async (id: number): Promise<boolean> => {
    try {
      const response = await apiCall(`/api/calendar/events/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        dispatch({ type: 'DELETE_EVENT', payload: id });
        return true;
      } else {
        throw new Error('Failed to delete event');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete event';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return false;
    }
  }, [apiCall]);

  // Sync with Google Calendar
  const syncWithGoogle = useCallback(async (): Promise<boolean> => {
    try {
      const response = await apiCall('/api/calendar/sync', {
        method: 'POST',
      });

      if (response.ok) {
        await loadCalendarData(); // Reload after sync
        return true;
      } else {
        throw new Error('Failed to sync with Google Calendar');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to sync calendar';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return false;
    }
  }, [apiCall, loadCalendarData]);

  // Bulk schedule from goals
  const bulkScheduleFromGoals = useCallback(async (): Promise<boolean> => {
    try {
      const response = await apiCall('/api/ai-calendar/bulk-schedule-from-goals', {
        method: 'POST',
        body: JSON.stringify({ days_ahead: 7 }),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload after scheduling
        return true;
      } else {
        throw new Error('Failed to schedule from goals');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to schedule from goals';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return false;
    }
  }, [apiCall, loadCalendarData]);

  // Optimize week
  const optimizeWeek = useCallback(async (): Promise<boolean> => {
    try {
      const response = await apiCall('/api/ai-calendar/weekly-optimize', {
        method: 'POST',
        body: JSON.stringify({ week_start_date: state.selectedDate }),
      });

      if (response.ok) {
        await loadCalendarData(); // Reload after optimization
        return true;
      } else {
        throw new Error('Failed to optimize week');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to optimize week';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return false;
    }
  }, [apiCall, loadCalendarData, state.selectedDate]);

  // Load data when selected date changes
  useEffect(() => {
    loadCalendarData();
  }, [loadCalendarData]);

  const contextValue: CalendarContextType = {
    state,
    dispatch,
    loadCalendarData,
    createEvent,
    updateEvent,
    deleteEvent,
    syncWithGoogle,
    bulkScheduleFromGoals,
    optimizeWeek,
  };

  return (
    <CalendarContext.Provider value={contextValue}>
      {children}
    </CalendarContext.Provider>
  );
};

// Custom hook to use the calendar context
export const useCalendar = (): CalendarContextType => {
  const context = useContext(CalendarContext);
  if (context === undefined) {
    throw new Error('useCalendar must be used within a CalendarProvider');
  }
  return context;
};