import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Plus, MoreHorizontal } from 'lucide-react';
import { chatAPI } from '../services/api';

interface Message {
  id: string;
  type: 'ai' | 'user';
  content: string;
  timestamp: Date;
  quickReplies?: string[];
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [, setIsLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load chat history on component mount
    const loadChatHistory = async () => {
      try {
        const response = await chatAPI.getMessages(20);
        if (response.messages && response.messages.length > 0) {
          const formattedMessages = response.messages.map((msg: any) => ({
            id: msg.id?.toString() || Date.now().toString(),
            type: msg.sender === 'user' ? 'user' : 'ai',
            content: msg.message || msg.response,
            timestamp: new Date(msg.timestamp || msg.created_at),
            quickReplies: msg.suggested_actions
          }));
          setMessages(formattedMessages);
        } else {
          // Set welcome message if no history
          setMessages([{
            id: '1',
            type: 'ai',
            content: "Good morning! I'm Aurora, your AI life companion. How are you feeling today?",
            timestamp: new Date(),
            quickReplies: ['Great!', 'Could be better', 'Feeling motivated', 'Need some guidance']
          }]);
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
        // Set welcome message on error
        setMessages([{
          id: '1',
          type: 'ai',
          content: "Good morning! I'm Aurora, your AI life companion. How are you feeling today?",
          timestamp: new Date(),
          quickReplies: ['Great!', 'Could be better', 'Feeling motivated', 'Need some guidance']
        }]);
      } finally {
        setIsLoading(false);
      }
    };

    loadChatHistory();
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Send message to AI backend
      const response = await chatAPI.sendMessage(content);
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.response || 'I apologize, I\'m having trouble responding right now.',
        timestamp: new Date(),
        quickReplies: response.suggested_actions || ['Show my schedule', 'Review my goals', 'How am I doing?']
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Failed to send message:', error);
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

  // Removed unused helper functions

  const handleQuickReply = async (reply: string) => {
    try {
      // Handle quick commands via API
      await chatAPI.quickCommand(reply);
      sendMessage(reply);
    } catch (error) {
      console.error('Quick reply failed:', error);
      sendMessage(reply); // Fall back to regular message
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="bg-white border-b border-[#D9D9D9] px-4 py-3 flex items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-[#4A90E2] to-[#722ED1] rounded-full flex items-center justify-center">
            <span className="text-white font-medium">A</span>
          </div>
          <div>
            <h1 className="font-medium text-[#262626]">Aurora</h1>
            <p className="text-sm text-[#8C8C8C]">Your AI life companion</p>
          </div>
        </div>
        <button className="ml-auto p-2 text-[#8C8C8C] hover:text-[#262626]">
          <MoreHorizontal className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile Chat Messages */}
      <div className="mobile-chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`mobile-chat-message ${message.type}`}>
            <div className={`mobile-chat-bubble ${message.type}`}>
              <p>{message.content}</p>
              {message.quickReplies && (
                <div className="mobile-quick-replies">
                  {message.quickReplies.map((reply, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickReply(reply)}
                      className="mobile-quick-reply"
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
          <div className="mobile-chat-message ai">
            <div className="mobile-chat-bubble ai">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-[#718096] rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-[#718096] rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-[#718096] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Mobile Input Area */}
      <div className="mobile-chat-input-container">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <button
            type="button"
            className="p-2 text-[#718096] hover:text-[#667eea] transition-colors"
          >
            <Plus className="w-5 h-5" />
          </button>
          <div className="flex-1 relative">
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Message Aurora..."
              className="mobile-chat-input"
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[#718096] hover:text-[#667eea] transition-colors"
            >
              <Mic className="w-4 h-4" />
            </button>
          </div>
          <button
            type="submit"
            className="mobile-chat-send-button"
            disabled={!inputValue.trim()}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}