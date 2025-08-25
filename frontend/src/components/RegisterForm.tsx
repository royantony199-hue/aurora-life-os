import React, { useState } from 'react';
import { Loader } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface RegisterFormProps {
  onToggleMode: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onToggleMode }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { register, isLoading, error, clearError } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    if (!username || !email || !password) return;
    
    if (password !== confirmPassword) {
      return;
    }

    try {
      await register(email, password, username);
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  return (
    <>
      <div className="mobile-auth-logo">
        <span>A</span>
      </div>
      <h1 className="mobile-auth-title">Create Account</h1>
      <p className="mobile-auth-subtitle">Join Aurora Life OS</p>
      <div>
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mobile-error">
              {error}
            </div>
          )}
          
          <div className="mobile-form-group">
            <label htmlFor="username" className="mobile-form-label">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Your username"
              className="mobile-input"
              required
            />
          </div>
          
          <div className="mobile-form-group">
            <label htmlFor="email" className="mobile-form-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
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
              placeholder="Create a password"
              className="mobile-input"
              required
            />
          </div>
          
          <div className="mobile-form-group">
            <label htmlFor="confirmPassword" className="mobile-form-label">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              className="mobile-input"
              required
            />
          </div>
          
          {password && confirmPassword && password !== confirmPassword && (
            <div className="mobile-error">Passwords do not match</div>
          )}
          
          <button
            type="submit"
            className="mobile-button"
            disabled={isLoading || !username || !email || !password || password !== confirmPassword}
          >
            {isLoading ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
          
          <div className="text-center mt-6">
            <button
              type="button"
              onClick={onToggleMode}
              className="text-[#667eea] hover:underline text-sm font-medium"
            >
              Already have an account? Sign in
            </button>
          </div>
        </form>
      </div>
    </>
  );
};