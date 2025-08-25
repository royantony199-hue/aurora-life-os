import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { authAPI, setAuthToken, clearAuthToken, isAuthenticated } from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, password: string, username: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('aurora_access_token');
    if (token) {
      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
        setError(null);
      } catch (error: any) {
        console.error('Auth check failed:', error);
        // Token invalid, clear it
        clearAuthToken();
        setUser(null);
        
        // Don't show error for auth check failures on startup
        if (error.response?.status !== 401) {
          setError('Authentication verification failed');
        }
      }
    }
    setIsLoading(false);
  };

  const login = async (username: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      
      const response = await authAPI.login(username, password);
      setAuthToken(response.access_token);
      
      // Get user data
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Login failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, username: string) => {
    try {
      setError(null);
      setIsLoading(true);
      
      await authAPI.register(email, password, username);
      
      // Auto-login after registration
      await login(username, password);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Registration failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    error,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};