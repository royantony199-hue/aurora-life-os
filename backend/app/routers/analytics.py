#!/usr/bin/env python3
"""
Analytics API Routes
Provides data visualization endpoints for mood tracking, goal progress, and productivity insights
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pydantic import BaseModel

from ..core.database import get_db
from ..models.mood import MoodEntry
from ..models.goal import Goal, GoalStatus
from ..models.task import Task, TaskStatus
from ..models.user import User

router = APIRouter()

class MoodAnalyticsResponse(BaseModel):
    """Response model for mood analytics data"""
    daily_average: List[Dict[str, Any]]
    weekly_trends: Dict[str, float]
    mood_distribution: Dict[int, int]
    energy_patterns: Dict[str, float]
    stress_correlation: List[Dict[str, float]]
    recommendations: List[str]

class ProductivityAnalyticsResponse(BaseModel):
    """Response model for productivity analytics"""
    task_completion_rate: float
    daily_productivity: List[Dict[str, Any]]
    peak_productivity_hours: List[int]
    goal_progress_summary: List[Dict[str, Any]]
    achievement_streaks: Dict[str, int]

@router.get("/mood/history/{user_id}", response_model=MoodAnalyticsResponse)
async def get_mood_analytics(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive mood analytics for visualization
    Includes daily averages, trends, patterns, and recommendations
    """
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Fetch mood entries for the period
    mood_entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == user_id,
        MoodEntry.created_at >= start_date
    ).order_by(MoodEntry.created_at).all()
    
    if not mood_entries:
        return MoodAnalyticsResponse(
            daily_average=[],
            weekly_trends={},
            mood_distribution={},
            energy_patterns={},
            stress_correlation=[],
            recommendations=["Start tracking your mood to see insights!"]
        )
    
    # Calculate daily averages
    daily_data = {}
    for entry in mood_entries:
        date_key = entry.created_at.date().isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = {
                'mood_sum': 0,
                'energy_sum': 0,
                'stress_sum': 0,
                'count': 0
            }
        
        daily_data[date_key]['mood_sum'] += entry.mood_level
        daily_data[date_key]['energy_sum'] += entry.energy_level
        daily_data[date_key]['stress_sum'] += entry.stress_level if entry.stress_level else 5
        daily_data[date_key]['count'] += 1
    
    # Format daily averages for chart
    daily_average = []
    for date, data in sorted(daily_data.items()):
        daily_average.append({
            'date': date,
            'mood': round(data['mood_sum'] / data['count'], 1),
            'energy': round(data['energy_sum'] / data['count'], 1),
            'stress': round(data['stress_sum'] / data['count'], 1),
            'entries': data['count']
        })
    
    # Calculate weekly trends
    weekly_trends = _calculate_weekly_trends(mood_entries)
    
    # Calculate mood distribution
    mood_distribution = {}
    for entry in mood_entries:
        mood_level = entry.mood_level
        mood_distribution[mood_level] = mood_distribution.get(mood_level, 0) + 1
    
    # Calculate energy patterns by time of day
    energy_patterns = _calculate_energy_patterns(mood_entries)
    
    # Calculate stress correlation
    stress_correlation = _calculate_stress_correlation(mood_entries)
    
    # Generate insights and recommendations
    recommendations = _generate_mood_recommendations(
        daily_average, weekly_trends, energy_patterns
    )
    
    return MoodAnalyticsResponse(
        daily_average=daily_average,
        weekly_trends=weekly_trends,
        mood_distribution=mood_distribution,
        energy_patterns=energy_patterns,
        stress_correlation=stress_correlation,
        recommendations=recommendations
    )

