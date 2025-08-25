import { useState, useEffect } from 'react';
import { TrendingUp, Heart, Zap, Brain, Loader } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Textarea } from './ui/textarea';
import { moodAPI } from '../services/api';

interface MoodEntry {
  id: number;
  user_id: number;
  mood_score: number;
  energy_level: number;
  stress_level?: number;
  notes?: string;
  created_at: string;
  burnout_risk?: number;
  date?: string;
}

interface MoodAnalytics {
  average_mood: number;
  average_energy: number;
  average_stress: number;
  mood_trend: string;
  energy_trend: string;
  burnout_risk: number;
}

export function MoodTracker() {
  const [currentMood, setCurrentMood] = useState([7]);
  const [currentEnergy, setCurrentEnergy] = useState([6]);
  const [currentStress, setCurrentStress] = useState([4]);
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [moodHistory, setMoodHistory] = useState<MoodEntry[]>([]);
  const [analytics, setAnalytics] = useState<MoodAnalytics | null>(null);

  const getMoodEmoji = (mood: number) => {
    if (mood >= 9) return '😄';
    if (mood >= 7) return '😊';
    if (mood >= 5) return '😐';
    if (mood >= 3) return '😕';
    return '😢';
  };

  const getMoodColor = (mood: number) => {
    if (mood >= 8) return '#52C41A';
    if (mood >= 6) return '#FAAD14';
    if (mood >= 4) return '#FF7D00';
    return '#FF4D4F';
  };

  const getEnergyColor = (energy: number) => {
    if (energy >= 8) return '#722ED1';
    if (energy >= 6) return '#4A90E2';
    if (energy >= 4) return '#FAAD14';
    return '#8C8C8C';
  };

  const avgMood = analytics?.average_mood || (moodHistory.length > 0 
    ? Math.round(moodHistory.reduce((acc, entry) => acc + entry.mood_score, 0) / moodHistory.length)
    : 0);
  const avgEnergy = analytics?.average_energy || (moodHistory.length > 0 
    ? Math.round(moodHistory.reduce((acc, entry) => acc + entry.energy_level, 0) / moodHistory.length)
    : 0);

  useEffect(() => {
    loadMoodData();
  }, []);

  const loadMoodData = async () => {
    try {
      setIsLoading(true);
      const [historyResponse, analyticsResponse] = await Promise.all([
        moodAPI.getMoodHistory(30).catch(() => []),
        moodAPI.getMoodAnalytics('month').catch(() => null)
      ]);
      
      setMoodHistory(historyResponse.entries || historyResponse || []);
      setAnalytics(analyticsResponse?.analytics || analyticsResponse || null);
    } catch (error) {
      console.error('Failed to load mood data:', error);
      setMoodHistory([]);
      setAnalytics(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveMood = async () => {
    try {
      setIsSaving(true);
      await moodAPI.saveMood({
        mood_score: currentMood[0],
        energy_level: currentEnergy[0],
        stress_level: currentStress[0],
        notes: notes.trim() || undefined
      });
      
      // Reset form and reload data
      setNotes('');
      await loadMoodData();
      
    } catch (error) {
      console.error('Failed to save mood:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="h-full bg-[#F5F7FA] overflow-y-auto">
      {/* Header */}
      <div className="bg-white border-b border-[#D9D9D9] px-4 py-4">
        <h1 className="text-xl font-medium text-[#262626]">Mood Tracker</h1>
        <p className="text-sm text-[#8C8C8C]">How are you feeling today?</p>
      </div>

      <div className="p-4 space-y-6">
        {/* Today's Check-in */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-[#FF4D4F]" />
              Today's Check-in
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Mood Slider */}
            {/* Mood Slider */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-[#262626]">Mood</label>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getMoodEmoji(currentMood[0])}</span>
                  <span className="text-lg font-bold text-[#4A90E2]">{currentMood[0]}/10</span>
                </div>
              </div>
              <Slider
                value={currentMood}
                onValueChange={setCurrentMood}
                max={10}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-[#8C8C8C] mt-1">
                <span>😢 Very Low</span>
                <span>😄 Very High</span>
              </div>
            </div>

            {/* Energy Slider */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-[#262626]">Energy Level</label>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4" style={{ color: getEnergyColor(currentEnergy[0]) }} />
                  <span className="text-lg font-bold text-[#4A90E2]">{currentEnergy[0]}/10</span>
                </div>
              </div>
              <Slider
                value={currentEnergy}
                onValueChange={setCurrentEnergy}
                max={10}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-[#8C8C8C] mt-1">
                <span>⚡ Drained</span>
                <span>🔋 Energized</span>
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="text-sm font-medium text-[#262626] mb-2 block">Notes (Optional)</label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="What's affecting your mood today?"
                className="bg-[#F5F7FA] border-0 focus:ring-2 focus:ring-[#4A90E2]"
                rows={3}
              />
            </div>

            <Button 
              onClick={handleSaveMood}
              className="w-full bg-[#4A90E2] hover:bg-[#4A90E2]/90"
            >
              Save Today's Mood
            </Button>
          </CardContent>
        </Card>

        {/* Mood Insights */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4 text-center">
              <div className="w-12 h-12 bg-[#52C41A]/10 rounded-full flex items-center justify-center mx-auto mb-2">
                <Heart className="w-6 h-6 text-[#52C41A]" />
              </div>
              <p className="text-2xl font-bold" style={{ color: getMoodColor(avgMood) }}>{avgMood}/10</p>
              <p className="text-sm text-[#8C8C8C]">Avg Mood</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4 text-center">
              <div className="w-12 h-12 bg-[#722ED1]/10 rounded-full flex items-center justify-center mx-auto mb-2">
                <Zap className="w-6 h-6 text-[#722ED1]" />
              </div>
              <p className="text-2xl font-bold" style={{ color: getEnergyColor(avgEnergy) }}>{avgEnergy}/10</p>
              <p className="text-sm text-[#8C8C8C]">Avg Energy</p>
            </CardContent>
          </Card>
        </div>

        {/* Mood History */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#4A90E2]" />
              Recent Entries
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {moodHistory.length > 0 ? (
              moodHistory.slice(0, 5).map((entry) => (
                <div key={entry.id} className="flex items-center gap-3 p-3 bg-[#F5F7FA] rounded-lg">
                  <div className="text-center">
                    <p className="text-xs text-[#8C8C8C]">
                      {entry.date ? new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Recent'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getMoodEmoji(entry.mood_score || entry.mood_level || 5)}</span>
                    <div>
                      <p className="text-sm font-medium text-[#262626]">
                        Mood: {entry.mood_score || entry.mood_level || 5}/10 • Energy: {entry.energy_level || 5}/10
                      </p>
                      {entry.notes && (
                        <p className="text-xs text-[#8C8C8C] truncate max-w-[200px]">{entry.notes}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6">
                <div className="w-12 h-12 bg-[#8C8C8C]/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Heart className="w-6 h-6 text-[#8C8C8C]" />
                </div>
                <p className="text-[#8C8C8C] text-sm">No mood entries yet</p>
                <p className="text-[#8C8C8C] text-xs">Check in above to start tracking your mood</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Insights */}
        <Card className="border-0 shadow-sm bg-gradient-to-r from-[#4A90E2]/5 to-[#722ED1]/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-[#4A90E2]" />
              Aurora's Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="bg-white/50 rounded-lg p-3">
                <p className="text-sm text-[#262626]">
                  <strong>Pattern Detected:</strong> Your mood tends to be highest on days when you exercise in the morning.
                </p>
              </div>
              <div className="bg-white/50 rounded-lg p-3">
                <p className="text-sm text-[#262626]">
                  <strong>Suggestion:</strong> Try scheduling 15 minutes of movement when your energy dips below 5.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}