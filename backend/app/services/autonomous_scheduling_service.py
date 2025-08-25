#!/usr/bin/env python3
"""
Autonomous Scheduling Service

Provides intelligent scheduling capabilities that automatically suggest optimal times
for tasks and meetings based on user's energy patterns, mood data, calendar availability,
and task requirements.
"""

import json
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from .openai_service import OpenAIService
from ..models.user import User
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..models.mood import MoodEntry
from ..models.calendar import CalendarEvent
from ..models.goal import Goal


class AutonomousSchedulingService:
    """
    Intelligent scheduling service that finds optimal times for tasks
    based on multiple factors including energy, mood, and availability
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def suggest_optimal_schedule(
        self,
        user_id: int,
        db: Session,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Generate optimal schedule suggestions for the next N days
        """
        
        # Gather all necessary data
        user = db.query(User).filter(User.id == user_id).first()
        pending_tasks = self._get_pending_tasks(user_id, db)
        energy_patterns = self._analyze_energy_patterns(user_id, db)
        calendar_events = self._get_calendar_events(user_id, days_ahead, db)
        user_preferences = self._get_user_preferences(user_id, db)
        
        # Generate available time slots
        available_slots = self._find_available_slots(
            calendar_events, user_preferences, days_ahead
        )
        
        # Match tasks to optimal time slots
        scheduled_tasks = await self._match_tasks_to_slots(
            pending_tasks,
            available_slots,
            energy_patterns,
            user_preferences,
            db
        )
        
        # Generate scheduling insights
        insights = self._generate_scheduling_insights(
            scheduled_tasks,
            energy_patterns,
            pending_tasks
        )
        
        return {
            'scheduled_tasks': scheduled_tasks,
            'insights': insights,
            'energy_patterns': energy_patterns,
            'unscheduled_tasks': self._get_unscheduled_tasks(pending_tasks, scheduled_tasks)
        }
    
    async def reschedule_intelligently(
        self,
        task_id: int,
        user_id: int,
        db: Session,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Intelligently reschedule a specific task based on current context
        """
        
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            return {'success': False, 'message': 'Task not found'}
        
        # Analyze why rescheduling is needed
        context = await self._analyze_reschedule_context(task, reason, user_id, db)
        
        # Find new optimal time
        new_time_suggestions = await self._find_optimal_reschedule_time(
            task, context, user_id, db
        )
        
        return {
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'current_time': task.scheduled_for.isoformat() if task.scheduled_for else None
            },
            'suggestions': new_time_suggestions,
            'reasoning': context['reasoning']
        }
    
    async def auto_schedule_new_task(
        self,
        task: Task,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Automatically schedule a newly created task at the optimal time
        """
        
        # Get user's energy patterns and preferences
        energy_patterns = self._analyze_energy_patterns(user_id, db)
        user_preferences = self._get_user_preferences(user_id, db)
        
        # Get calendar availability for next 2 weeks
        calendar_events = self._get_calendar_events(user_id, 14, db)
        available_slots = self._find_available_slots(
            calendar_events, user_preferences, 14
        )
        
        # Find best slot for this specific task
        best_slot = await self._find_best_slot_for_task(
            task,
            available_slots,
            energy_patterns,
            user_preferences
        )
        
        if best_slot:
            return {
                'success': True,
                'suggested_time': best_slot['start_time'],
                'confidence': best_slot['confidence'],
                'reasoning': best_slot['reasoning']
            }
        else:
            return {
                'success': False,
                'message': 'No suitable time slot found',
                'alternatives': self._suggest_alternatives(task, user_preferences)
            }
    
    def _get_pending_tasks(self, user_id: int, db: Session) -> List[Task]:
        """Get all pending tasks that need scheduling"""
        # Temporarily get all pending tasks without scheduled_for filter due to DB migration issues
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).order_by(Task.priority.desc(), Task.created_at).all()
    
    def _analyze_energy_patterns(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Analyze user's energy patterns from mood data"""
        
        # Get last 30 days of mood data
        thirty_days_ago = datetime.now() - timedelta(days=30)
        mood_entries = db.query(MoodEntry).filter(
            MoodEntry.user_id == user_id,
            MoodEntry.created_at >= thirty_days_ago
        ).all()
        
        if not mood_entries:
            # Return default patterns if no data
            return {
                'peak_hours': [10, 11, 14, 15],
                'low_hours': [13, 17, 18],
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'patterns_available': False
            }
        
        # Analyze by hour of day
        hour_energy = {}
        hour_mood = {}
        
        for entry in mood_entries:
            hour = entry.created_at.hour
            if hour not in hour_energy:
                hour_energy[hour] = []
                hour_mood[hour] = []
            
            hour_energy[hour].append(entry.energy_level)
            hour_mood[hour].append(entry.mood_level)
        
        # Calculate averages
        energy_by_hour = {}
        mood_by_hour = {}
        
        for hour in range(24):
            if hour in hour_energy:
                energy_by_hour[hour] = sum(hour_energy[hour]) / len(hour_energy[hour])
                mood_by_hour[hour] = sum(hour_mood[hour]) / len(hour_mood[hour])
        
        # Find peak and low hours
        sorted_hours = sorted(energy_by_hour.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h[0] for h in sorted_hours[:4] if h[1] >= 6]
        low_hours = [h[0] for h in sorted_hours[-4:] if h[1] < 5]
        
        # Analyze by day of week
        day_energy = {}
        for entry in mood_entries:
            day_name = entry.created_at.strftime('%A')
            if day_name not in day_energy:
                day_energy[day_name] = []
            day_energy[day_name].append(entry.energy_level)
        
        avg_by_day = {}
        for day, energies in day_energy.items():
            avg_by_day[day] = sum(energies) / len(energies)
        
        best_days = sorted(avg_by_day.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'peak_hours': peak_hours,
            'low_hours': low_hours,
            'energy_by_hour': energy_by_hour,
            'mood_by_hour': mood_by_hour,
            'best_days': [d[0] for d in best_days],
            'patterns_available': True
        }
    
    def _get_calendar_events(
        self,
        user_id: int,
        days_ahead: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get calendar events for the specified period"""
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        # Get events from database
        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_date,
            CalendarEvent.start_time <= end_date
        ).order_by(CalendarEvent.start_time).all()
        
        # Convert to dict format
        return [
            {
                'id': event.id,
                'title': event.title,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'is_all_day': getattr(event, 'is_all_day', False)  # Default to False if field doesn't exist
            }
            for event in events
        ]
    
    def _get_user_preferences(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user scheduling preferences"""
        
        # In a real implementation, this would come from user settings
        # For now, return sensible defaults
        return {
            'work_start': time(9, 0),  # 9 AM
            'work_end': time(18, 0),   # 6 PM
            'lunch_start': time(12, 0), # 12 PM
            'lunch_duration': 60,       # 60 minutes
            'min_task_duration': 15,    # 15 minutes
            'max_task_duration': 120,   # 2 hours
            'buffer_between_tasks': 15, # 15 minutes
            'prefer_mornings_for': ['deep_work', 'important'],
            'prefer_afternoons_for': ['meetings', 'creative'],
            'no_work_days': ['Sunday']
        }
    
    def _find_available_slots(
        self,
        calendar_events: List[Dict],
        preferences: Dict,
        days_ahead: int
    ) -> List[Dict[str, Any]]:
        """Find available time slots considering calendar and preferences"""
        
        available_slots = []
        current_date = datetime.now().date()
        
        for day_offset in range(days_ahead):
            check_date = current_date + timedelta(days=day_offset)
            
            # Skip non-work days
            if check_date.strftime('%A') in preferences.get('no_work_days', []):
                continue
            
            # Get work hours for this day
            work_start = datetime.combine(check_date, preferences['work_start'])
            work_end = datetime.combine(check_date, preferences['work_end'])
            lunch_start = datetime.combine(check_date, preferences['lunch_start'])
            lunch_end = lunch_start + timedelta(minutes=preferences['lunch_duration'])
            
            # Get events for this day
            day_events = [
                e for e in calendar_events
                if e['start_time'].date() == check_date
            ]
            
            # Sort events by start time
            day_events.sort(key=lambda x: x['start_time'])
            
            # Find gaps between events
            current_time = work_start
            
            for event in day_events:
                # Check if there's a gap before this event
                if current_time < event['start_time']:
                    # Check if gap overlaps with lunch
                    if current_time < lunch_start and event['start_time'] > lunch_start:
                        # Add slot before lunch
                        if lunch_start - current_time >= timedelta(minutes=preferences['min_task_duration']):
                            available_slots.append({
                                'start_time': current_time,
                                'end_time': lunch_start,
                                'duration_minutes': (lunch_start - current_time).seconds // 60,
                                'date': check_date,
                                'type': 'morning'
                            })
                        current_time = lunch_end
                    
                    # Add slot if it doesn't overlap with lunch
                    if current_time >= lunch_end or event['start_time'] <= lunch_start:
                        duration = (event['start_time'] - current_time).seconds // 60
                        if duration >= preferences['min_task_duration']:
                            available_slots.append({
                                'start_time': current_time,
                                'end_time': event['start_time'],
                                'duration_minutes': duration,
                                'date': check_date,
                                'type': 'afternoon' if current_time.hour >= 12 else 'morning'
                            })
                
                current_time = event['end_time']
            
            # Check for slot after last event
            if current_time < work_end:
                # Handle lunch if not already passed
                if current_time < lunch_start:
                    if lunch_start - current_time >= timedelta(minutes=preferences['min_task_duration']):
                        available_slots.append({
                            'start_time': current_time,
                            'end_time': lunch_start,
                            'duration_minutes': (lunch_start - current_time).seconds // 60,
                            'date': check_date,
                            'type': 'morning'
                        })
                    current_time = lunch_end
                
                # Add final slot
                if current_time < work_end:
                    duration = (work_end - current_time).seconds // 60
                    if duration >= preferences['min_task_duration']:
                        available_slots.append({
                            'start_time': current_time,
                            'end_time': work_end,
                            'duration_minutes': duration,
                            'date': check_date,
                            'type': 'afternoon' if current_time.hour >= 12 else 'morning'
                        })
        
        return available_slots
    
    async def _match_tasks_to_slots(
        self,
        tasks: List[Task],
        slots: List[Dict],
        energy_patterns: Dict,
        preferences: Dict,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Match tasks to optimal time slots using AI"""
        
        scheduled_tasks = []
        used_slots = []
        
        for task in tasks:
            # Skip if task already scheduled (if field exists)
            try:
                if hasattr(task, 'scheduled_for') and task.scheduled_for and task.scheduled_for > datetime.now():
                    continue
            except AttributeError:
                # scheduled_for field doesn't exist yet, continue with task
                pass
            
            # Find best slot for this task
            best_slot = await self._find_best_slot_for_task(
                task,
                [s for s in slots if s not in used_slots],
                energy_patterns,
                preferences
            )
            
            if best_slot:
                scheduled_task = {
                    'task_id': task.id,
                    'task_title': task.title,
                    'task_priority': task.priority.value,
                    'task_type': task.task_type.value if task.task_type else 'general',
                    'scheduled_time': best_slot['start_time'],
                    'duration_minutes': min(
                        task.estimated_duration or 30,
                        best_slot['duration_minutes']
                    ),
                    'confidence': best_slot.get('confidence', 0.8),
                    'reasoning': best_slot.get('reasoning', 'Optimal time based on your patterns')
                }
                
                scheduled_tasks.append(scheduled_task)
                used_slots.append(best_slot)
        
        return scheduled_tasks
    
    async def _find_best_slot_for_task(
        self,
        task: Task,
        available_slots: List[Dict],
        energy_patterns: Dict,
        preferences: Dict
    ) -> Optional[Dict[str, Any]]:
        """Find the best time slot for a specific task"""
        
        if not available_slots:
            return None
        
        # Score each slot based on multiple factors
        slot_scores = []
        
        for slot in available_slots:
            score = 0
            reasoning = []
            
            # Check if slot is long enough
            if slot['duration_minutes'] < (task.estimated_duration or 30):
                continue
            
            # Energy level scoring
            slot_hour = slot['start_time'].hour
            if slot_hour in energy_patterns.get('peak_hours', []):
                score += 30
                reasoning.append("Peak energy time")
            elif slot_hour in energy_patterns.get('low_hours', []):
                score -= 20
                reasoning.append("Low energy time")
            
            # Task type preference scoring
            if task.task_type == TaskType.RESEARCH and slot['type'] == 'morning':
                score += 20
                reasoning.append("Morning is best for deep work")
            elif task.priority == TaskPriority.URGENT:
                # Urgent tasks get bonus for earlier slots
                days_away = (slot['start_time'].date() - datetime.now().date()).days
                score += max(0, 10 - days_away * 2)
                reasoning.append("Scheduled soon due to urgency")
            
            # Day of week scoring
            day_name = slot['start_time'].strftime('%A')
            if day_name in energy_patterns.get('best_days', []):
                score += 10
                reasoning.append(f"{day_name} is a high-energy day")
            
            # Add slot with score
            slot_scores.append({
                **slot,
                'score': score,
                'confidence': min(0.95, 0.5 + score / 100),
                'reasoning': ', '.join(reasoning) if reasoning else 'Standard scheduling'
            })
        
        # Return highest scoring slot
        if slot_scores:
            return max(slot_scores, key=lambda x: x['score'])
        
        return None
    
    async def _analyze_reschedule_context(
        self,
        task: Task,
        reason: Optional[str],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze why a task needs rescheduling"""
        
        context = {
            'task': task,
            'reason': reason or 'User requested reschedule',
            'current_mood': None,
            'current_energy': None,
            'conflicts': []
        }
        
        # Get current mood/energy
        latest_mood = db.query(MoodEntry).filter(
            MoodEntry.user_id == user_id
        ).order_by(MoodEntry.created_at.desc()).first()
        
        if latest_mood:
            context['current_mood'] = latest_mood.mood_level
            context['current_energy'] = latest_mood.energy_level
        
        # Check for calendar conflicts
        if task.scheduled_for:
            conflicts = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time <= task.scheduled_for,
                CalendarEvent.end_time > task.scheduled_for
            ).all()
            
            context['conflicts'] = [
                {'title': c.title, 'time': c.start_time}
                for c in conflicts
            ]
        
        # Generate AI reasoning
        prompt = f"""
        Task "{task.title}" needs rescheduling.
        Reason: {reason}
        Current energy: {context.get('current_energy', 'unknown')}/10
        Conflicts: {len(context['conflicts'])} calendar conflicts
        
        Provide a brief explanation of why rescheduling makes sense.
        """
        
        try:
            response = await self.openai_service.generate_conversational_response(prompt)
            context['reasoning'] = response
        except:
            context['reasoning'] = f"Rescheduling due to: {reason or 'schedule optimization'}"
        
        return context
    
    async def _find_optimal_reschedule_time(
        self,
        task: Task,
        context: Dict,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Find new optimal times for a task that needs rescheduling"""
        
        # Get next 7 days of availability
        energy_patterns = self._analyze_energy_patterns(user_id, db)
        calendar_events = self._get_calendar_events(user_id, 7, db)
        preferences = self._get_user_preferences(user_id, db)
        
        available_slots = self._find_available_slots(
            calendar_events, preferences, 7
        )
        
        # Find top 3 slots
        suggestions = []
        
        for _ in range(3):
            best_slot = await self._find_best_slot_for_task(
                task,
                [s for s in available_slots if s not in [sug['slot'] for sug in suggestions]],
                energy_patterns,
                preferences
            )
            
            if best_slot:
                suggestions.append({
                    'time': best_slot['start_time'].isoformat(),
                    'day': best_slot['start_time'].strftime('%A'),
                    'date': best_slot['start_time'].strftime('%B %d'),
                    'confidence': best_slot.get('confidence', 0.8),
                    'reasoning': best_slot.get('reasoning', 'Good time slot'),
                    'slot': best_slot
                })
        
        return suggestions
    
    def _generate_scheduling_insights(
        self,
        scheduled_tasks: List[Dict],
        energy_patterns: Dict,
        all_tasks: List[Task]
    ) -> List[str]:
        """Generate insights about the scheduling decisions"""
        
        insights = []
        
        # Workload distribution
        scheduled_count = len(scheduled_tasks)
        total_count = len(all_tasks)
        
        if scheduled_count < total_count:
            insights.append(
                f"Scheduled {scheduled_count} of {total_count} tasks. "
                f"Consider breaking down larger tasks or extending your work hours."
            )
        
        # Energy optimization
        if energy_patterns.get('patterns_available'):
            morning_tasks = sum(
                1 for t in scheduled_tasks
                if t['scheduled_time'].hour < 12
            )
            insights.append(
                f"Scheduled {morning_tasks} tasks in the morning when your energy is typically higher."
            )
        
        # Priority alignment
        urgent_scheduled = sum(
            1 for t in scheduled_tasks
            if t['task_priority'] == 'urgent'
        )
        if urgent_scheduled > 0:
            insights.append(
                f"All {urgent_scheduled} urgent tasks have been prioritized in your schedule."
            )
        
        return insights
    
    def _get_unscheduled_tasks(
        self,
        all_tasks: List[Task],
        scheduled_tasks: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Get list of tasks that couldn't be scheduled"""
        
        scheduled_ids = {t['task_id'] for t in scheduled_tasks}
        
        unscheduled = []
        for task in all_tasks:
            if task.id not in scheduled_ids:
                unscheduled.append({
                    'id': task.id,
                    'title': task.title,
                    'priority': task.priority.value,
                    'estimated_duration': task.estimated_duration,
                    'reason': 'No suitable time slot found'
                })
        
        return unscheduled
    
    def _suggest_alternatives(
        self,
        task: Task,
        preferences: Dict
    ) -> List[str]:
        """Suggest alternatives when a task can't be scheduled"""
        
        alternatives = []
        
        if task.estimated_duration and task.estimated_duration > 120:
            alternatives.append(
                "Consider breaking this task into smaller subtasks"
            )
        
        if task.priority != TaskPriority.URGENT:
            alternatives.append(
                "This task could be scheduled for next week when you have more availability"
            )
        
        alternatives.append(
            "You might need to reschedule or delegate other tasks to make room"
        )
        
        return alternatives