@router.get("/mood/patterns/{user_id}")
async def get_mood_patterns(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyze mood patterns to identify trends and triggers
    """
    
    # Get last 60 days of mood data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    mood_entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == user_id,
        MoodEntry.created_at >= start_date
    ).order_by(MoodEntry.created_at).all()
    
    if not mood_entries:
        return {"message": "No mood data available for pattern analysis"}
    
    # Analyze patterns
    patterns = {
        'day_of_week_patterns': _analyze_day_of_week_patterns(mood_entries),
        'time_of_day_patterns': _analyze_time_of_day_patterns(mood_entries),
        'mood_volatility': _calculate_mood_volatility(mood_entries),
        'energy_mood_correlation': _calculate_energy_mood_correlation(mood_entries),
        'improvement_trend': _calculate_improvement_trend(mood_entries),
        'low_mood_triggers': _identify_low_mood_patterns(mood_entries)
    }
    
    return patterns

@router.get("/productivity/{user_id}", response_model=ProductivityAnalyticsResponse)
async def get_productivity_analytics(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get productivity analytics including task completion, peak hours, and goal progress
    """
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Fetch tasks for the period
    tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.created_at >= start_date
    ).all()
    
    # Fetch goals
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    
    # Calculate task completion rate
    completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    completion_rate = len(completed_tasks) / len(tasks) if tasks else 0
    
    # Calculate daily productivity
    daily_productivity = _calculate_daily_productivity(tasks, start_date, end_date)
    
    # Calculate peak productivity hours
    peak_hours = _calculate_peak_productivity_hours(completed_tasks)
    
    # Calculate goal progress summary
    goal_progress = []
    for goal in goals:
        related_tasks = [t for t in tasks if t.goal_id == goal.id]
        completed_goal_tasks = [t for t in related_tasks if t.status == TaskStatus.COMPLETED]
        
        goal_progress.append({
            'goal_title': goal.title,
            'goal_id': goal.id,
            'progress': goal.progress,
            'task_completion_rate': len(completed_goal_tasks) / len(related_tasks) if related_tasks else 0,
            'days_until_deadline': (goal.target_date - datetime.now()).days if goal.target_date else None,
            'status': goal.status.value
        })
    
    # Calculate achievement streaks
    achievement_streaks = _calculate_achievement_streaks(completed_tasks)
    
    return ProductivityAnalyticsResponse(
        task_completion_rate=round(completion_rate * 100, 1),
        daily_productivity=daily_productivity,
        peak_productivity_hours=peak_hours,
        goal_progress_summary=goal_progress,
        achievement_streaks=achievement_streaks
    )

