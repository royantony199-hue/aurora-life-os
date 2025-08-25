import React, { Component, ReactNode } from 'react';

interface ApiErrorBoundaryProps {
  children: ReactNode;
  onError?: (error: Error) => void;
}

interface ApiErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  isNetworkError: boolean;
  isAuthError: boolean;
  retryCount: number;
}

export class ApiErrorBoundary extends Component<ApiErrorBoundaryProps, ApiErrorBoundaryState> {
  private maxRetries = 3;

  constructor(props: ApiErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      isNetworkError: false,
      isAuthError: false,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ApiErrorBoundaryState> {
    // Analyze error type
    const isNetworkError = error.message.includes('fetch') || 
                          error.message.includes('network') ||
                          error.message.includes('Failed to fetch');
    
    const isAuthError = error.message.includes('401') || 
                       error.message.includes('Unauthorized') ||
                       error.message.includes('authentication');

    return {
      hasError: true,
      error,
      isNetworkError,
      isAuthError
    };
  }

  componentDidCatch(error: Error) {
    // Call error handler if provided
    this.props.onError?.(error);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error caught:', error);
    }
  }

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: undefined,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  private handleLogin = () => {
    // Redirect to login page
    window.location.href = '/login';
  };

  private renderErrorUI() {
    const { error, isNetworkError, isAuthError, retryCount } = this.state;

    if (isAuthError) {
      return (
        <div className="flex flex-col items-center justify-center p-6 bg-yellow-50 border border-yellow-200 rounded-lg m-4">
          <div className="text-yellow-600 text-4xl mb-3">🔒</div>
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Authentication Required
          </h3>
          <p className="text-yellow-700 text-center mb-4">
            Your session has expired. Please log in again to continue.
          </p>
          <button
            onClick={this.handleLogin}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Login
          </button>
        </div>
      );
    }

    if (isNetworkError) {
      return (
        <div className="flex flex-col items-center justify-center p-6 bg-orange-50 border border-orange-200 rounded-lg m-4">
          <div className="text-orange-600 text-4xl mb-3">🌐</div>
          <h3 className="text-lg font-semibold text-orange-800 mb-2">
            Connection Problem
          </h3>
          <p className="text-orange-700 text-center mb-4">
            Unable to connect to our servers. Please check your internet connection and try again.
          </p>
          <div className="flex gap-2">
            {retryCount < this.maxRetries && (
              <button
                onClick={this.handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Retry ({this.maxRetries - retryCount} left)
              </button>
            )}
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    // Generic API error
    return (
      <div className="flex flex-col items-center justify-center p-6 bg-red-50 border border-red-200 rounded-lg m-4">
        <div className="text-red-600 text-4xl mb-3">⚠️</div>
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Something Went Wrong
        </h3>
        <p className="text-red-700 text-center mb-4">
          An unexpected error occurred while processing your request.
        </p>
        <div className="flex gap-2">
          {retryCount < this.maxRetries && (
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          )}
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
          >
            Refresh Page
          </button>
        </div>
        {process.env.NODE_ENV === 'development' && error && (
          <details className="mt-4 max-w-full">
            <summary className="cursor-pointer text-sm text-gray-600">Error Details</summary>
            <pre className="text-xs bg-gray-100 p-2 rounded mt-2 overflow-auto max-h-32">
              {error.toString()}
            </pre>
          </details>
        )}
      </div>
    );
  }

  render() {
    if (this.state.hasError) {
      return this.renderErrorUI();
    }

    return this.props.children;
  }
}