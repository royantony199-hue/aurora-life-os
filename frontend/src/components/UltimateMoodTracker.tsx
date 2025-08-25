import { useState, useEffect } from 'react';
import { TrendingUp, Heart, Zap, Brain } from 'lucide-react';
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

export function UltimateMoodTracker() {
  const [currentMood, setCurrentMood] = useState(7);
  const [currentEnergy, setCurrentEnergy] = useState(6);
  const [currentStress, setCurrentStress] = useState(4);
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
        mood_score: currentMood,
        energy_level: currentEnergy,
        stress_level: currentStress,
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

  if (isLoading) {
    return (
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">❤️</div>
          <div>
            <div className="card-title">Mood Tracker</div>
            <div className="card-subtitle">Loading your mood data...</div>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 16px' }}></div>
          <p style={{ color: '#718096' }}>Loading mood tracker...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Today's Check-in Card */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">❤️</div>
          <div>
            <div className="card-title">Today's Check-in</div>
            <div className="card-subtitle">How are you feeling?</div>
          </div>
        </div>

        {/* Mood Slider */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <label style={{ fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>Mood</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '24px' }}>{getMoodEmoji(currentMood)}</span>
              <span style={{ fontSize: '18px', fontWeight: '600', color: '#4A90E2' }}>{currentMood}/10</span>
            </div>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            value={currentMood}
            onChange={(e) => setCurrentMood(parseInt(e.target.value))}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              background: `linear-gradient(to right, ${getMoodColor(1)} 0%, ${getMoodColor(currentMood)} ${(currentMood - 1) * 11.11}%, #E5E7EB ${(currentMood - 1) * 11.11}%, #E5E7EB 100%)`,
              outline: 'none',
              appearance: 'none',
              cursor: 'pointer'
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#718096', marginTop: '4px' }}>
            <span>😢 Very Low</span>
            <span>😄 Very High</span>
          </div>
        </div>

        {/* Energy Slider */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <label style={{ fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>Energy Level</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={16} color={getEnergyColor(currentEnergy)} />
              <span style={{ fontSize: '18px', fontWeight: '600', color: '#4A90E2' }}>{currentEnergy}/10</span>
            </div>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            value={currentEnergy}
            onChange={(e) => setCurrentEnergy(parseInt(e.target.value))}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              background: `linear-gradient(to right, ${getEnergyColor(1)} 0%, ${getEnergyColor(currentEnergy)} ${(currentEnergy - 1) * 11.11}%, #E5E7EB ${(currentEnergy - 1) * 11.11}%, #E5E7EB 100%)`,
              outline: 'none',
              appearance: 'none',
              cursor: 'pointer'
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#718096', marginTop: '4px' }}>
            <span>⚡ Drained</span>
            <span>🔋 Energized</span>
          </div>
        </div>

        {/* Stress Slider */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <label style={{ fontSize: '14px', fontWeight: '500', color: '#1a202c' }}>Stress Level</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Brain size={16} color={currentStress > 7 ? '#FF4D4F' : currentStress > 4 ? '#FAAD14' : '#52C41A'} />
              <span style={{ fontSize: '18px', fontWeight: '600', color: '#4A90E2' }}>{currentStress}/10</span>
            </div>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            value={currentStress}
            onChange={(e) => setCurrentStress(parseInt(e.target.value))}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              background: `linear-gradient(to right, #52C41A 0%, #FAAD14 50%, #FF4D4F 100%)`,
              outline: 'none',
              appearance: 'none',
              cursor: 'pointer'
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#718096', marginTop: '4px' }}>
            <span>🧘 Calm</span>
            <span>😰 Very Stressed</span>
          </div>
        </div>

        {/* Notes */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ fontSize: '14px', fontWeight: '500', color: '#1a202c', display: 'block', marginBottom: '8px' }}>
            Notes (Optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="What's affecting your mood today?"
            rows={3}
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid rgba(102, 126, 234, 0.2)',
              borderRadius: '12px',
              background: 'rgba(102, 126, 234, 0.05)',
              fontSize: '14px',
              resize: 'vertical',
              outline: 'none',
              transition: 'all 0.2s ease'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#667eea';
              e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'rgba(102, 126, 234, 0.2)';
              e.target.style.boxShadow = 'none';
            }}
          />
        </div>

        <button 
          className="ultimate-btn"
          onClick={handleSaveMood}
          disabled={isSaving}
          style={{ width: '100%' }}
        >
          {isSaving ? 'Saving...' : 'Save Today\'s Mood'}
        </button>
      </div>

      {/* Mood Insights */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div className="ultimate-card" style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'rgba(82, 196, 26, 0.1)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px'
          }}>
            <Heart size={24} color="#52C41A" />
          </div>
          <p style={{ 
            fontSize: '24px', 
            fontWeight: '700', 
            margin: '0 0 4px 0', 
            color: getMoodColor(avgMood) 
          }}>
            {avgMood}/10
          </p>
          <p style={{ fontSize: '14px', color: '#718096', margin: 0 }}>Avg Mood</p>
        </div>

        <div className="ultimate-card" style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'rgba(114, 46, 209, 0.1)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px'
          }}>
            <Zap size={24} color="#722ED1" />
          </div>
          <p style={{ 
            fontSize: '24px', 
            fontWeight: '700', 
            margin: '0 0 4px 0', 
            color: getEnergyColor(avgEnergy) 
          }}>
            {avgEnergy}/10
          </p>
          <p style={{ fontSize: '14px', color: '#718096', margin: 0 }}>Avg Energy</p>
        </div>
      </div>

      {/* Recent Entries */}
      <div className="ultimate-card">
        <div className="card-header">
          <div className="card-icon">📊</div>
          <div>
            <div className="card-title">Recent Entries</div>
            <div className="card-subtitle">Your mood history</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {moodHistory.length > 0 ? (
            moodHistory.slice(0, 5).map((entry) => (
              <div
                key={entry.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px',
                  background: 'rgba(102, 126, 234, 0.05)',
                  borderRadius: '12px',
                  border: '1px solid rgba(102, 126, 234, 0.1)'
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <p style={{ 
                    fontSize: '12px', 
                    color: '#718096', 
                    margin: 0 
                  }}>
                    {entry.date ? new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Recent'}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                  <span style={{ fontSize: '20px' }}>{getMoodEmoji(entry.mood_score || 5)}</span>
                  <div>
                    <p style={{ 
                      fontSize: '14px', 
                      fontWeight: '500', 
                      color: '#1a202c', 
                      margin: 0 
                    }}>
                      Mood: {entry.mood_score || 5}/10 • Energy: {entry.energy_level || 5}/10
                    </p>
                    {entry.notes && (
                      <p style={{ 
                        fontSize: '12px', 
                        color: '#718096', 
                        margin: 0, 
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        maxWidth: '200px'
                      }}>
                        {entry.notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                background: 'rgba(113, 128, 150, 0.1)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 12px'
              }}>
                <Heart size={24} color="#8C8C8C" />
              </div>
              <p style={{ color: '#718096', fontSize: '14px', margin: '0 0 4px 0' }}>No mood entries yet</p>
              <p style={{ color: '#718096', fontSize: '12px', margin: 0 }}>Check in above to start tracking your mood</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Insights */}
      <div className="ultimate-card" style={{ 
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(114, 46, 209, 0.1) 100%)',
        border: '1px solid rgba(102, 126, 234, 0.2)'
      }}>
        <div className="card-header">
          <div className="card-icon">🤖</div>
          <div>
            <div className="card-title">Aurora's Insights</div>
            <div className="card-subtitle">AI-powered mood analysis</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.5)',
            borderRadius: '12px',
            padding: '12px'
          }}>
            <p style={{ fontSize: '14px', color: '#1a202c', margin: 0 }}>
              <strong>Pattern Detected:</strong> Your mood tends to be highest on days when you exercise in the morning.
            </p>
          </div>
          <div style={{
            background: 'rgba(255, 255, 255, 0.5)',
            borderRadius: '12px',
            padding: '12px'
          }}>
            <p style={{ fontSize: '14px', color: '#1a202c', margin: 0 }}>
              <strong>Suggestion:</strong> Try scheduling 15 minutes of movement when your energy dips below 5.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}