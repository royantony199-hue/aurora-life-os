#!/usr/bin/env python3
"""
Voice Command Processing Service
Handles natural language parsing for quick actions and commands
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.goal import Goal, GoalStatus, GoalCategory
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..models.mood import MoodEntry
from ..models.calendar import CalendarEvent
from .openai_service import OpenAIService


class VoiceCommandService:
    """
    Service for parsing natural language commands into structured actions
    Supports goals, tasks, calendar, and mood operations
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def parse_command(self, command: str, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Parse a natural language command and return structured action data
        """
        command = command.strip().lower()
        
        # Try pattern matching first for common commands
        pattern_result = self._try_pattern_matching(command, user_id, db)
        if pattern_result:
            return pattern_result
        
        # Fall back to AI parsing for complex commands
        ai_result = await self._ai_parse_command(command, user_id, db)
        return ai_result
    
    def _try_pattern_matching(self, command: str, user_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Try to match command against common patterns"""
        
        # Mood commands
        if any(phrase in command for phrase in ['feeling', 'mood', 'how am i']):
            mood_match = re.search(r'(\d+)/10|(\d+) out of 10|mood (\d+)', command)
            if mood_match:
                mood_value = int(mood_match.group(1) or mood_match.group(2) or mood_match.group(3))
                if 1 <= mood_value <= 10:
                    return {
                        'action': 'log_mood',
                        'parameters': {'mood_level': mood_value},
                        'confidence': 0.9
                    }
        
        # Goal creation commands
        if command.startswith(('create goal', 'add goal', 'new goal')):
            goal_text = re.sub(r'^(create|add|new)\s+goal\s+', '', command)
            if goal_text:
                return {
                    'action': 'create_goal',
                    'parameters': {
                        'title': goal_text.title(),
                        'category': 'personal'
                    },
                    'confidence': 0.8
                }
        
        # Task creation commands
        if command.startswith(('add task', 'create task', 'new task', 'todo')):
            task_text = re.sub(r'^(add|create|new)\s+(task|todo)\s+', '', command)
            if not task_text:
                task_text = re.sub(r'^todo\s+', '', command)
            if task_text:
                return {
                    'action': 'create_task',
                    'parameters': {
                        'title': task_text.title(),
                        'priority': 'medium'
                    },
                    'confidence': 0.8
                }
        
        # Calendar/schedule queries
        if any(phrase in command for phrase in ['what\'s next', 'schedule today', 'calendar', 'meetings']):
            return {
                'action': 'show_schedule',
                'parameters': {'days': 1},
                'confidence': 0.7
            }
        
        # Goal status queries
        if any(phrase in command for phrase in ['my goals', 'goal progress', 'how am i doing']):
            return {
                'action': 'show_goals',
                'parameters': {},
                'confidence': 0.8
            }
        
        # Task status queries
        if any(phrase in command for phrase in ['my tasks', 'what should i do', 'next task']):
            return {
                'action': 'suggest_task',
                'parameters': {},
                'confidence': 0.8
            }
        
        # Quick reschedule commands
        if any(phrase in command for phrase in ['reschedule', 'move', 'postpone']):
            return {
                'action': 'reschedule_help',
                'parameters': {'command': command},
                'confidence': 0.6
            }
        
        return None
    
    async def _ai_parse_command(self, command: str, user_id: int, db: Session) -> Dict[str, Any]:
        """Use AI to parse complex commands"""
        try:
            # Get user context
            user = db.query(User).filter(User.id == user_id).first()
            recent_goals = db.query(Goal).filter(Goal.user_id == user_id).limit(5).all()
            
            context = f"User: {user.full_name if user else 'Unknown'}\n"
            context += f"Recent goals: {[g.title for g in recent_goals]}\n"
            
            prompt = f"""Parse this voice command into a structured action:
Command: "{command}"

Context: {context}

Return a JSON object with:
- action: one of [create_goal, create_task, log_mood, show_schedule, show_goals, suggest_task, reschedule_help, chat_response]
- parameters: dict with relevant parameters
- confidence: float 0-1

Examples:
"Set a goal to exercise daily" -> {{"action": "create_goal", "parameters": {{"title": "Exercise Daily", "category": "health"}}, "confidence": 0.9}}
"I'm feeling 7 today" -> {{"action": "log_mood", "parameters": {{"mood_level": 7}}, "confidence": 0.9}}
"What meetings do I have tomorrow" -> {{"action": "show_schedule", "parameters": {{"days": 1}}, "confidence": 0.8}}

If the command is conversational or unclear, use action "chat_response" and include the original command as a parameter.
"""
            
            response = await self.openai_service.generate_task_breakdown(prompt)
            
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                import json
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                result = json.loads(json_str)
                result['ai_parsed'] = True
                return result
                
        except Exception as e:
            print(f"AI parsing error: {e}")
        
        # Fallback to chat response
        return {
            'action': 'chat_response',
            'parameters': {'message': command},
            'confidence': 0.5,
            'ai_parsed': False
        }
    
    async def execute_command(self, parsed_command: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
        """Execute the parsed command and return results"""
        action = parsed_command.get('action')
        params = parsed_command.get('parameters', {})
        
        try:
            if action == 'log_mood':
                return await self._execute_log_mood(params, user_id, db)
            elif action == 'create_goal':
                return await self._execute_create_goal(params, user_id, db)
            elif action == 'create_task':
                return await self._execute_create_task(params, user_id, db)
            elif action == 'show_schedule':
                return await self._execute_show_schedule(params, user_id, db)
            elif action == 'show_goals':
                return await self._execute_show_goals(params, user_id, db)
            elif action == 'suggest_task':
                return await self._execute_suggest_task(params, user_id, db)
            elif action == 'reschedule_help':
                return await self._execute_reschedule_help(params, user_id, db)
            else:
                return {
                    'success': False,
                    'message': f"Unknown action: {action}",
                    'action': action
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error executing command: {str(e)}",
                'action': action
            }
    
    async def _execute_log_mood(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Log mood entry"""
        mood_level = params.get('mood_level', 5)
        
        mood_entry = MoodEntry(
            user_id=user_id,
            mood_level=mood_level,
            energy_level=mood_level,  # Use same value for now
            notes=f"Logged via voice command"
        )
        
        db.add(mood_entry)
        db.commit()
        
        return {
            'success': True,
            'message': f"✅ Mood logged: {mood_level}/10",
            'action': 'log_mood',
            'data': {'mood_level': mood_level}
        }
    
    async def _execute_create_goal(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Create a new goal"""
        title = params.get('title', 'New Goal')
        category = params.get('category', 'personal')
        
        try:
            goal_category = GoalCategory(category.lower())
        except ValueError:
            goal_category = GoalCategory.PERSONAL
        
        goal = Goal(
            user_id=user_id,
            title=title,
            description=f"Goal created via voice command",
            category=goal_category,
            status=GoalStatus.ACTIVE
        )
        
        db.add(goal)
        db.commit()
        
        return {
            'success': True,
            'message': f"🎯 Goal created: {title}",
            'action': 'create_goal',
            'data': {'goal_id': goal.id, 'title': title}
        }
    
    async def _execute_create_task(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Create a new task"""
        title = params.get('title', 'New Task')
        priority = params.get('priority', 'medium')
        
        try:
            task_priority = TaskPriority(priority.lower())
        except ValueError:
            task_priority = TaskPriority.MEDIUM
        
        task = Task(
            user_id=user_id,
            title=title,
            description=f"Task created via voice command",
            priority=task_priority,
            task_type=TaskType.ACTION
        )
        
        db.add(task)
        db.commit()
        
        return {
            'success': True,
            'message': f"✅ Task created: {title}",
            'action': 'create_task',
            'data': {'task_id': task.id, 'title': title}
        }
    
    async def _execute_show_schedule(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Show upcoming schedule"""
        days = params.get('days', 1)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_date,
            CalendarEvent.start_time <= end_date
        ).order_by(CalendarEvent.start_time).limit(10).all()
        
        if not events:
            return {
                'success': True,
                'message': f"📅 No events scheduled for the next {days} day(s)",
                'action': 'show_schedule',
                'data': {'events': []}
            }
        
        event_list = []
        for event in events:
            event_list.append({
                'title': event.title,
                'start_time': event.start_time.strftime('%H:%M'),
                'date': event.start_time.strftime('%Y-%m-%d')
            })
        
        return {
            'success': True,
            'message': f"📅 Found {len(events)} upcoming event(s)",
            'action': 'show_schedule',
            'data': {'events': event_list}
        }
    
    async def _execute_show_goals(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Show goal progress"""
        goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == GoalStatus.ACTIVE
        ).order_by(Goal.progress.desc()).limit(5).all()
        
        if not goals:
            return {
                'success': True,
                'message': "🎯 No active goals found. Create one to get started!",
                'action': 'show_goals',
                'data': {'goals': []}
            }
        
        goal_list = []
        for goal in goals:
            goal_list.append({
                'title': goal.title,
                'progress': goal.progress,
                'category': goal.category.value
            })
        
        avg_progress = sum(g.progress for g in goals) / len(goals)
        
        return {
            'success': True,
            'message': f"🎯 {len(goals)} active goals, {avg_progress:.1f}% average progress",
            'action': 'show_goals',
            'data': {'goals': goal_list}
        }
    
    async def _execute_suggest_task(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Suggest next task"""
        # Get available tasks
        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.PENDING
        ).limit(3).all()
        
        if not tasks:
            return {
                'success': True,
                'message': "✅ No pending tasks! You're all caught up.",
                'action': 'suggest_task',
                'data': {'tasks': []}
            }
        
        # Simple scoring - high priority first
        def task_score(task):
            priority_scores = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
            return priority_scores.get(task.priority.value, 2)
        
        best_task = max(tasks, key=task_score)
        
        return {
            'success': True,
            'message': f"💡 Suggested task: {best_task.title}",
            'action': 'suggest_task',
            'data': {
                'task': {
                    'id': best_task.id,
                    'title': best_task.title,
                    'priority': best_task.priority.value,
                    'description': best_task.description
                }
            }
        }
    
    async def _execute_reschedule_help(self, params: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Provide rescheduling assistance"""
        command = params.get('command', '')
        
        return {
            'success': True,
            'message': "📅 I can help you reschedule! Try: 'move my 2pm meeting to 3pm' or visit the Calendar tab for drag-and-drop rescheduling.",
            'action': 'reschedule_help',
            'data': {'original_command': command}
        }