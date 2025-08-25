import { useState, useEffect } from 'react';
import { Plus, Target, Calendar, TrendingUp, CheckCircle2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { goalsAPI } from '../services/api';

interface Goal {
  id: number;
  title: string;
  description: string;
  progress: number;
  target_date: string;
  status: 'active' | 'completed' | 'paused';
  category: string;
  priority: string;
  created_at: string;
  updated_at: string;
}

interface NewGoal {
  title: string;
  description: string;
  target_date: string;
  category: string;
  priority: 'low' | 'medium' | 'high';
}

export function GoalsDashboard() {
  const [goals, setGoals] = useState<Goal[]>([]);

  const overallProgress = goals.length > 0 
    ? Math.round(goals.reduce((acc, goal) => acc + goal.progress, 0) / goals.length) 
    : 0;

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const response = await goalsAPI.getGoals();
      setGoals(response.goals || response);
    } catch (error) {
      console.error('Failed to load goals:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-[#52C41A] text-white';
      case 'active': return 'bg-[#4A90E2] text-white';
      case 'paused': return 'bg-[#FAAD14] text-white';
      default: return 'bg-[#8C8C8C] text-white';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Learning': 'bg-[#722ED1]/10 text-[#722ED1]',
      'Health': 'bg-[#52C41A]/10 text-[#52C41A]',
      'Personal': 'bg-[#FAAD14]/10 text-[#FAAD14]',
    };
    return colors[category] || 'bg-[#8C8C8C]/10 text-[#8C8C8C]';
  };

  return (
    <div className="h-full bg-[#F5F7FA] overflow-y-auto">
      {/* Header */}
      <div className="bg-white border-b border-[#D9D9D9] px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-medium text-[#262626]">Your Goals</h1>
            <p className="text-sm text-[#8C8C8C]">Track your progress and achieve your dreams</p>
          </div>
          <Button 
            onClick={() => {/* Handle add goal action */}}
            className="bg-[#4A90E2] hover:bg-[#4A90E2]/90 rounded-full"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Goal
          </Button>
        </div>

        {/* Overall Progress */}
        <Card className="mt-4 border-0 bg-gradient-to-r from-[#4A90E2]/10 to-[#722ED1]/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[#262626]">Overall Progress</p>
                <p className="text-2xl font-bold text-[#4A90E2]">{overallProgress}%</p>
              </div>
              <div className="w-16 h-16 relative">
                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth="2"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#4A90E2"
                    strokeWidth="2"
                    strokeDasharray={`${overallProgress}, 100`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-[#4A90E2]" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Goals List */}
      <div className="p-4 space-y-4">
        {goals.map((goal) => (
          <Card key={goal.id} className="border-0 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <CardTitle className="text-lg text-[#262626]">{goal.title}</CardTitle>
                    <Badge className={`text-xs px-2 py-1 ${getStatusColor(goal.status)}`}>
                      {goal.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-[#8C8C8C] mb-2">{goal.description}</p>
                  <Badge variant="outline" className={`text-xs ${getCategoryColor(goal.category)}`}>
                    {goal.category}
                  </Badge>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-[#4A90E2]">{goal.progress}%</p>
                  <p className="text-xs text-[#8C8C8C]">Complete</p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <Progress value={goal.progress} className="mb-4 h-2" />
              
              <div className="space-y-3">
                <div className="flex items-start gap-2">
                  <Target className="w-4 h-4 text-[#4A90E2] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-[#262626]">Next Action</p>
                    <p className="text-sm text-[#8C8C8C]">Continue working on this goal</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-2">
                  <Calendar className="w-4 h-4 text-[#FAAD14] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-[#262626]">Target Date</p>
                    <p className="text-sm text-[#8C8C8C]">
                      {goal.target_date ? new Date(goal.target_date).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric', 
                        year: 'numeric' 
                      }) : 'No deadline set'}
                    </p>
                  </div>
                </div>
                
                <div className="bg-[#4A90E2]/5 rounded-lg p-3 border-l-4 border-[#4A90E2]">
                  <p className="text-sm font-medium text-[#4A90E2] mb-1">Aurora's Note</p>
                  <p className="text-sm text-[#262626]">Keep up the great work! Focus on consistent daily progress.</p>
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <Button variant="outline" size="sm" className="flex-1">
                  View Details
                </Button>
                <Button size="sm" className="bg-[#52C41A] hover:bg-[#52C41A]/90">
                  <CheckCircle2 className="w-4 h-4 mr-1" />
                  Mark Complete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}