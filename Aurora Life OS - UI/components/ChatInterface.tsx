import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Plus, MoreHorizontal } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

interface Message {
  id: string;
  type: 'ai' | 'user';
  content: string;
  timestamp: Date;
  quickReplies?: string[];
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: "Good morning! I'm Aurora, your AI life companion. How are you feeling today?",
      timestamp: new Date(),
      quickReplies: ['Great!', 'Could be better', 'Feeling motivated', 'Need some guidance']
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

  const sendMessage = (content: string) => {
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

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: getAIResponse(content),
        timestamp: new Date(),
        quickReplies: getQuickReplies(content)
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const getAIResponse = (userMessage: string): string => {
    const responses = [
      "That's wonderful to hear! Let's make today productive. What would you like to focus on?",
      "I understand. Would you like to talk about what's on your mind or shall we plan something uplifting?",
      "I'm here to help you achieve your goals. What's the most important thing you'd like to work on today?",
      "Let's break down your day into manageable steps. What's your top priority right now?"
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const getQuickReplies = (userMessage: string): string[] => {
    return ['Show my schedule', 'Review my goals', 'How am I doing?', 'I need motivation'];
  };

  const handleQuickReply = (reply: string) => {
    sendMessage(reply);
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

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[280px] rounded-2xl px-4 py-3 ${
              message.type === 'user' 
                ? 'bg-[#4A90E2] text-white' 
                : 'bg-[#F5F7FA] text-[#262626]'
            }`}>
              <p className="text-sm">{message.content}</p>
              {message.quickReplies && (
                <div className="mt-3 space-y-2">
                  {message.quickReplies.map((reply, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickReply(reply)}
                      className="block w-full text-left px-3 py-2 text-xs bg-white text-[#4A90E2] rounded-lg hover:bg-[#4A90E2]/10 transition-colors"
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
          <div className="flex justify-start">
            <div className="max-w-[280px] bg-[#F5F7FA] rounded-2xl px-4 py-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-[#8C8C8C] rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-[#8C8C8C] rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-[#8C8C8C] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-[#D9D9D9] px-4 py-3 bg-white">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <button
            type="button"
            className="p-2 text-[#8C8C8C] hover:text-[#4A90E2] transition-colors"
          >
            <Plus className="w-5 h-5" />
          </button>
          <div className="flex-1 relative">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Message Aurora..."
              className="pr-12 bg-[#F5F7FA] border-0 rounded-full focus:ring-2 focus:ring-[#4A90E2]"
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[#8C8C8C] hover:text-[#4A90E2] transition-colors"
            >
              <Mic className="w-4 h-4" />
            </button>
          </div>
          <Button
            type="submit"
            size="sm"
            className="rounded-full bg-[#4A90E2] hover:bg-[#4A90E2]/90"
            disabled={!inputValue.trim()}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
