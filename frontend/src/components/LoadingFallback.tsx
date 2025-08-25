import React from 'react';

interface LoadingFallbackProps {
  title: string;
  description: string;
  icon?: string;
}

export function LoadingFallback({ title, description, icon = "⏳" }: LoadingFallbackProps) {
  return (
    <div className="mobile-card text-center py-8">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
      <p className="text-sm text-gray-500">{description}</p>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: string;
  actionText?: string;
  onAction?: () => void;
}

export function EmptyState({ title, description, icon = "📝", actionText, onAction }: EmptyStateProps) {
  return (
    <div className="mobile-card text-center py-8">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mobile-button mobile-button-small"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}