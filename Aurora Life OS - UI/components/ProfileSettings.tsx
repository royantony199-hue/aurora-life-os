import React, { useState } from 'react';
import { User, Settings, Bell, Calendar, Shield, HelpCircle, LogOut, ChevronRight, Moon, Sun } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';

export function ProfileSettings() {
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState({
    dailyCheckins: true,
    goalReminders: true,
    moodInsights: false,
    weeklyReports: true
  });

  const userStats = {
    daysActive: 28,
    goalsCompleted: 3,
    avgMood: 7.2,
    streakDays: 12
  };

  const settingsSections = [
    {
      title: 'Notifications',
      icon: Bell,
      items: [
        {
          id: 'dailyCheckins',
          label: 'Daily Check-ins',
          description: 'Remind me to log my mood daily',
          value: notifications.dailyCheckins,
          onChange: (value: boolean) => setNotifications(prev => ({ ...prev, dailyCheckins: value }))
        },
        {
          id: 'goalReminders',
          label: 'Goal Reminders',
          description: 'Notify me about upcoming deadlines',
          value: notifications.goalReminders,
          onChange: (value: boolean) => setNotifications(prev => ({ ...prev, goalReminders: value }))
        },
        {
          id: 'moodInsights',
          label: 'Mood Insights',
          description: 'Weekly mood pattern insights',
          value: notifications.moodInsights,
          onChange: (value: boolean) => setNotifications(prev => ({ ...prev, moodInsights: value }))
        },
        {
          id: 'weeklyReports',
          label: 'Weekly Progress Reports',
          description: 'Summary of achievements and progress',
          value: notifications.weeklyReports,
          onChange: (value: boolean) => setNotifications(prev => ({ ...prev, weeklyReports: value }))
        }
      ]
    }
  ];

  const menuItems = [
    {
      icon: Calendar,
      label: 'Calendar Integration',
      description: 'Google Calendar connected',
      status: 'connected',
      action: () => console.log('Calendar settings')
    },
    {
      icon: Shield,
      label: 'Privacy & Security',
      description: 'Manage your data and privacy',
      action: () => console.log('Privacy settings')
    },
    {
      icon: HelpCircle,
      label: 'Help & Support',
      description: 'Get help and contact support',
      action: () => console.log('Help center')
    }
  ];

  return (
    <div className="h-full bg-[#F5F7FA] overflow-y-auto">
      {/* Header */}
      <div className="bg-white border-b border-[#D9D9D9] px-4 py-6">
        <div className="flex items-center gap-4">
          <Avatar className="w-16 h-16">
            <AvatarImage src="/placeholder-avatar.jpg" />
            <AvatarFallback className="bg-[#4A90E2] text-white text-xl">JD</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <h1 className="text-xl font-medium text-[#262626]">John Doe</h1>
            <p className="text-sm text-[#8C8C8C]">john.doe@example.com</p>
            <Badge className="mt-1 bg-[#52C41A]/10 text-[#52C41A] border-[#52C41A]/20">
              Premium Member
            </Badge>
          </div>
          <Button variant="outline" size="sm">
            Edit Profile
          </Button>
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Stats Overview */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle>Your Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-[#4A90E2]">{userStats.daysActive}</p>
                <p className="text-sm text-[#8C8C8C]">Days Active</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#52C41A]">{userStats.goalsCompleted}</p>
                <p className="text-sm text-[#8C8C8C]">Goals Completed</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#FAAD14]">{userStats.avgMood}</p>
                <p className="text-sm text-[#8C8C8C]">Avg Mood</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#722ED1]">{userStats.streakDays}</p>
                <p className="text-sm text-[#8C8C8C]">Day Streak</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* App Settings */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              App Settings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {darkMode ? <Moon className="w-5 h-5 text-[#8C8C8C]" /> : <Sun className="w-5 h-5 text-[#FAAD14]" />}
                  <div>
                    <p className="text-sm font-medium text-[#262626]">Dark Mode</p>
                    <p className="text-xs text-[#8C8C8C]">Switch to dark theme</p>
                  </div>
                </div>
                <Switch
                  checked={darkMode}
                  onCheckedChange={setDarkMode}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications Settings */}
        {settingsSections.map((section) => (
          <Card key={section.title} className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <section.icon className="w-5 h-5" />
                {section.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {section.items.map((item) => (
                  <div key={item.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-[#262626]">{item.label}</p>
                      <p className="text-xs text-[#8C8C8C]">{item.description}</p>
                    </div>
                    <Switch
                      checked={item.value}
                      onCheckedChange={item.onChange}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Menu Items */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            {menuItems.map((item, index) => (
              <button
                key={item.label}
                onClick={item.action}
                className={`w-full flex items-center gap-3 p-4 text-left hover:bg-[#F5F7FA] transition-colors ${
                  index !== menuItems.length - 1 ? 'border-b border-[#D9D9D9]' : ''
                }`}
              >
                <item.icon className="w-5 h-5 text-[#8C8C8C]" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-[#262626]">{item.label}</p>
                  <p className="text-xs text-[#8C8C8C]">{item.description}</p>
                </div>
                {item.status === 'connected' && (
                  <Badge className="bg-[#52C41A]/10 text-[#52C41A] border-[#52C41A]/20">
                    Connected
                  </Badge>
                )}
                <ChevronRight className="w-4 h-4 text-[#8C8C8C]" />
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Aurora AI Settings */}
        <Card className="border-0 shadow-sm bg-gradient-to-r from-[#4A90E2]/5 to-[#722ED1]/5">
          <CardHeader>
            <CardTitle>Aurora AI Preferences</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-white/50 rounded-lg p-3">
              <p className="text-sm font-medium text-[#262626] mb-1">Coaching Style</p>
              <p className="text-xs text-[#8C8C8C]">Supportive and encouraging</p>
            </div>
            <div className="bg-white/50 rounded-lg p-3">
              <p className="text-sm font-medium text-[#262626] mb-1">Check-in Frequency</p>
              <p className="text-xs text-[#8C8C8C]">Daily at 9:00 AM</p>
            </div>
            <Button variant="outline" className="w-full">
              Customize Aurora
            </Button>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            <button className="w-full flex items-center gap-3 p-4 text-left hover:bg-red-50 transition-colors text-red-600">
              <LogOut className="w-5 h-5" />
              <div>
                <p className="text-sm font-medium">Sign Out</p>
                <p className="text-xs text-red-400">Sign out of your account</p>
              </div>
            </button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
