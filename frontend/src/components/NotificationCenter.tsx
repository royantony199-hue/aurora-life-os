import React, { useState, useEffect } from 'react';
import { Bell, Calendar, Clock, X, Check, AlertCircle, Info } from 'lucide-react';
import { api } from '../services/api';

interface Notification {
  id: string;
  type: 'reminder' | 'achievement' | 'info' | 'warning';
  title: string;
  message: string;
  time: Date;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationCenter({ isOpen, onClose }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      // Load recent chat messages that are notifications
      const response = await api.get('/api/chat/messages?limit=20');
      const messages = response.data.messages || [];
      
      const notificationMessages = messages.filter((msg: any) => 
        msg.context_data?.notification_type || 
        msg.content.includes('⏰') || 
        msg.content.includes('🔔') || 
        msg.content.includes('🚨')
      );

      const formattedNotifications: Notification[] = notificationMessages.map((msg: any) => ({
        id: msg.id.toString(),
        type: getNotificationType(msg),
        title: getNotificationTitle(msg),
        message: msg.content,
        time: new Date(msg.created_at),
        read: false, // In a real app, track read status
        action: getNotificationAction(msg)
      }));

      // Add some demo notifications for testing
      const demoNotifications: Notification[] = [
        {
          id: 'demo-1',
          type: 'achievement',
          title: 'Goal Progress!',
          message: '🎉 You completed your daily mood check-in streak of 7 days!',
          time: new Date(Date.now() - 5 * 60000),
          read: false
        },
        {
          id: 'demo-2',
          type: 'info',
          title: 'Calendar Sync',
          message: '📅 Successfully synced 56 events from Google Calendar',
          time: new Date(Date.now() - 15 * 60000),
          read: false
        }
      ];

      const allNotifications = [...formattedNotifications, ...demoNotifications];
      allNotifications.sort((a, b) => b.time.getTime() - a.time.getTime());

      setNotifications(allNotifications.slice(0, 10)); // Keep latest 10
      setUnreadCount(allNotifications.filter(n => !n.read).length);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const getNotificationType = (msg: any): Notification['type'] => {
    if (msg.context_data?.notification_type === 'event_reminder') return 'reminder';
    if (msg.content.includes('🎉') || msg.content.includes('✅')) return 'achievement';
    if (msg.content.includes('⚠️') || msg.content.includes('🚨')) return 'warning';
    return 'info';
  };

  const getNotificationTitle = (msg: any): string => {
    if (msg.context_data?.notification_type === 'event_reminder') return 'Event Reminder';
    if (msg.content.includes('🎉')) return 'Achievement';
    if (msg.content.includes('📅')) return 'Calendar Update';
    return 'Notification';
  };

  const getNotificationAction = (msg: any) => {
    if (msg.context_data?.meeting_url) {
      return {
        label: 'Join Meeting',
        onClick: () => window.open(msg.context_data.meeting_url, '_blank')
      };
    }
    return undefined;
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'reminder': return <Clock className="w-5 h-5 text-blue-500" />;
      case 'achievement': return <Check className="w-5 h-5 text-green-500" />;
      case 'warning': return <AlertCircle className="w-5 h-5 text-orange-500" />;
      default: return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Notification Panel */}
      <div className="absolute top-0 right-0 h-full w-full max-w-sm bg-white shadow-2xl transform transition-transform duration-300 ease-out">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="w-6 h-6" />
              <div>
                <h2 className="text-lg font-semibold">Notifications</h2>
                <p className="text-sm opacity-90">{unreadCount} unread</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto h-[calc(100vh-140px)]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Bell className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">No notifications</p>
              <p className="text-sm">You're all caught up!</p>
            </div>
          ) : (
            <div className="space-y-0">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`border-b border-gray-100 p-4 transition-colors ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <p className="font-medium text-gray-900 text-sm">
                          {notification.title}
                        </p>
                        <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                          {formatTime(notification.time)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {notification.message}
                      </p>
                      {notification.action && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            notification.action!.onClick();
                          }}
                          className="mt-2 text-blue-600 text-sm font-medium hover:text-blue-700"
                        >
                          {notification.action.label}
                        </button>
                      )}
                    </div>
                    {!notification.read && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-2" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={clearAll}
              className="w-full text-center text-sm text-gray-500 hover:text-gray-700 py-2"
            >
              Clear all notifications
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Notification Bell Icon Component for Header
export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(2); // Demo count

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="relative p-2 text-white hover:bg-white/20 rounded-full transition-colors"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      
      <NotificationCenter 
        isOpen={isOpen} 
        onClose={() => setIsOpen(false)} 
      />
    </>
  );
}