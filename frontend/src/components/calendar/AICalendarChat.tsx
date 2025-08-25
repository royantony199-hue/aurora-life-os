import React, { useState } from 'react';
import { ChatMessage, RoutineSettings } from './types';

interface AICalendarChatProps {
  chatHistory: ChatMessage[];
  onSendMessage: (message: string) => void;
  routineSettings: RoutineSettings;
  isVisible: boolean;
  onClose: () => void;
}

export const AICalendarChat: React.FC<AICalendarChatProps> = ({
  chatHistory,
  onSendMessage,
  routineSettings,
  isVisible,
  onClose
}) => {
  const [chatMessage, setChatMessage] = useState('');

  if (!isVisible) return null;

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return;
    
    onSendMessage(chatMessage.trim());
    setChatMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '600px',
        height: '80%',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h3 style={{ margin: '0', fontSize: '20px', color: '#333' }}>
              🤖 AI Calendar Assistant
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#666' }}>
              Tell me your goal and I'll break it down into specific actionable tasks and schedule them strategically around your routine.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#999'
            }}
          >
            ×
          </button>
        </div>

        {/* Chat Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {chatHistory.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#666', marginTop: '50px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎯</div>
              <h4>Ready to help you schedule your goals!</h4>
              <p>Try saying:</p>
              <div style={{ 
                backgroundColor: '#f8f9fa', 
                padding: '12px', 
                borderRadius: '8px', 
                fontSize: '14px',
                textAlign: 'left',
                marginTop: '16px'
              }}>
                • "I need to learn singing"<br/>
                • "Schedule my workout routine"<br/>
                • "Plan my study schedule for this week"<br/>
                • "I want to add meditation to my routine"
              </div>
            </div>
          ) : (
            chatHistory.map((msg, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '12px 16px',
                    borderRadius: '18px',
                    backgroundColor: msg.role === 'user' ? '#4A90E2' : '#f1f3f4',
                    color: msg.role === 'user' ? 'white' : '#333',
                    fontSize: '14px',
                    lineHeight: '1.4',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input Area */}
        <div style={{
          padding: '20px',
          borderTop: '1px solid #e0e0e0'
        }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <textarea
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="What would you like to schedule? (e.g., 'I want to learn guitar')"
              style={{
                flex: 1,
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '14px',
                resize: 'none',
                minHeight: '44px',
                maxHeight: '100px'
              }}
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!chatMessage.trim()}
              style={{
                padding: '12px 20px',
                backgroundColor: chatMessage.trim() ? '#4A90E2' : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: chatMessage.trim() ? 'pointer' : 'not-allowed',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Send
            </button>
          </div>
          <div style={{
            fontSize: '12px',
            color: '#999',
            marginTop: '8px',
            textAlign: 'center'
          }}>
            Current routine: Wake up {routineSettings.wake_up_time} • Work {routineSettings.work_start}-{routineSettings.work_end} • Gym {routineSettings.gym_time}
          </div>
        </div>
      </div>
    </div>
  );
};