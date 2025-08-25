import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Plus } from 'lucide-react';
import { chatAPI } from '../services/api';

interface Message {
  id: string;
  type: 'ai' | 'user';
  content: string;
  timestamp: Date;
  quickReplies?: string[];
}

export function UltimateChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: "Hello! 👋 I'm Aurora, your AI life companion. How are you feeling today?",
      timestamp: new Date(),
      quickReplies: ['Great!', 'Could be better', 'Feeling motivated', 'Need guidance']
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await chatAPI.sendMessage(messageText);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.response || response.message,
        timestamp: new Date(),
        quickReplies: response.suggestions
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'I\'m sorry, I\'m having trouble connecting right now. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickReply = async (reply: string) => {
    try {
      await chatAPI.quickCommand(reply);
      sendMessage(reply);
    } catch (error) {
      console.error('Quick reply failed:', error);
      sendMessage(reply);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column', 
      padding: '0',
      overflow: 'hidden'
    }}>
      {/* Messages Container - Full Height */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        background: 'white',
        margin: '8px',
        marginBottom: '4px',
        borderRadius: '16px',
        padding: '16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
          paddingBottom: '12px',
          borderBottom: '1px solid rgba(0,0,0,0.1)'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '18px'
          }}>💬</div>
          <div>
            <div style={{ fontWeight: '600', fontSize: '16px', color: '#1a202c' }}>Chat with Aurora</div>
            <div style={{ fontSize: '12px', color: '#718096' }}>AI Assistant</div>
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
          {messages.map((message) => (
            <div key={message.id} className={`chat-message ${message.type}`}>
              <div className={`chat-bubble ${message.type}`}>
                <p style={{ margin: 0 }}>{message.content}</p>
                {message.quickReplies && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                    {message.quickReplies.map((reply, index) => (
                      <button
                        key={index}
                        onClick={() => handleQuickReply(reply)}
                        style={{
                          background: 'rgba(255, 255, 255, 0.2)',
                          color: message.type === 'ai' ? '#667eea' : 'white',
                          border: `1px solid ${message.type === 'ai' ? '#667eea' : 'rgba(255, 255, 255, 0.3)'}`,
                          borderRadius: '16px',
                          padding: '6px 12px',
                          fontSize: '13px',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        {reply}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="chat-message ai">
              <div className="chat-bubble ai">
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    background: '#667eea',
                    borderRadius: '50%',
                    animation: 'pulse 1.4s infinite'
                  }}></div>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    background: '#667eea',
                    borderRadius: '50%',
                    animation: 'pulse 1.4s infinite 0.2s'
                  }}></div>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    background: '#667eea',
                    borderRadius: '50%',
                    animation: 'pulse 1.4s infinite 0.4s'
                  }}></div>
                  <span style={{ marginLeft: '8px', fontSize: '13px', color: '#718096' }}>
                    Aurora is thinking...
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <div style={{ 
        margin: '0 8px 8px 8px',
        background: 'white',
        borderRadius: '16px',
        padding: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <button
            type="button"
            style={{
              width: '44px',
              height: '44px',
              background: 'rgba(102, 126, 234, 0.1)',
              border: 'none',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: '#667eea'
            }}
          >
            <Plus size={20} />
          </button>
          
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Message Aurora..."
              style={{
                width: '100%',
                padding: '12px 50px 12px 16px',
                border: '2px solid rgba(102, 126, 234, 0.1)',
                borderRadius: '12px',
                fontSize: '16px',
                background: '#f8fafc',
                transition: 'all 0.2s ease',
                outline: 'none'
              }}
            />
            <button
              type="button"
              style={{
                position: 'absolute',
                right: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#718096',
                padding: '4px'
              }}
            >
              <Mic size={18} />
            </button>
          </div>
          
          <button
            type="submit"
            disabled={!inputValue.trim()}
            style={{
              width: '44px',
              height: '44px',
              background: inputValue.trim() 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'rgba(113, 128, 150, 0.3)',
              border: 'none',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: inputValue.trim() ? 'pointer' : 'not-allowed',
              color: 'white',
              transition: 'all 0.2s ease'
            }}
          >
            <Send size={18} />
          </button>
        </form>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 70%, 100% { 
            transform: scale(1);
            opacity: 1;
          }
          35% { 
            transform: scale(1.3);
            opacity: 0.7;
          }
        }
      `}</style>
    </div>
  );
}