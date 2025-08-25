import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Plus, Brain, Target, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

interface CalendarEvent {
  id: string;
  title: string;
  time: string;
  duration: number;
  type: 'meeting' | 'task' | 'goal' | 'break' | 'personal';
  goalAlignment?: string;
  aiSuggestion?: string;
}

interface DayData {
  date: number;
  events: CalendarEvent[];
  mood?: number;
  isToday?: boolean;
}

export function CalendarView() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Sample calendar data
  const calendarData: DayData[] = [
    {
      date: 8,
      isToday: true,
      mood: 7,
      events: [
        {
          id: '1',
          title: 'Team Standup',
          time: '9:00 AM',
          duration: 30,
          type: 'meeting'
        },
        {
          id: '2',
          title: 'Spanish Practice',
          time: '12:00 PM',
          duration: 60,
          type: 'goal',
          goalAlignment: 'Learn Spanish',
          aiSuggestion: 'Perfect time for focused learning!'
        },
        {
          id: '3',
          title: 'Project Review',
          time: '2:00 PM',
          duration: 90,
          type: 'meeting'
        }
      ]
    },
    {
      date: 9,
      mood: 8,
      events: [
        {
          id: '4',
          title: 'Morning Run',
          time: '7:00 AM',
          duration: 45,
          type: 'goal',
          goalAlignment: 'Run a 10K',
          aiSuggestion: 'Great choice for high energy!'
        },
        {
          id: '5',
          title: 'Client Call',
          time: '10:00 AM',
          duration: 60,
          type: 'meeting'
        }
      ]
    }
  ];

  const getEventTypeColor = (type: string) => {
    const colors = {
      'meeting': 'bg-[#4A90E2] text-white',
      'task': 'bg-[#FAAD14] text-white',
      'goal': 'bg-[#52C41A] text-white',
      'break': 'bg-[#722ED1] text-white',
      'personal': 'bg-[#FF7D00] text-white'
    };
    return colors[type as keyof typeof colors] || 'bg-[#8C8C8C] text-white';
  };

  const getMoodEmoji = (mood: number) => {
    if (mood >= 8) return '😄';
    if (mood >= 6) return '😊';
    if (mood >= 4) return '😐';
    return '😕';
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + (direction === 'next' ? 1 : -1));
    setCurrentDate(newDate);
  };

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push({ type: 'empty', index: i });
    }
    
    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push({ type: 'day', date: day });
    }
    
    return days;
  };

  const getDayData = (day: number): DayData | undefined => {
    return calendarData.find(data => data.date === day);
  };

  const todayEvents = calendarData.find(day => day.isToday)?.events || [];

  return (
    <div className="h-full bg-[#F5F7FA] overflow-y-auto">
      {/* Header */}
      <div className="bg-white border-b border-[#D9D9D9] px-4 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <button onClick={() => navigateMonth('prev')} className="p-1 text-[#8C8C8C] hover:text-[#262626]">
              <ChevronLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-medium text-[#262626]">
              {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h1>
            <button onClick={() => navigateMonth('next')} className="p-1 text-[#8C8C8C] hover:text-[#262626]">
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
          <Button className="bg-[#4A90E2] hover:bg-[#4A90E2]/90 rounded-full">
            <Plus className="w-4 h-4 mr-2" />
            Add Event
          </Button>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {daysOfWeek.map((day) => (
            <div key={day} className="text-center text-sm font-medium text-[#8C8C8C] py-2">
              {day}
            </div>
          ))}
        </div>
        
        <div className="grid grid-cols-7 gap-1">
          {getDaysInMonth().map((item, index) => {
            if (item.type === 'empty') {
              return <div key={index} className="h-12"></div>;
            }
            
            const day = item.date;
            const dayData = getDayData(day);
            const isSelected = selectedDate.getDate() === day && 
                              selectedDate.getMonth() === currentDate.getMonth() &&
                              selectedDate.getFullYear() === currentDate.getFullYear();
            
            return (
              <button
                key={index}
                onClick={() => {
                  const newDate = new Date(currentDate);
                  newDate.setDate(day);
                  setSelectedDate(newDate);
                }}
                className={`h-12 rounded-lg flex flex-col items-center justify-center text-sm transition-colors relative ${
                  dayData?.isToday 
                    ? 'bg-[#4A90E2] text-white font-medium' 
                    : isSelected
                    ? 'bg-[#4A90E2]/10 text-[#4A90E2]'
                    : 'text-[#262626] hover:bg-[#F5F7FA]'
                }`}
              >
                <span>{day}</span>
                {dayData?.events.length > 0 && (
                  <div className="w-1 h-1 bg-current rounded-full mt-1"></div>
                )}
                {dayData?.mood && (
                  <span className="absolute top-0 right-0 text-xs">
                    {getMoodEmoji(dayData.mood)}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Today's Focus */}
        <Card className="border-0 shadow-sm bg-gradient-to-r from-[#4A90E2]/5 to-[#722ED1]/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-[#4A90E2]" />
              Today's Focus
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#52C41A]" />
                <span className="text-sm text-[#262626]">
                  2 hours available for deep work (10 AM - 12 PM)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-[#722ED1]" />
                <span className="text-sm text-[#262626]">
                  Perfect energy level for Spanish practice
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Today's Schedule */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle>Today's Schedule</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {todayEvents.length > 0 ? (
              todayEvents.map((event) => (
                <div key={event.id} className="flex items-center gap-3 p-3 bg-[#F5F7FA] rounded-lg">
                  <div className="w-1 h-12 rounded-full" style={{ backgroundColor: getEventTypeColor(event.type).includes('bg-[#4A90E2]') ? '#4A90E2' : '#52C41A' }}></div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-[#262626]">{event.title}</h3>
                      <Badge className={`text-xs ${getEventTypeColor(event.type)}`}>
                        {event.type}
                      </Badge>
                    </div>
                    <p className="text-sm text-[#8C8C8C]">{event.time} • {event.duration} min</p>
                    {event.goalAlignment && (
                      <p className="text-xs text-[#4A90E2] mt-1">
                        📍 Aligned with: {event.goalAlignment}
                      </p>
                    )}
                    {event.aiSuggestion && (
                      <p className="text-xs text-[#722ED1] mt-1">
                        💡 {event.aiSuggestion}
                      </p>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-[#8C8C8C]">No events scheduled for today</p>
                <Button variant="outline" className="mt-2">
                  Schedule your day
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Scheduling Suggestions */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-[#722ED1]" />
              Smart Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="bg-[#52C41A]/5 rounded-lg p-3 border-l-4 border-[#52C41A]">
              <p className="text-sm text-[#262626]">
                <strong>Optimal Time:</strong> Schedule your 10K training run for 7 AM tomorrow when your energy is typically highest.
              </p>
            </div>
            <div className="bg-[#FAAD14]/5 rounded-lg p-3 border-l-4 border-[#FAAD14]">
              <p className="text-sm text-[#262626]">
                <strong>Conflict Alert:</strong> Your 2 PM meeting overlaps with your usual reading time. Consider rescheduling.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
