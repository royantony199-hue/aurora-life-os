import React, { memo, useMemo } from 'react';
import { CalendarEvent, Goal } from './types';
import { useOptimizedCallback } from '../../hooks/useOptimizedCallback';

interface CalendarEventListProps {
  events: CalendarEvent[];
  goals: Goal[];
  selectedDate: string;
  onEditEvent: (event: CalendarEvent) => void;
  onDeleteEvent: (eventId: number) => void;
}

// Memoized individual event component to prevent unnecessary re-renders
const EventItem = memo<{
  event: CalendarEvent;
  goalTitle: string;
  onEdit: (event: CalendarEvent) => void;
  onDelete: (eventId: number) => void;
}>(({ event, goalTitle, onEdit, onDelete }) => {
  const getEventColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return '#ff6b6b';
      case 'medium': return '#4ecdc4';
      case 'low': return '#95e1d3';
      default: return '#e0e0e0';
    }
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  // Optimized callbacks to prevent parent re-renders
  const handleEdit = useOptimizedCallback(() => onEdit(event), [event, onEdit]);
  const handleDelete = useOptimizedCallback(() => onDelete(event.id), [event.id, onDelete]);

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '16px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        position: 'relative'
      }}
    >
      {/* Priority indicator */}
      <div
        style={{
          position: 'absolute',
          left: '0',
          top: '0',
          bottom: '0',
          width: '4px',
          backgroundColor: getEventColor(event.priority),
          borderTopLeftRadius: '8px',
          borderBottomLeftRadius: '8px'
        }}
      />
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <h4 style={{
              fontSize: '16px',
              fontWeight: '600',
              margin: '0',
              color: '#333'
            }}>
              {event.title}
            </h4>
            
            <span style={{
              fontSize: '12px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: getEventColor(event.priority),
              color: 'white',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              {event.priority}
            </span>
            
            {event.is_synced && (
              <span style={{
                fontSize: '12px',
                padding: '2px 8px',
                borderRadius: '12px',
                backgroundColor: '#4CAF50',
                color: 'white'
              }}>
                📱 Synced
              </span>
            )}
          </div>
          
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
            ⏰ {formatTime(event.start_time)} - {formatTime(event.end_time)}
          </div>
          
          {event.description && (
            <p style={{
              fontSize: '14px',
              color: '#555',
              margin: '0 0 8px 0',
              lineHeight: '1.4'
            }}>
              {event.description}
            </p>
          )}
          
          {event.goal_id && goalTitle && (
            <div style={{
              fontSize: '12px',
              color: '#7c3aed',
              backgroundColor: '#f3e8ff',
              padding: '4px 8px',
              borderRadius: '4px',
              display: 'inline-block'
            }}>
              🎯 Goal: {goalTitle}
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleEdit}
            style={{
              padding: '8px',
              backgroundColor: '#e3f2fd',
              color: '#1976d2',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
            title="Edit event"
          >
            ✏️
          </button>
          
          <button
            onClick={handleDelete}
            style={{
              padding: '8px',
              backgroundColor: '#ffebee',
              color: '#d32f2f',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
            title="Delete event"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
});

EventItem.displayName = 'EventItem';

// Main component with optimization
export const OptimizedCalendarEventList = memo<CalendarEventListProps>(({
  events,
  goals,
  selectedDate,
  onEditEvent,
  onDeleteEvent
}) => {
  // Memoize goal lookup to prevent recalculation on every render
  const goalTitles = useMemo(() => {
    const goalMap = new Map<number, string>();
    goals.forEach(goal => {
      goalMap.set(goal.id, goal.title);
    });
    return goalMap;
  }, [goals]);

  // Memoize sorted events
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => 
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
  }, [events]);

  // Memoize formatted date
  const formattedDate = useMemo(() => {
    return new Date(selectedDate).toLocaleDateString();
  }, [selectedDate]);

  if (events.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px 20px',
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        margin: '20px 0'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📅</div>
        <h3 style={{ marginBottom: '8px' }}>No events scheduled</h3>
        <p>Create your first event or let AI schedule your day!</p>
      </div>
    );
  }

  return (
    <div style={{ marginTop: '20px' }}>
      <h3 style={{
        fontSize: '18px',
        fontWeight: 'bold',
        marginBottom: '16px',
        color: '#333'
      }}>
        Events for {formattedDate}
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {sortedEvents.map(event => (
          <EventItem
            key={event.id}
            event={event}
            goalTitle={goalTitles.get(event.goal_id || 0) || ''}
            onEdit={onEditEvent}
            onDelete={onDeleteEvent}
          />
        ))}
      </div>
    </div>
  );
});

OptimizedCalendarEventList.displayName = 'OptimizedCalendarEventList';