@router.get("/insights/{user_id}")
async def get_personalized_insights(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get AI-generated personalized insights based on mood and productivity data
    """
    
    # Get recent data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    
    mood_entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == user_id,
        MoodEntry.created_at >= start_date
    ).all()
    
    tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.created_at >= start_date
    ).all()
    
    # Generate insights
    insights = {
        'mood_insights': _generate_mood_insights(mood_entries),
        'productivity_insights': _generate_productivity_insights(tasks),
        'recommendations': _generate_personalized_recommendations(mood_entries, tasks),
        'celebration_moments': _identify_celebration_moments(mood_entries, tasks)
    }
    
    return insights

# Helper functions

def _calculate_weekly_trends(mood_entries: List[MoodEntry]) -> Dict[str, float]:
    """Calculate week-over-week trends"""
    if len(mood_entries) < 14:
        return {"trend": "insufficient_data"}
    
    # Split into current and previous week
    one_week_ago = datetime.now() - timedelta(days=7)
    current_week = [e for e in mood_entries if e.created_at >= one_week_ago]
    previous_week = [e for e in mood_entries if e.created_at < one_week_ago]
    
    if not current_week or not previous_week:
        return {"trend": "insufficient_data"}
    
    current_avg = sum(e.mood_level for e in current_week) / len(current_week)
    previous_avg = sum(e.mood_level for e in previous_week) / len(previous_week)
    
    change_percent = ((current_avg - previous_avg) / previous_avg) * 100
    
    return {
        "current_week_avg": round(current_avg, 1),
        "previous_week_avg": round(previous_avg, 1),
        "change_percent": round(change_percent, 1),
        "trend": "improving" if change_percent > 0 else "declining"
    }

def _calculate_energy_patterns(mood_entries: List[MoodEntry]) -> Dict[str, float]:
    """Calculate average energy levels by time of day"""
    time_buckets = {
        "morning": {"start": 6, "end": 12, "sum": 0, "count": 0},
        "afternoon": {"start": 12, "end": 17, "sum": 0, "count": 0},
        "evening": {"start": 17, "end": 22, "sum": 0, "count": 0},
        "night": {"start": 22, "end": 6, "sum": 0, "count": 0}
    }
    
    for entry in mood_entries:
        hour = entry.created_at.hour
        
        for period, data in time_buckets.items():
            if period == "night":
                if hour >= data["start"] or hour < data["end"]:
                    data["sum"] += entry.energy_level
                    data["count"] += 1
            else:
                if data["start"] <= hour < data["end"]:
                    data["sum"] += entry.energy_level
                    data["count"] += 1
    
    patterns = {}
    for period, data in time_buckets.items():
        if data["count"] > 0:
            patterns[period] = round(data["sum"] / data["count"], 1)
        else:
            patterns[period] = 0
    
    return patterns

def _calculate_stress_correlation(mood_entries: List[MoodEntry]) -> List[Dict[str, float]]:
    """Calculate correlation between stress and mood/energy"""
    correlations = []
    
    for entry in mood_entries[-10:]:  # Last 10 entries
        correlations.append({
            "mood": entry.mood_level,
            "energy": entry.energy_level,
            "stress": entry.stress_level if entry.stress_level else 5
        })
    
    return correlations

def _generate_mood_recommendations(
    daily_average: List[Dict],
    weekly_trends: Dict,
    energy_patterns: Dict
) -> List[str]:
    """Generate personalized recommendations based on mood data"""
    recommendations = []
    
    # Check for low mood patterns
    if daily_average:
        recent_avg = sum(d['mood'] for d in daily_average[-7:]) / min(7, len(daily_average))
        if recent_avg < 5:
            recommendations.append("Your mood has been lower than usual. Consider scheduling activities that bring you joy.")
    
    # Check energy patterns
    if energy_patterns:
        highest_energy = max(energy_patterns.items(), key=lambda x: x[1])
        recommendations.append(f"Your energy peaks in the {highest_energy[0]}. Schedule important tasks during this time.")
    
    # Check trends
    if weekly_trends.get('trend') == 'declining':
        recommendations.append("Your mood is trending downward. It might be time for self-care or reaching out to support.")
    elif weekly_trends.get('trend') == 'improving':
        recommendations.append("Great job! Your mood is improving. Keep up whatever you're doing!")
    
    return recommendations if recommendations else ["Keep tracking your mood to unlock personalized insights!"]

def _analyze_day_of_week_patterns(mood_entries: List[MoodEntry]) -> Dict[str, float]:
    """Analyze mood patterns by day of week"""
    day_data = {}
    
    for entry in mood_entries:
        day_name = entry.created_at.strftime("%A")
        if day_name not in day_data:
            day_data[day_name] = {"sum": 0, "count": 0}
        
        day_data[day_name]["sum"] += entry.mood_level
        day_data[day_name]["count"] += 1
    
    patterns = {}
    for day, data in day_data.items():
        patterns[day] = round(data["sum"] / data["count"], 1) if data["count"] > 0 else 0
    
    return patterns

def _analyze_time_of_day_patterns(mood_entries: List[MoodEntry]) -> Dict[int, float]:
    """Analyze mood patterns by hour of day"""
    hour_data = {}
    
    for entry in mood_entries:
        hour = entry.created_at.hour
        if hour not in hour_data:
            hour_data[hour] = {"sum": 0, "count": 0}
        
        hour_data[hour]["sum"] += entry.mood_level
        hour_data[hour]["count"] += 1
    
    patterns = {}
    for hour in range(24):
        if hour in hour_data and hour_data[hour]["count"] > 0:
            patterns[hour] = round(hour_data[hour]["sum"] / hour_data[hour]["count"], 1)
    
    return patterns

def _calculate_mood_volatility(mood_entries: List[MoodEntry]) -> float:
    """Calculate mood volatility (standard deviation)"""
    if len(mood_entries) < 2:
        return 0
    
    moods = [e.mood_level for e in mood_entries]
    mean = sum(moods) / len(moods)
    variance = sum((x - mean) ** 2 for x in moods) / len(moods)
    return round(variance ** 0.5, 2)

def _calculate_energy_mood_correlation(mood_entries: List[MoodEntry]) -> float:
    """Calculate correlation between energy and mood"""
    if len(mood_entries) < 2:
        return 0
    
    moods = [e.mood_level for e in mood_entries]
    energies = [e.energy_level for e in mood_entries]
    
    # Simple correlation coefficient
    n = len(moods)
    sum_x = sum(moods)
    sum_y = sum(energies)
    sum_xy = sum(x * y for x, y in zip(moods, energies))
    sum_x2 = sum(x ** 2 for x in moods)
    sum_y2 = sum(y ** 2 for y in energies)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
    
    if denominator == 0:
        return 0
    
    return round(numerator / denominator, 2)

def _calculate_improvement_trend(mood_entries: List[MoodEntry]) -> Dict[str, Any]:
    """Calculate overall improvement trend"""
    if len(mood_entries) < 7:
        return {"trend": "insufficient_data"}
    
    # Compare first and last week averages
    first_week = mood_entries[:7]
    last_week = mood_entries[-7:]
    
    first_avg = sum(e.mood_level for e in first_week) / 7
    last_avg = sum(e.mood_level for e in last_week) / 7
    
    improvement = last_avg - first_avg
    
    return {
        "first_week_avg": round(first_avg, 1),
        "last_week_avg": round(last_avg, 1),
        "improvement": round(improvement, 1),
        "trend": "improving" if improvement > 0.5 else "stable" if improvement > -0.5 else "declining"
    }

def _identify_low_mood_patterns(mood_entries: List[MoodEntry]) -> List[str]:
    """Identify patterns when mood is low"""
    low_mood_entries = [e for e in mood_entries if e.mood_level <= 4]
    
    if not low_mood_entries:
        return ["No low mood patterns detected"]
    
    patterns = []
    
    # Check time patterns
    low_mood_hours = [e.created_at.hour for e in low_mood_entries]
    if low_mood_hours:
        most_common_hour = max(set(low_mood_hours), key=low_mood_hours.count)
        patterns.append(f"Low moods often occur around {most_common_hour}:00")
    
    # Check day patterns
    low_mood_days = [e.created_at.strftime("%A") for e in low_mood_entries]
    if low_mood_days:
        most_common_day = max(set(low_mood_days), key=low_mood_days.count)
        patterns.append(f"Low moods are more common on {most_common_day}s")
    
    return patterns

def _calculate_daily_productivity(tasks: List[Task], start_date: datetime, end_date: datetime) -> List[Dict]:
    """Calculate daily productivity metrics"""
    daily_data = {}
    
    # Initialize all days in range
    current = start_date.date()
    while current <= end_date.date():
        daily_data[current.isoformat()] = {
            "created": 0,
            "completed": 0,
            "total_duration": 0
        }
        current += timedelta(days=1)
    
    # Aggregate task data
    for task in tasks:
        date_key = task.created_at.date().isoformat()
        if date_key in daily_data:
            daily_data[date_key]["created"] += 1
            
            if task.status == TaskStatus.COMPLETED:
                daily_data[date_key]["completed"] += 1
                if task.estimated_duration:
                    daily_data[date_key]["total_duration"] += task.estimated_duration
    
    # Format for response
    return [
        {
            "date": date,
            "tasks_created": data["created"],
            "tasks_completed": data["completed"],
            "completion_rate": round(data["completed"] / data["created"] * 100, 1) if data["created"] > 0 else 0,
            "total_minutes": data["total_duration"]
        }
        for date, data in sorted(daily_data.items())
    ]

def _calculate_peak_productivity_hours(completed_tasks: List[Task]) -> List[int]:
    """Identify hours when most tasks are completed"""
    hour_counts = {}
    
    for task in completed_tasks:
        if task.updated_at:
            hour = task.updated_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    if not hour_counts:
        return []
    
    # Get top 3 hours
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    return [hour for hour, count in sorted_hours[:3]]

def _calculate_achievement_streaks(completed_tasks: List[Task]) -> Dict[str, int]:
    """Calculate streaks of task completion"""
    if not completed_tasks:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Sort tasks by completion date
    sorted_tasks = sorted(completed_tasks, key=lambda x: x.updated_at or x.created_at)
    
    current_streak = 0
    longest_streak = 0
    last_date = None
    
    for task in sorted_tasks:
        task_date = (task.updated_at or task.created_at).date()
        
        if last_date is None:
            current_streak = 1
        elif task_date == last_date:
            # Same day, don't increment
            pass
        elif task_date == last_date + timedelta(days=1):
            # Consecutive day
            current_streak += 1
        else:
            # Streak broken
            longest_streak = max(longest_streak, current_streak)
            current_streak = 1
        
        last_date = task_date
    
    longest_streak = max(longest_streak, current_streak)
    
    # Check if streak is still active
    today = datetime.now().date()
    if last_date != today and last_date != today - timedelta(days=1):
        current_streak = 0
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }

def _generate_mood_insights(mood_entries: List[MoodEntry]) -> List[str]:
    """Generate insights from mood data"""
    if not mood_entries:
        return ["Start tracking your mood to see insights"]
    
    insights = []
    
    # Average mood
    avg_mood = sum(e.mood_level for e in mood_entries) / len(mood_entries)
    insights.append(f"Your average mood over the past 2 weeks: {avg_mood:.1f}/10")
    
    # Best and worst days
    best_day = max(mood_entries, key=lambda x: x.mood_level)
    worst_day = min(mood_entries, key=lambda x: x.mood_level)
    
    insights.append(f"Your best day was {best_day.created_at.strftime('%A')} with a mood of {best_day.mood_level}/10")
    insights.append(f"Your most challenging day was {worst_day.created_at.strftime('%A')} with a mood of {worst_day.mood_level}/10")
    
    return insights

def _generate_productivity_insights(tasks: List[Task]) -> List[str]:
    """Generate insights from task data"""
    if not tasks:
        return ["Create some tasks to see productivity insights"]
    
    insights = []
    
    # Completion rate
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    completion_rate = len(completed) / len(tasks) * 100
    insights.append(f"You've completed {completion_rate:.0f}% of your tasks")
    
    # Most productive day
    day_counts = {}
    for task in completed:
        day = task.updated_at.strftime("%A") if task.updated_at else task.created_at.strftime("%A")
        day_counts[day] = day_counts.get(day, 0) + 1
    
    if day_counts:
        best_day = max(day_counts.items(), key=lambda x: x[1])
        insights.append(f"You're most productive on {best_day[0]}s")
    
    return insights

def _generate_personalized_recommendations(
    mood_entries: List[MoodEntry],
    tasks: List[Task]
) -> List[str]:
    """Generate personalized recommendations"""
    recommendations = []
    
    if mood_entries:
        avg_mood = sum(e.mood_level for e in mood_entries) / len(mood_entries)
        avg_energy = sum(e.energy_level for e in mood_entries) / len(mood_entries)
        
        if avg_mood < 5:
            recommendations.append("Consider scheduling more activities that bring you joy")
        
        if avg_energy < 5:
            recommendations.append("Low energy detected - prioritize rest and recovery")
    
    if tasks:
        incomplete = [t for t in tasks if t.status != TaskStatus.COMPLETED]
        if len(incomplete) > 10:
            recommendations.append("You have many incomplete tasks - consider prioritizing or delegating")
    
    return recommendations if recommendations else ["You're doing great! Keep it up!"]

def _identify_celebration_moments(
    mood_entries: List[MoodEntry],
    tasks: List[Task]
) -> List[str]:
    """Identify moments worth celebrating"""
    celebrations = []
    
    # High mood days
    high_mood_days = [e for e in mood_entries if e.mood_level >= 8]
    if high_mood_days:
        celebrations.append(f"You had {len(high_mood_days)} great mood days!")
    
    # Task completions
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    if len(completed) >= 10:
        celebrations.append(f"Amazing! You completed {len(completed)} tasks!")
    
    return celebrations if celebrations else ["Keep going - celebrations are coming!"]