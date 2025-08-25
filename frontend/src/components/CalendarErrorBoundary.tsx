import React from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface CalendarErrorFallbackProps {
  error?: Error;
  retry?: () => void;
}

const CalendarErrorFallback: React.FC<CalendarErrorFallbackProps> = ({ error, retry }) => (
  <div className="flex flex-col items-center justify-center p-8 bg-red-50 border border-red-200 rounded-lg m-4">
    <div className="text-red-600 text-6xl mb-4">📅</div>
    <h3 className="text-lg font-semibold text-red-800 mb-2">
      Calendar Temporarily Unavailable
    </h3>
    <p className="text-red-600 text-center mb-4 max-w-md">
      We're having trouble loading your calendar. This might be due to a connection issue or temporary problem with our servers.
    </p>
    <div className="flex gap-2">
      <button
        onClick={retry}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        Try Again
      </button>
      <button
        onClick={() => window.location.reload()}
        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
      >
        Refresh Page
      </button>
    </div>
    {process.env.NODE_ENV === 'development' && error && (
      <details className="mt-4 max-w-full">
        <summary className="cursor-pointer text-sm text-gray-600">Technical Details</summary>
        <pre className="text-xs bg-gray-100 p-2 rounded mt-2 overflow-auto">
          {error.toString()}
        </pre>
      </details>
    )}
  </div>
);

interface CalendarErrorBoundaryProps {
  children: React.ReactNode;
}

export const CalendarErrorBoundary: React.FC<CalendarErrorBoundaryProps> = ({ children }) => {
  return (
    <ErrorBoundary fallback={<CalendarErrorFallback />}>
      {children}
    </ErrorBoundary>
  );
};