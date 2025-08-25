import React, { useState } from 'react';
import { Loader } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface LoginFormProps {
  onToggleMode: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onToggleMode }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, clearError } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    if (!username || !password) return;

    try {
      await login(username, password);
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  return (
    <>
      <div className="mobile-auth-logo">
        <span>A</span>
      </div>
      <h1 className="mobile-auth-title">Welcome Back</h1>
      <p className="mobile-auth-subtitle">Sign in to Aurora Life OS</p>
      <div>
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mobile-error">
              {error}
            </div>
          )}
          
          <div className="mobile-form-group">
            <label htmlFor="username" className="mobile-form-label">
              Username or Email
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username or email"
              className="mobile-input"
              required
            />
          </div>
          
          <div className="mobile-form-group">
            <label htmlFor="password" className="mobile-form-label">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="mobile-input"
              required
            />
          </div>
          
          <button
            type="submit"
            className="mobile-button"
            disabled={isLoading || !username || !password}
          >
            {isLoading ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
          
          <div className="text-center mt-6">
            <button
              type="button"
              onClick={onToggleMode}
              className="text-[#667eea] hover:underline text-sm font-medium"
            >
              Don't have an account? Sign up
            </button>
          </div>
        </form>
      </div>
    </>
  );
};