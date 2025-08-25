import axios from 'axios';

// API Configuration  
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('aurora_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token
      localStorage.removeItem('aurora_access_token');
      localStorage.removeItem('aurora_refresh_token');
      
      // Try to refresh token if available
      const refreshToken = localStorage.getItem('aurora_refresh_token');
      if (refreshToken) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('aurora_access_token', data.access_token);
            localStorage.setItem('aurora_refresh_token', data.refresh_token);
            
            // Retry the original request with new token
            error.config.headers.Authorization = `Bearer ${data.access_token}`;
            return api.request(error.config);
          }
        } catch (refreshError) {
          console.error('Failed to refresh auth token:', refreshError);
        }
      }
      
      // Redirect to login if refresh failed
      // Use history API to avoid full page reload
      if (typeof window !== 'undefined' && window.history) {
        window.history.pushState(null, '', '/login');
        window.dispatchEvent(new PopStateEvent('popstate'));
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (emailOrUsername: string, password: string) => {
    const response = await api.post('/api/auth/token', {
      username: emailOrUsername, // Backend uses username field for login
      password,
    }, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      transformRequest: [(data) => {
        const params = new URLSearchParams();
        params.append('username', data.username);
        params.append('password', data.password);
        return params;
      }]
    });
    return response.data;
  },

  register: async (email: string, password: string, username: string) => {
    const response = await api.post('/api/auth/register', {
      email,
      password,
      username,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/users/me');
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (message: string, context?: any) => {
    const response = await api.post('/api/chat/message', {
      message,
      context,
    });
    return response.data;
  },

  getMessages: async (limit: number = 50) => {
    const response = await api.get(`/api/chat/messages?limit=${limit}`);
    return response.data;
  },

  quickCommand: async (command: string) => {
    const response = await api.post('/api/chat/quick-command', {
      command,
    });
    return response.data;
  },
};

// Goals API
export const goalsAPI = {
  getGoals: async () => {
    const response = await api.get('/api/goals/');
    return response.data;
  },

  createGoal: async (goalData: {
    title: string;
    description?: string;
    target_date?: string;
    category: string;
  }) => {
    const response = await api.post('/api/goals/', goalData);
    return response.data;
  },

  updateGoal: async (goalId: number, goalData: any) => {
    const response = await api.put(`/api/goals/${goalId}/`, goalData);
    return response.data;
  },

  deleteGoal: async (goalId: number) => {
    const response = await api.delete(`/api/goals/${goalId}/`);
    return response.data;
  },

  updateProgress: async (goalId: number, progress: number, notes?: string) => {
    const response = await api.post(`/api/goals/${goalId}/progress`, {
      progress,
      notes,
    });
    return response.data;
  },

  getInsights: async (goalId: number) => {
    const response = await api.get(`/api/goals/${goalId}/insights`);
    return response.data;
  },

  getAnalytics: async () => {
    const response = await api.get('/api/goals/analytics/overview');
    return response.data;
  },
};

// Tasks API
export const tasksAPI = {
  getTasks: async (status?: string, priority?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    
    const response = await api.get(`/api/tasks?${params.toString()}`);
    return response.data;
  },

  createTask: async (taskData: {
    title: string;
    description?: string;
    due_date?: string;
    priority?: string;
    goal_id?: number;
  }) => {
    const response = await api.post('/api/tasks', taskData);
    return response.data;
  },

  updateTask: async (taskId: number, taskData: any) => {
    const response = await api.put(`/api/tasks/${taskId}`, taskData);
    return response.data;
  },

  completeTask: async (taskId: number) => {
    const response = await api.post(`/api/tasks/${taskId}/complete`);
    return response.data;
  },

  deleteTask: async (taskId: number) => {
    const response = await api.delete(`/api/tasks/${taskId}`);
    return response.data;
  },

  breakdownGoal: async (goalId: number) => {
    const response = await api.post(`/api/goals/${goalId}/breakdown`);
    return response.data;
  },

  getNextSuggestion: async () => {
    const response = await api.get('/api/tasks/suggestions/next');
    return response.data;
  },
};

// Mood API
export const moodAPI = {
  saveMood: async (moodData: {
    mood_score: number;
    energy_level: number;
    stress_level: number;
    notes?: string;
  }) => {
    // Convert mood_score to mood_level for backend compatibility
    const backendData = {
      mood_level: moodData.mood_score,
      energy_level: moodData.energy_level,
      stress_level: moodData.stress_level,
      notes: moodData.notes
    };
    const response = await api.post('/api/mood/checkin', backendData);
    return response.data;
  },

  getMoodHistory: async (days: number = 30) => {
    const response = await api.get(`/api/mood/history?days=${days}`);
    return response.data;
  },

  getMoodAnalytics: async (period: string = 'week') => {
    const response = await api.get(`/api/mood/analytics?period=${period}`);
    return response.data;
  },

  getBurnoutAssessment: async () => {
    const response = await api.get('/api/mood/burnout-assessment');
    return response.data;
  },
};

// Calendar API
export const calendarAPI = {
  getEvents: async (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get(`/api/calendar/events?${params.toString()}`);
    return response.data;
  },

  createEvent: async (eventData: {
    title: string;
    description?: string;
    start_time: string;
    end_time: string;
    location?: string;
  }) => {
    const response = await api.post('/api/calendar/events', eventData);
    return response.data;
  },

  updateEvent: async (eventId: number, eventData: any) => {
    const response = await api.put(`/api/calendar/events/${eventId}`, eventData);
    return response.data;
  },

  deleteEvent: async (eventId: number) => {
    const response = await api.delete(`/api/calendar/events/${eventId}`);
    return response.data;
  },

  syncWithGoogle: async () => {
    const response = await api.post('/api/calendar/sync');
    return response.data;
  },

  connectGoogle: async () => {
    const response = await api.get('/api/calendar/connect-google');
    return response.data;
  },

  getConnectionStatus: async () => {
    const response = await api.get('/api/calendar/connection-status');
    return response.data;
  },
};

// AI Calendar API
export const aiCalendarAPI = {
  generateSchedule: async (date: string) => {
    const response = await api.post('/api/ai-calendar/generate-hourly-schedule', {
      date,
    });
    return response.data;
  },

  optimizeWeek: async (weekStartDate: string) => {
    const response = await api.post('/api/ai-calendar/optimize-weekly', {
      week_start_date: weekStartDate,
    });
    return response.data;
  },

  bulkScheduleGoals: async (daysAhead: number = 7) => {
    const response = await api.post(`/api/ai-calendar/bulk-schedule-from-goals?days_ahead=${daysAhead}`);
    return response.data;
  },

  getProductivityInsights: async (days: number = 7) => {
    const response = await api.get(`/api/ai-calendar/productivity-insights?days=${days}`);
    return response.data;
  },

  createSmartEvent: async (eventData: {
    title: string;
    description?: string;
    duration_minutes: number;
    goal_id?: number;
    suggested_time?: string;
  }) => {
    const response = await api.post('/api/ai-calendar/smart-create', eventData);
    return response.data;
  },
};

// User Profile API
export const userAPI = {
  getProfile: async () => {
    const response = await api.get('/api/users/me');
    return response.data;
  },

  updateProfile: async (profileData: any) => {
    const response = await api.put('/api/users/me', profileData);
    return response.data;
  },
};

// Utility functions
export const setAuthToken = (token: string) => {
  localStorage.setItem('aurora_access_token', token);
};

export const clearAuthToken = () => {
  localStorage.removeItem('aurora_access_token');
  localStorage.removeItem('aurora_refresh_token');
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('aurora_access_token');
};

export default api;