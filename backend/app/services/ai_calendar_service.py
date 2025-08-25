#!/usr/bin/env python3
"""
AI Calendar Service

Provides intelligent calendar management with AI-powered scheduling,
goal-based time allocation, and hour-by-hour planning for solopreneurs.
"""

import json
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from .openai_service import OpenAIService
from .autonomous_scheduling_service import AutonomousSchedulingService
from ..models.user import User
from ..models.calendar import CalendarEvent, EventType, EventPriority, SchedulingType
from ..models.goal import Goal, GoalStatus
from ..models.task import Task, TaskStatus, TaskPriority


class AICalendarService:
    """
    AI-powered calendar service for intelligent event management
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.scheduling_service = AutonomousSchedulingService()
        
    async def create_smart_event(
        self,
        user_id: int,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Create a calendar event with AI-powered optimization
        """
        
        # Extract basic event information
        title = event_data.get('title')
        description = event_data.get('description', '')
        duration_minutes = event_data.get('duration_minutes', 60)
        event_type = event_data.get('event_type', EventType.TASK)
        priority = event_data.get('priority', EventPriority.MEDIUM)
        goal_id = event_data.get('goal_id')
        
        # Get user's goals and context
        user_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == GoalStatus.ACTIVE
        ).all()
        
        # AI analysis of the event
        ai_analysis = await self._analyze_event_with_ai(
            title, description, event_type, user_goals
        )
        
        # Find optimal time slot
        suggested_time = event_data.get('suggested_time')
        if not suggested_time:
            optimal_time = await self._find_optimal_time_for_event(
                user_id, event_data, ai_analysis, db
            )
        else:
            optimal_time = {
                'start_time': datetime.fromisoformat(suggested_time),
                'confidence': 0.9,
                'reasoning': 'User specified time'
            }
        
        if not optimal_time:
            return {
                'success': False,
                'error': 'No suitable time slot found',
                'alternatives': await self._suggest_alternatives(user_id, event_data, db)
            }
        
        # Get Eisenhower Matrix classification
        user_context = await self._get_user_context(user_id, db)
        eisenhower_result = await self.classify_eisenhower_matrix(
            event_title=title,
            event_description=description,
            user_context=user_context,
            goal_related=bool(goal_id)
        )
        
        eisenhower_classification = eisenhower_result.get('classification', {})
        
        # Create the calendar event with AI enhancements
        calendar_event = CalendarEvent(
            user_id=user_id,
            title=title,
            description=description,
            event_type=event_type,
            start_time=optimal_time['start_time'],
            end_time=optimal_time['start_time'] + timedelta(minutes=duration_minutes),
            goal_id=goal_id,
            
            # AI Scheduling Fields
            priority=priority,
            scheduling_type=SchedulingType.AI_SUGGESTED if not suggested_time else SchedulingType.MANUAL,
            energy_required=ai_analysis.get('energy_required', 5),
            optimal_time_of_day=ai_analysis.get('optimal_time_of_day', 'morning'),
            ai_reasoning=optimal_time.get('reasoning', ''),
            flexibility=ai_analysis.get('flexibility', 30),
            
            # Eisenhower Matrix Fields
            eisenhower_quadrant=eisenhower_classification.get('quadrant'),
            is_urgent=eisenhower_classification.get('is_urgent', False),
            is_important=eisenhower_classification.get('is_important', True),
            urgency_reason=eisenhower_classification.get('urgency_reason'),
            importance_reason=eisenhower_classification.get('importance_reason'),
            
            # Goal Integration
            contributes_to_goal=bool(goal_id) or ai_analysis.get('contributes_to_goal', False),
            goal_weight=ai_analysis.get('goal_weight', 5),
            
            # Scheduling Metadata
            auto_scheduled=not suggested_time,
            user_confirmed=bool(suggested_time),
            
            # Time Optimization
            focus_level_required=ai_analysis.get('focus_level_required', 5),
            break_before=ai_analysis.get('break_before', 0),
            break_after=ai_analysis.get('break_after', 0),
            can_be_interrupted=ai_analysis.get('can_be_interrupted', True),
            
            # AI insights
            ai_insights=ai_analysis,
            mood_impact_prediction=ai_analysis.get('mood_impact_prediction', 0)
        )
        
        db.add(calendar_event)
        db.commit()
        db.refresh(calendar_event)
        
        # Sync to Google Calendar if connected
        google_synced = False
        google_event_url = None
        try:
            from app.services.google_calendar_service import GoogleCalendarService
            google_service = GoogleCalendarService()
            
            if google_service.is_calendar_connected(user_id):
                google_result = google_service.create_calendar_event(
                    user_id,
                    {
                        'title': title,
                        'description': f"{description}\n\n🤖 AI-scheduled for optimal productivity\n🎯 Goal: {goal_id if goal_id else 'General productivity'}",
                        'start_time': calendar_event.start_time,
                        'end_time': calendar_event.end_time
                    }
                )
                
                if google_result['success']:
                    calendar_event.google_event_id = google_result['event_id']
                    calendar_event.is_synced = True
                    calendar_event.sync_status = "synced"
                    google_synced = True
                    google_event_url = google_result.get('event_url')
                    db.commit()
                    
        except Exception as sync_error:
            print(f"Google Calendar sync failed: {sync_error}")
            # Don't fail the entire operation if sync fails
        
        return {
            'success': True,
            'event_id': calendar_event.id,
            'scheduled_time': calendar_event.start_time.isoformat(),
            'confidence': optimal_time.get('confidence', 0.8),
            'ai_reasoning': calendar_event.ai_reasoning,
            'contributes_to_goals': calendar_event.contributes_to_goal,
            'recommendations': ai_analysis.get('recommendations', []),
            'google_synced': google_synced,
            'google_event_url': google_event_url
        }
    
    async def update_event_intelligently(
        self,
        event_id: int,
        user_id: int,
        updates: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Update a calendar event with AI optimization
        """
        
        event = db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == user_id
        ).first()
        
        if not event:
            return {'success': False, 'error': 'Event not found'}
        
        # Check if time change is requested
        new_time = updates.get('start_time')
        if new_time:
            # Validate the new time with AI
            validation = await self._validate_time_change(
                event, datetime.fromisoformat(new_time), user_id, db
            )
            
            if not validation['is_optimal']:
                return {
                    'success': False,
                    'warning': validation['warning'],
                    'better_alternatives': validation['alternatives'],
                    'proceed_anyway': True  # User can override
                }
        
        # Apply updates
        for field, value in updates.items():
            if field == 'start_time':
                event.start_time = datetime.fromisoformat(value)
                event.end_time = event.start_time + (event.end_time - event.start_time)  # Preserve duration
                event.reschedule_count += 1
                event.last_rescheduled = datetime.now()
            elif field == 'duration_minutes':
                duration = timedelta(minutes=int(value))
                event.end_time = event.start_time + duration
            elif hasattr(event, field):
                setattr(event, field, value)
        
        db.commit()
        
        return {
            'success': True,
            'event_id': event.id,
            'updated_fields': list(updates.keys()),
            'new_schedule': {
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat()
            }
        }
    
    async def delete_event_and_reschedule(
        self,
        event_id: int,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Delete an event and intelligently reschedule affected tasks
        """
        
        event = db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == user_id
        ).first()
        
        if not event:
            return {'success': False, 'error': 'Event not found'}
        
        # Check if this event was goal-related
        was_goal_related = event.contributes_to_goal
        freed_time_slot = {
            'start': event.start_time,
            'end': event.end_time,
            'duration_minutes': (event.end_time - event.start_time).seconds // 60
        }
        
        # Delete the event
        db.delete(event)
        db.commit()
        
        # If it was goal-related, suggest rescheduling
        recommendations = []
        if was_goal_related:
            recommendations = await self._suggest_goal_time_reallocation(
                user_id, freed_time_slot, db
            )
        
        return {
            'success': True,
            'freed_time_slot': {
                'start_time': freed_time_slot['start'].isoformat(),
                'end_time': freed_time_slot['end'].isoformat(),
                'duration_minutes': freed_time_slot['duration_minutes']
            },
            'recommendations': recommendations,
            'was_goal_related': was_goal_related
        }
    
    async def generate_hourly_schedule(
        self,
        user_id: int,
        date: str,  # YYYY-MM-DD
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate an hour-by-hour AI schedule for a specific date
        """
        
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get user's goals and priorities
        user_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == GoalStatus.ACTIVE
        ).all()
        
        # Get existing events for the day
        start_of_day = datetime.combine(target_date, time(0, 0))
        end_of_day = datetime.combine(target_date, time(23, 59))
        
        existing_events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_of_day,
            CalendarEvent.start_time <= end_of_day
        ).order_by(CalendarEvent.start_time).all()
        
        # Generate AI-powered hourly schedule
        ai_schedule = await self._generate_ai_hourly_schedule(
            user_id, target_date, user_goals, existing_events, db
        )
        
        return {
            'date': date,
            'hourly_schedule': ai_schedule,
            'existing_events_count': len(existing_events),
            'ai_generated_slots': len([s for s in ai_schedule if s.get('ai_generated', False)]),
            'productivity_score': self._calculate_productivity_score(ai_schedule),
            'goal_alignment_score': self._calculate_goal_alignment_score(ai_schedule, user_goals)
        }
    
    async def optimize_weekly_schedule(
        self,
        user_id: int,
        week_start_date: str,  # YYYY-MM-DD (Monday)
        db: Session
    ) -> Dict[str, Any]:
        """
        Optimize an entire week's schedule based on goals and priorities
        """
        
        week_start = datetime.strptime(week_start_date, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
        
        # Get week's events
        week_events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= datetime.combine(week_start, time(0, 0)),
            CalendarEvent.start_time <= datetime.combine(week_end, time(23, 59))
        ).order_by(CalendarEvent.start_time).all()
        
        # Get user's goals
        user_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == GoalStatus.ACTIVE
        ).all()
        
        # Analyze current week distribution
        analysis = await self._analyze_weekly_distribution(
            user_id, week_events, user_goals, db
        )
        
        # Generate optimization suggestions
        optimizations = await self._generate_weekly_optimizations(
            user_id, week_events, analysis, db
        )
        
        return {
            'week_start': week_start_date,
            'current_analysis': analysis,
            'optimization_suggestions': optimizations,
            'estimated_improvement': analysis.get('improvement_potential', 'moderate'),
            'goal_progress_impact': analysis.get('goal_impact', 'positive')
        }
    
    async def _analyze_event_with_ai(
        self,
        title: str,
        description: str,
        event_type: EventType,
        user_goals: List[Goal]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze an event and suggest optimal parameters
        """
        
        goals_context = "\n".join([
            f"- {goal.title} ({goal.category.value}, {goal.progress:.0f}% complete)"
            for goal in user_goals
        ]) if user_goals else "No active goals"
        
        prompt = f"""
        Analyze this calendar event and suggest optimal scheduling parameters:
        
        Event: {title}
        Description: {description}
        Type: {event_type.value}
        
        User's Active Goals:
        {goals_context}
        
        Provide analysis in JSON format:
        {{
            "energy_required": 1-10,
            "focus_level_required": 1-10,
            "optimal_time_of_day": "morning/afternoon/evening",
            "flexibility": 0-120 (minutes can be moved),
            "break_before": 0-30 (minutes break needed before),
            "break_after": 0-30 (minutes break needed after),
            "can_be_interrupted": true/false,
            "contributes_to_goal": true/false,
            "goal_weight": 1-10 (if contributes to goal),
            "mood_impact_prediction": -5 to +5,
            "recommendations": ["specific suggestions for this event"]
        }}
        
        Consider:
        - Type of work required
        - Cognitive load
        - Goal alignment
        - Typical energy patterns for this work
        """
        
        try:
            response = await self.openai_service.generate_task_breakdown(prompt)
            return json.loads(response)
        except Exception as e:
            # Fallback analysis
            return {
                "energy_required": 5,
                "focus_level_required": 5,
                "optimal_time_of_day": "morning",
                "flexibility": 30,
                "break_before": 0,
                "break_after": 5,
                "can_be_interrupted": True,
                "contributes_to_goal": False,
                "goal_weight": 5,
                "mood_impact_prediction": 0,
                "recommendations": ["Consider breaking into smaller tasks if complex"]
            }
    
    async def _find_optimal_time_for_event(
        self,
        user_id: int,
        event_data: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        db: Session,
        eisenhower_classification: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the optimal time slot for an event using Eisenhower Matrix priorities
        """
        
        # Use autonomous scheduling service to find best slot
        duration_minutes = event_data.get('duration_minutes', 60)
        
        # Get Eisenhower Matrix classification if not provided
        if not eisenhower_classification:
            user_context = await self._get_user_context(user_id, db)
            eisenhower_result = await self.classify_eisenhower_matrix(
                event_title=event_data.get('title', 'Event'),
                event_description=event_data.get('description', ''),
                user_context=user_context,
                goal_related=bool(event_data.get('goal_id'))
            )
            eisenhower_classification = eisenhower_result.get('classification', {})
        
        # Apply Eisenhower Matrix scheduling preferences
        quadrant = eisenhower_classification.get('quadrant', 'q2_not_urgent_important')
        
        # Determine optimal scheduling window based on quadrant
        if quadrant == 'q1_urgent_important':
            # Q1: Schedule ASAP (within next 2 days)
            max_days_ahead = 2
            prefer_morning = True
            priority_score = 4
        elif quadrant == 'q2_not_urgent_important':
            # Q2: Schedule in focused time slots (morning preferred)
            max_days_ahead = 14
            prefer_morning = True  
            priority_score = 3
        elif quadrant == 'q3_urgent_not_important':
            # Q3: Schedule in less optimal times, consider delegation
            max_days_ahead = 3
            prefer_morning = False
            priority_score = 2
        else:  # Q4
            # Q4: Schedule only if absolutely necessary, in low-energy times
            max_days_ahead = 7
            prefer_morning = False
            priority_score = 1
        
        # Create a temporary task object for scheduling
        temp_task = type('TempTask', (), {
            'id': 0,
            'title': event_data.get('title', 'Event'),
            'estimated_duration': duration_minutes,
            'priority': event_data.get('priority', TaskPriority.MEDIUM),
            'task_type': None
        })
        
        # Get available slots for next 14 days
        calendar_events = self.scheduling_service._get_calendar_events(user_id, 14, db)
        preferences = self.scheduling_service._get_user_preferences(user_id, db)
        energy_patterns = self.scheduling_service._analyze_energy_patterns(user_id, db)
        
        available_slots = self.scheduling_service._find_available_slots(
            calendar_events, preferences, 14
        )
        
        # Filter slots based on AI analysis preferences
        optimal_time_of_day = ai_analysis.get('optimal_time_of_day', 'morning')
        if optimal_time_of_day == 'morning':
            available_slots = [s for s in available_slots if s['start_time'].hour < 12]
        elif optimal_time_of_day == 'afternoon':
            available_slots = [s for s in available_slots if 12 <= s['start_time'].hour < 17]
        elif optimal_time_of_day == 'evening':
            available_slots = [s for s in available_slots if s['start_time'].hour >= 17]
        
        # Find best slot
        best_slot = await self.scheduling_service._find_best_slot_for_task(
            temp_task, available_slots, energy_patterns, preferences
        )
        
        return best_slot
    
    async def _generate_ai_hourly_schedule(
        self,
        user_id: int,
        target_date: datetime.date,
        user_goals: List[Goal],
        existing_events: List[CalendarEvent],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Generate hour-by-hour AI schedule for solopreneurs
        """
        
        # Create hourly slots from 6 AM to 10 PM
        schedule = []
        current_time = datetime.combine(target_date, time(6, 0))
        end_time = datetime.combine(target_date, time(22, 0))
        
        # Map existing events by hour
        existing_by_hour = {}
        for event in existing_events:
            hour = event.start_time.hour
            if hour not in existing_by_hour:
                existing_by_hour[hour] = []
            existing_by_hour[hour].append(event)
        
        # Get energy patterns for the user
        energy_patterns = self.scheduling_service._analyze_energy_patterns(user_id, db)
        
        while current_time < end_time:
            hour = current_time.hour
            
            if hour in existing_by_hour:
                # Existing event
                event = existing_by_hour[hour][0]  # Take first event in this hour
                schedule.append({
                    'hour': f"{hour:02d}:00",
                    'type': 'existing_event',
                    'title': event.title,
                    'event_type': event.event_type.value,
                    'duration_minutes': (event.end_time - event.start_time).seconds // 60,
                    'ai_generated': False,
                    'goal_related': event.contributes_to_goal
                })
            else:
                # Generate AI suggestion for this hour
                ai_suggestion = await self._suggest_hour_activity(
                    user_id, hour, target_date, user_goals, energy_patterns
                )
                schedule.append({
                    'hour': f"{hour:02d}:00",
                    'type': 'ai_suggestion',
                    'title': ai_suggestion['title'],
                    'description': ai_suggestion['description'],
                    'event_type': ai_suggestion['event_type'],
                    'duration_minutes': 60,
                    'ai_generated': True,
                    'goal_related': ai_suggestion['goal_related'],
                    'energy_match': ai_suggestion['energy_match'],
                    'priority': ai_suggestion['priority']
                })
            
            current_time += timedelta(hours=1)
        
        return schedule
    
    async def _suggest_hour_activity(
        self,
        user_id: int,
        hour: int,
        target_date: datetime.date,
        user_goals: List[Goal],
        energy_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest optimal activity for a specific hour
        """
        
        # Determine energy level for this hour
        energy_level = energy_patterns.get('energy_by_hour', {}).get(hour, 5)
        
        # Standard schedule structure for solopreneurs
        if 6 <= hour <= 8:
            return {
                'title': 'Morning Routine',
                'description': 'Personal development, exercise, planning',
                'event_type': 'personal',
                'goal_related': True,
                'energy_match': 'high',
                'priority': 'high'
            }
        elif 9 <= hour <= 11:
            if energy_level >= 7:
                return {
                    'title': 'Deep Work Block',
                    'description': 'Most important goal work when energy is peak',
                    'event_type': 'deep_work',
                    'goal_related': True,
                    'energy_match': 'perfect',
                    'priority': 'urgent'
                }
            else:
                return {
                    'title': 'Strategic Planning',
                    'description': 'Review goals, plan next actions',
                    'event_type': 'planning',
                    'goal_related': True,
                    'energy_match': 'good',
                    'priority': 'high'
                }
        elif hour == 12:
            return {
                'title': 'Lunch Break',
                'description': 'Meal and mental reset',
                'event_type': 'break',
                'goal_related': False,
                'energy_match': 'recovery',
                'priority': 'medium'
            }
        elif 13 <= hour <= 15:
            return {
                'title': 'Client/Business Work',
                'description': 'Revenue-generating activities',
                'event_type': 'goal_work',
                'goal_related': True,
                'energy_match': 'good',
                'priority': 'high'
            }
        elif 16 <= hour <= 17:
            return {
                'title': 'Learning & Skill Development',
                'description': 'Courses, reading, skill building',
                'event_type': 'learning',
                'goal_related': True,
                'energy_match': 'moderate',
                'priority': 'medium'
            }
        elif 18 <= hour <= 19:
            return {
                'title': 'Admin & Communication',
                'description': 'Emails, admin tasks, networking',
                'event_type': 'admin',
                'goal_related': False,
                'energy_match': 'low',
                'priority': 'medium'
            }
        else:
            return {
                'title': 'Personal Time',
                'description': 'Rest, family, personal activities',
                'event_type': 'personal',
                'goal_related': False,
                'energy_match': 'rest',
                'priority': 'low'
            }
    
    def _calculate_productivity_score(self, schedule: List[Dict[str, Any]]) -> float:
        """Calculate productivity score for a schedule"""
        
        total_hours = len(schedule)
        if total_hours == 0:
            return 0.0
        
        productive_hours = sum(1 for slot in schedule if slot.get('goal_related', False))
        return round((productive_hours / total_hours) * 100, 1)
    
    def _calculate_goal_alignment_score(
        self,
        schedule: List[Dict[str, Any]],
        user_goals: List[Goal]
    ) -> float:
        """Calculate how well the schedule aligns with user goals"""
        
        if not user_goals:
            return 0.0
        
        goal_related_slots = [s for s in schedule if s.get('goal_related', False)]
        total_slots = len(schedule)
        
        if total_slots == 0:
            return 0.0
        
        return round((len(goal_related_slots) / total_slots) * 100, 1)
    
    async def _validate_time_change(
        self,
        event: CalendarEvent,
        new_time: datetime,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Validate if a time change is optimal
        """
        
        # Check for conflicts
        conflicts = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.id != event.id,
            CalendarEvent.start_time <= new_time,
            CalendarEvent.end_time > new_time
        ).count()
        
        if conflicts > 0:
            return {
                'is_optimal': False,
                'warning': 'Time conflict with existing event',
                'alternatives': []
            }
        
        # Check energy patterns
        energy_patterns = self.scheduling_service._analyze_energy_patterns(user_id, db)
        hour = new_time.hour
        
        if hour in energy_patterns.get('low_hours', []):
            return {
                'is_optimal': False,
                'warning': 'This time is typically low energy for you',
                'alternatives': []
            }
        
        return {'is_optimal': True}
    
    async def _suggest_alternatives(
        self,
        user_id: int,
        event_data: Dict[str, Any],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative times when no optimal slot is found
        """
        
        # This would implement alternative suggestions
        # For now, return placeholder
        return [
            {
                'time': (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0).isoformat(),
                'reason': 'Tomorrow morning during peak energy hours'
            }
        ]
    
    async def _suggest_goal_time_reallocation(
        self,
        user_id: int,
        freed_slot: Dict[str, Any],
        db: Session
    ) -> List[str]:
        """
        Suggest how to use freed time for goal achievement
        """
        
        user_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == GoalStatus.ACTIVE
        ).order_by(Goal.priority.desc()).limit(3).all()
        
        recommendations = []
        if user_goals:
            recommendations.append(
                f"Use this time for '{user_goals[0].title}' - your highest priority goal"
            )
            recommendations.append(
                "Consider scheduling a deep work block for goal-related tasks"
            )
        
        return recommendations
    
    async def _analyze_weekly_distribution(
        self,
        user_id: int,
        week_events: List[CalendarEvent],
        user_goals: List[Goal],
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze how well the week is distributed for goal achievement
        """
        
        total_hours = sum(
            (event.end_time - event.start_time).seconds // 3600
            for event in week_events
        )
        
        goal_hours = sum(
            (event.end_time - event.start_time).seconds // 3600
            for event in week_events if event.contributes_to_goal
        )
        
        return {
            'total_scheduled_hours': total_hours,
            'goal_related_hours': goal_hours,
            'goal_percentage': (goal_hours / total_hours * 100) if total_hours > 0 else 0,
            'improvement_potential': 'high' if goal_hours < total_hours * 0.6 else 'moderate',
            'goal_impact': 'positive' if goal_hours > total_hours * 0.4 else 'needs_improvement'
        }
    
    async def _generate_weekly_optimizations(
        self,
        user_id: int,
        week_events: List[CalendarEvent],
        analysis: Dict[str, Any],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Generate optimization suggestions for the week
        """
        
        optimizations = []
        
        if analysis['goal_percentage'] < 50:
            optimizations.append({
                'type': 'goal_focus',
                'title': 'Increase Goal-Related Time',
                'description': f"Only {analysis['goal_percentage']:.1f}% of your week is goal-focused. Aim for 60%+",
                'impact': 'high'
            })
        
        # Add more optimization logic here
        
        return optimizations
    
    async def classify_eisenhower_matrix(
        self,
        event_title: str,
        event_description: str,
        user_context: Dict[str, Any],
        goal_related: bool = False
    ) -> Dict[str, Any]:
        """
        Use AI to classify an event into the Eisenhower Matrix quadrants
        """
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            classification_prompt = f"""
You are an expert productivity consultant. Analyze this task/event and classify it using the Eisenhower Matrix.

EISENHOWER MATRIX QUADRANTS:
1. Q1 (Urgent + Important): Crisis, emergencies, deadlines TODAY/TOMORROW, critical problems
2. Q2 (Not Urgent + Important): Goal work, planning, skill development, relationship building, prevention
3. Q3 (Urgent + Not Important): Interruptions, some emails, non-essential meetings, busy work with deadlines
4. Q4 (Not Urgent + Not Important): Time wasters, excessive social media, trivial activities, mindless browsing

USER CONTEXT:
- Goals: {user_context.get('goals', 'Not specified')}
- Work Focus: {user_context.get('work_focus', 'General productivity')}
- Current Priorities: {user_context.get('priorities', 'Not specified')}

EVENT TO CLASSIFY:
- Title: "{event_title}"
- Description: "{event_description or 'No description'}"
- Is Goal-Related: {goal_related}

CLASSIFICATION RULES:
- Urgent = Has a deadline within 2-3 days OR is time-sensitive
- Important = Contributes to goals, values, or long-term success

Return JSON:
{{
  "quadrant": "q1_urgent_important|q2_not_urgent_important|q3_urgent_not_important|q4_not_urgent_not_important",
  "is_urgent": true/false,
  "is_important": true/false,
  "urgency_reason": "Why this is urgent (deadline, dependency, etc.) or null",
  "importance_reason": "Why this is important (goal contribution, impact, etc.) or null",
  "confidence": 0.95,
  "scheduling_recommendation": "do_first|schedule|delegate|eliminate",
  "optimal_time_allocation": "How much time should be spent on this type of task"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": classification_prompt},
                    {"role": "user", "content": f"Classify: {event_title}"}
                ],
                temperature=0.3
            )
            
            import json
            classification = json.loads(response.choices[0].message.content)
            
            return {
                'success': True,
                'classification': classification
            }
            
        except Exception as e:
            # Fallback classification based on keywords
            return self._fallback_eisenhower_classification(event_title, event_description, goal_related)
    
    def _fallback_eisenhower_classification(
        self,
        event_title: str,
        event_description: str,
        goal_related: bool
    ) -> Dict[str, Any]:
        """
        Fallback classification when AI fails
        """
        title_lower = event_title.lower()
        desc_lower = (event_description or "").lower()
        
        # Urgent keywords
        urgent_keywords = ['urgent', 'asap', 'today', 'tomorrow', 'deadline', 'due', 'emergency', 'crisis', 'meeting']
        is_urgent = any(keyword in title_lower or keyword in desc_lower for keyword in urgent_keywords)
        
        # Important keywords (goal-related activities)
        important_keywords = ['goal', 'strategy', 'planning', 'development', 'learning', 'growth', 'important']
        is_important = goal_related or any(keyword in title_lower or keyword in desc_lower for keyword in important_keywords)
        
        # Default to important if unclear
        if not is_urgent and not is_important:
            is_important = True
        
        # Determine quadrant
        if is_urgent and is_important:
            quadrant = "q1_urgent_important"
            recommendation = "do_first"
        elif not is_urgent and is_important:
            quadrant = "q2_not_urgent_important"
            recommendation = "schedule"
        elif is_urgent and not is_important:
            quadrant = "q3_urgent_not_important"
            recommendation = "delegate"
        else:
            quadrant = "q4_not_urgent_not_important"
            recommendation = "eliminate"
        
        return {
            'success': True,
            'classification': {
                'quadrant': quadrant,
                'is_urgent': is_urgent,
                'is_important': is_important,
                'urgency_reason': "Keyword analysis" if is_urgent else None,
                'importance_reason': "Goal-related activity" if goal_related else "Keyword analysis" if is_important else None,
                'confidence': 0.7,
                'scheduling_recommendation': recommendation,
                'optimal_time_allocation': "Focus time for high-impact work"
            }
        }
    
    async def _get_user_context(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Get user context for Eisenhower Matrix classification
        """
        try:
            from app.models import User
            from app.models.goal import Goal
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Get user's goals
            goals = db.query(Goal).filter(Goal.user_id == user_id).all()
            goal_titles = [goal.title for goal in goals] if goals else []
            
            return {
                'goals': goal_titles,
                'work_focus': getattr(user, 'industry', 'General productivity'),
                'priorities': getattr(user, 'primary_challenges', 'Productivity optimization'),
                'experience_level': getattr(user, 'experience_level', 'intermediate')
            }
        except Exception as e:
            print(f"Error getting user context: {e}")
            return {
                'goals': [],
                'work_focus': 'General productivity',
                'priorities': 'Productivity optimization'
            }
    
    async def smart_reschedule_dependent_events(
        self,
        moved_event_id: int,
        new_start_time: datetime,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        When an event moves, automatically reschedule dependent events
        """
        try:
            from app.models.calendar import CalendarEvent
            
            # Get the moved event
            moved_event = db.query(CalendarEvent).filter(
                CalendarEvent.id == moved_event_id,
                CalendarEvent.user_id == user_id
            ).first()
            
            if not moved_event:
                return {'success': False, 'error': 'Event not found'}
            
            # Find all events that depend on this event
            dependent_events = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.depends_on_event_ids.like(f'%{moved_event_id}%')
            ).all()
            
            # Find all events that this event depends on (to check constraints)
            blocking_events = []
            if moved_event.depends_on_event_ids:
                blocking_ids = moved_event.depends_on_event_ids if isinstance(moved_event.depends_on_event_ids, list) else []
                if blocking_ids:
                    blocking_events = db.query(CalendarEvent).filter(
                        CalendarEvent.id.in_(blocking_ids),
                        CalendarEvent.user_id == user_id
                    ).all()
            
            rescheduled_events = []
            conflicts = []
            
            # Calculate new duration and end time for moved event
            original_duration = moved_event.end_time - moved_event.start_time
            new_end_time = new_start_time + original_duration
            
            # Update the moved event first
            moved_event.start_time = new_start_time
            moved_event.end_time = new_end_time
            moved_event.reschedule_count += 1
            moved_event.last_rescheduled = datetime.utcnow()
            
            # Process dependent events
            for dependent_event in dependent_events:
                if not dependent_event.auto_reschedule_enabled:
                    conflicts.append({
                        'event_id': dependent_event.id,
                        'title': dependent_event.title,
                        'reason': 'Auto-reschedule disabled',
                        'action_required': 'Manual rescheduling needed'
                    })
                    continue
                
                # Determine new time based on dependency type
                dependency_type = dependent_event.dependency_type or 'sequential'
                buffer_minutes = dependent_event.reschedule_buffer_minutes or 15
                
                if dependency_type == 'sequential':
                    # This event should start after the moved event ends
                    suggested_start = new_end_time + timedelta(minutes=buffer_minutes)
                elif dependency_type == 'same_day':
                    # Keep on same day but after the moved event
                    if new_start_time.date() == dependent_event.start_time.date():
                        suggested_start = max(new_end_time + timedelta(minutes=buffer_minutes), dependent_event.start_time)
                    else:
                        # Move to the new day
                        suggested_start = datetime.combine(new_start_time.date(), dependent_event.start_time.time())
                        if suggested_start <= new_end_time:
                            suggested_start = new_end_time + timedelta(minutes=buffer_minutes)
                else:  # before_deadline
                    # Ensure dependent event happens before any deadline constraints
                    suggested_start = dependent_event.start_time  # Keep original if possible
                
                # Check for conflicts with existing events
                event_duration = dependent_event.end_time - dependent_event.start_time
                suggested_end = suggested_start + event_duration
                
                # Find a conflict-free slot
                final_start_time = await self._find_conflict_free_slot(
                    user_id, suggested_start, event_duration, dependent_event.id, db
                )
                
                if final_start_time:
                    # Update dependent event
                    dependent_event.start_time = final_start_time
                    dependent_event.end_time = final_start_time + event_duration
                    dependent_event.reschedule_count += 1
                    dependent_event.last_rescheduled = datetime.utcnow()
                    
                    rescheduled_events.append({
                        'event_id': dependent_event.id,
                        'title': dependent_event.title,
                        'old_time': suggested_start.isoformat(),
                        'new_time': final_start_time.isoformat(),
                        'dependency_type': dependency_type,
                        'reason': f'Auto-rescheduled due to {moved_event.title} moving'
                    })
                else:
                    conflicts.append({
                        'event_id': dependent_event.id,
                        'title': dependent_event.title,
                        'reason': 'No available time slot found',
                        'action_required': 'Manual rescheduling needed'
                    })
            
            # Commit all changes
            db.commit()
            
            return {
                'success': True,
                'moved_event': {
                    'id': moved_event_id,
                    'title': moved_event.title,
                    'new_time': new_start_time.isoformat()
                },
                'rescheduled_events': rescheduled_events,
                'conflicts': conflicts,
                'summary': {
                    'events_rescheduled': len(rescheduled_events),
                    'conflicts_found': len(conflicts),
                    'total_affected': len(dependent_events)
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'error': f'Smart rescheduling failed: {str(e)}'
            }
    
    async def _find_conflict_free_slot(
        self,
        user_id: int,
        preferred_start: datetime,
        duration: timedelta,
        exclude_event_id: int,
        db: Session,
        max_search_days: int = 7
    ) -> Optional[datetime]:
        """
        Find a conflict-free time slot for an event
        """
        from app.models.calendar import CalendarEvent
        
        current_time = preferred_start
        search_end = preferred_start + timedelta(days=max_search_days)
        
        while current_time < search_end:
            potential_end = current_time + duration
            
            # Check for conflicts with existing events
            conflicts = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.id != exclude_event_id,
                CalendarEvent.start_time < potential_end,
                CalendarEvent.end_time > current_time
            ).count()
            
            if conflicts == 0:
                # Check if it's within reasonable working hours (8 AM - 8 PM)
                hour = current_time.hour
                if 8 <= hour <= 20:
                    return current_time
            
            # Move to next 30-minute slot
            current_time += timedelta(minutes=30)
        
        return None
    
    async def detect_event_dependencies(
        self,
        event_title: str,
        event_description: str,
        existing_events: List,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Use AI to detect potential dependencies between events
        """
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Create event list for analysis
            event_list = "\n".join([
                f"- {event.title} ({event.start_time.strftime('%Y-%m-%d %H:%M')})" 
                for event in existing_events[:20]  # Limit to recent events
            ])
            
            dependency_prompt = f"""
Analyze this new event and identify potential dependencies with existing events.

NEW EVENT:
- Title: "{event_title}"
- Description: "{event_description or 'No description'}"

EXISTING EVENTS:
{event_list}

DEPENDENCY TYPES:
1. SEQUENTIAL: Event B must happen after Event A completes
2. SAME_DAY: Events should happen on the same day
3. BEFORE_DEADLINE: Event must happen before a deadline event
4. PREPARATION: Event A is preparation for Event B

Return JSON:
{{
  "dependencies_found": true/false,
  "dependent_events": [
    {{
      "event_title": "Existing event title",
      "dependency_type": "sequential|same_day|before_deadline|preparation",
      "relationship": "This new event depends on existing event OR existing event depends on this new event",
      "reason": "Why these events are related",
      "confidence": 0.9
    }}
  ],
  "suggestions": [
    "Scheduling suggestions based on dependencies"
  ]
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": dependency_prompt},
                    {"role": "user", "content": f"Analyze dependencies for: {event_title}"}
                ],
                temperature=0.3
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            return {
                'success': True,
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Dependency detection failed: {str(e)}',
                'analysis': {
                    'dependencies_found': False,
                    'dependent_events': [],
                    'suggestions': []
                }
            }