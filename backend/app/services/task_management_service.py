#!/usr/bin/env python3
"""
Task Management Service
AI-powered goal breakdown into actionable tasks matching PRD requirements
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..models.user import User
from ..models.goal import Goal, GoalStatus
from ..models.task import Task, TaskStatus, TaskPriority, TaskType, TaskDependency
from ..models.mood import MoodEntry
from .openai_service import OpenAIService


class TaskManagementService:
    """
    Service for AI-powered task breakdown and management
    Implements PRD requirements for goal-to-task conversion
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def break_down_goal_into_tasks(
        self, 
        goal: Goal, 
        user_id: int, 
        db: Session,
        max_tasks: int = 8,
        consider_user_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Break down a goal into actionable tasks using AI
        Core PRD requirement: "Task breakdown from goals to actionable items"
        """
        try:
            # Get user context for personalized breakdown
            user_context = {}
            if consider_user_context:
                user_context = await self._get_user_context_for_tasks(user_id, db)
            
            # Build AI prompt for goal breakdown
            prompt = self._build_goal_breakdown_prompt(goal, user_context, max_tasks)
            
            # Get AI response using dedicated task breakdown method
            response = await self.openai_service.generate_task_breakdown(prompt)
            
            # Parse AI response into structured tasks
            tasks_data = self._parse_ai_task_response(response, goal)
            
            return tasks_data
            
        except Exception as e:
            print(f"Error in goal breakdown: {e}")
            # Fallback to basic breakdown if AI fails
            return self._create_fallback_tasks(goal)
    
    async def create_tasks_from_breakdown(
        self, 
        goal: Goal, 
        user_id: int, 
        db: Session,
        auto_schedule: bool = True
    ) -> List[Task]:
        """
        Create actual Task records from AI breakdown
        """
        tasks_data = await self.break_down_goal_into_tasks(goal, user_id, db)
        created_tasks = []
        
        for i, task_data in enumerate(tasks_data):
            task = Task(
                user_id=user_id,
                goal_id=goal.id,
                title=task_data["title"],
                description=task_data["description"],
                task_type=TaskType(task_data.get("type", "action")),
                priority=TaskPriority(task_data.get("priority", "medium")),
                estimated_duration=task_data.get("estimated_minutes", 60),
                energy_level_required=task_data.get("energy_required", 5),
                preferred_time_of_day=task_data.get("preferred_time", "morning"),
                order_index=i,
                ai_generated=True,
                ai_suggestions=json.dumps(task_data.get("ai_tips", [])),
                mood_when_created=task_data.get("mood_context", 5)
            )
            
            # Smart scheduling if enabled
            if auto_schedule and task_data.get("suggested_due_date"):
                task.due_date = datetime.fromisoformat(task_data["suggested_due_date"])
            
            db.add(task)
            created_tasks.append(task)
        
        db.commit()
        return created_tasks
    
    async def suggest_next_task(
        self, 
        user_id: int, 
        db: Session,
        consider_mood: bool = True,
        consider_energy: bool = True,
        consider_time: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        AI-powered next task suggestion based on context
        PRD requirement: "Smart scheduling based on goals and energy levels"
        """
        try:
            # Get user's current context
            user_context = await self._get_user_context_for_tasks(user_id, db)
            current_time = datetime.now()
            
            # Get available tasks
            available_tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user_id,
                    Task.status == TaskStatus.PENDING,
                    (Task.due_date == None) | (Task.due_date > current_time)
                )
            ).all()
            
            if not available_tasks:
                return None
            
            # Score tasks based on current context
            scored_tasks = []
            for task in available_tasks:
                score = self._calculate_task_score(task, user_context, current_time)
                scored_tasks.append((task, score))
            
            # Sort by score and return top suggestion
            scored_tasks.sort(key=lambda x: x[1], reverse=True)
            best_task = scored_tasks[0][0]
            
            # Generate AI explanation for why this task is suggested
            explanation = await self._generate_task_suggestion_explanation(
                best_task, user_context, db
            )
            
            return {
                "task_id": best_task.id,
                "title": best_task.title,
                "description": best_task.description,
                "estimated_duration": best_task.get_time_estimate_display(),
                "priority": best_task.priority.value,
                "reason": explanation,
                "ai_tips": json.loads(best_task.ai_suggestions or "[]"),
                "goal_title": best_task.goal.title if best_task.goal else None
            }
            
        except Exception as e:
            print(f"Error suggesting next task: {e}")
            return None
    
    async def update_goal_progress_from_tasks(self, goal_id: int, db: Session):
        """
        Update goal progress based on completed tasks
        PRD requirement: "Progress tracking and milestone celebration"
        """
        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return
        
        tasks = db.query(Task).filter(Task.goal_id == goal_id).all()
        if not tasks:
            return
        
        # Calculate progress based on task completion
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        total_weight = sum(self._get_task_weight(t) for t in tasks)
        completed_weight = sum(self._get_task_weight(t) for t in completed_tasks)
        
        if total_weight > 0:
            new_progress = (completed_weight / total_weight) * 100
            goal.progress = round(new_progress, 1)
            db.commit()
            
            # Check for milestone celebration
            if new_progress >= 100 and goal.status != GoalStatus.COMPLETED:
                goal.status = GoalStatus.COMPLETED
                db.commit()
                return {"milestone": "goal_completed", "progress": new_progress}
            elif new_progress >= 75 and goal.progress < 75:
                return {"milestone": "75_percent", "progress": new_progress}
            elif new_progress >= 50 and goal.progress < 50:
                return {"milestone": "halfway", "progress": new_progress}
            elif new_progress >= 25 and goal.progress < 25:
                return {"milestone": "25_percent", "progress": new_progress}
    
    def _build_goal_breakdown_prompt(self, goal: Goal, user_context: Dict, max_tasks: int) -> str:
        """Build AI prompt for goal breakdown"""
        prompt = f"""You are an expert productivity coach helping break down a goal into actionable tasks.

GOAL TO BREAK DOWN:
Title: {goal.title}
Description: {goal.description or "No description provided"}
Category: {goal.category.value}
Target Date: {goal.target_date.strftime("%Y-%m-%d") if goal.target_date else "No deadline"}
Current Progress: {goal.progress}%

USER CONTEXT:
- Recent mood level: {user_context.get('recent_mood', 'Unknown')}/10
- Recent energy level: {user_context.get('recent_energy', 'Unknown')}/10
- Preferred work style: {user_context.get('coaching_style', 'balanced')}
- Industry: {user_context.get('industry', 'general')}

INSTRUCTIONS:
1. Break this goal into {max_tasks} specific, actionable tasks
2. Order tasks logically (what should be done first, second, etc.)
3. Consider the user's energy level and mood for task sequencing
4. Make tasks SMART (Specific, Measurable, Achievable, Relevant, Time-bound)

For each task, provide:
- Title (clear, action-oriented)
- Description (specific steps to take)
- Type (action/milestone/research/decision/review/habit)
- Priority (low/medium/high/urgent)
- Estimated time in minutes
- Energy level required (1-10 scale)
- Preferred time of day (morning/afternoon/evening)
- 2-3 AI tips for success

Format your response as a JSON array of task objects like this:
[
  {{
    "title": "Research target audience",
    "description": "Spend 30 minutes researching who your ideal customers are",
    "type": "research",
    "priority": "high", 
    "estimated_minutes": 30,
    "energy_required": 6,
    "preferred_time": "morning",
    "ai_tips": ["Use Google Analytics", "Create user personas", "Focus on demographics first"]
  }}
]

Make sure tasks are practical and achievable given the user's context."""

        return prompt
    
    def _parse_ai_task_response(self, response: str, goal: Goal) -> List[Dict[str, Any]]:
        """Parse AI response into structured task data"""
        try:
            # Remove markdown code blocks if present
            cleaned_response = response.replace("```json", "").replace("```", "")
            
            # Try to extract JSON from response
            if "[" in cleaned_response and "]" in cleaned_response:
                start = cleaned_response.find("[")
                end = cleaned_response.rfind("]") + 1
                json_str = cleaned_response[start:end]
                tasks = json.loads(json_str)
                
                # Validate and clean task data
                cleaned_tasks = []
                for task in tasks:
                    if "title" in task:
                        cleaned_task = {
                            "title": task.get("title", "Untitled Task"),
                            "description": task.get("description", ""),
                            "type": task.get("type", "action"),
                            "priority": task.get("priority", "medium"),
                            "estimated_minutes": int(task.get("estimated_minutes", 60)),
                            "energy_required": min(10, max(1, int(task.get("energy_required", 5)))),
                            "preferred_time": task.get("preferred_time", "morning"),
                            "ai_tips": task.get("ai_tips", [])
                        }
                        cleaned_tasks.append(cleaned_task)
                
                return cleaned_tasks[:8]  # Max 8 tasks
                
        except Exception as e:
            print(f"Error parsing AI task response: {e}")
        
        # Fallback if parsing fails
        return self._create_fallback_tasks(goal)
    
    def _create_fallback_tasks(self, goal: Goal) -> List[Dict[str, Any]]:
        """Create basic task breakdown if AI fails"""
        return [
            {
                "title": f"Plan approach for {goal.title}",
                "description": "Break down the goal and create a detailed plan",
                "type": "research",
                "priority": "high",
                "estimated_minutes": 30,
                "energy_required": 7,
                "preferred_time": "morning",
                "ai_tips": ["Start with the end in mind", "Identify key milestones", "Consider potential obstacles"]
            },
            {
                "title": f"Take first action on {goal.title}",
                "description": "Begin working on the most important aspect",
                "type": "action",
                "priority": "high",
                "estimated_minutes": 60,
                "energy_required": 6,
                "preferred_time": "morning",
                "ai_tips": ["Start small", "Focus on progress not perfection", "Track your progress"]
            },
            {
                "title": f"Review progress on {goal.title}",
                "description": "Assess what's working and what needs adjustment",
                "type": "review",
                "priority": "medium",
                "estimated_minutes": 20,
                "energy_required": 4,
                "preferred_time": "evening",
                "ai_tips": ["Be honest about challenges", "Celebrate small wins", "Adjust approach as needed"]
            }
        ]
    
    async def _get_user_context_for_tasks(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user context for task planning"""
        user = db.query(User).filter(User.id == user_id).first()
        recent_mood = db.query(MoodEntry).filter(MoodEntry.user_id == user_id).order_by(desc(MoodEntry.created_at)).first()
        
        return {
            "recent_mood": recent_mood.mood_level if recent_mood else 5,
            "recent_energy": recent_mood.energy_level if recent_mood else 5,
            "coaching_style": user.coaching_style if user else "balanced",
            "industry": user.industry if user else "general",
            "work_hours_start": user.work_hours_start if user else "09:00",
            "work_hours_end": user.work_hours_end if user else "18:00"
        }
    
    def _calculate_task_score(self, task: Task, user_context: Dict, current_time: datetime) -> float:
        """Calculate task recommendation score based on context"""
        score = 0.0
        
        # Base priority score
        priority_scores = {"low": 1, "medium": 2, "high": 3, "urgent": 4}
        score += priority_scores.get(task.priority.value, 2) * 10
        
        # Energy level matching
        user_energy = user_context.get("recent_energy", 5)
        task_energy = task.energy_level_required or 5
        energy_match = 10 - abs(user_energy - task_energy)
        score += energy_match * 5
        
        # Time of day preference
        current_hour = current_time.hour
        if task.preferred_time_of_day:
            if task.preferred_time_of_day == "morning" and 6 <= current_hour <= 11:
                score += 15
            elif task.preferred_time_of_day == "afternoon" and 12 <= current_hour <= 17:
                score += 15
            elif task.preferred_time_of_day == "evening" and 18 <= current_hour <= 22:
                score += 15
        
        # Due date urgency
        if task.due_date:
            days_until_due = task.days_until_due
            if days_until_due <= 1:
                score += 20
            elif days_until_due <= 3:
                score += 10
            elif days_until_due <= 7:
                score += 5
        
        # Goal priority (if task belongs to active goal)
        if task.goal and task.goal.status == GoalStatus.ACTIVE:
            score += 10
        
        return score
    
    def _get_task_weight(self, task: Task) -> float:
        """Get task weight for progress calculation"""
        # Milestones are worth more than regular tasks
        if task.task_type == TaskType.MILESTONE:
            return 3.0
        elif task.task_type == TaskType.DECISION:
            return 2.0
        elif task.task_type == TaskType.REVIEW:
            return 1.5
        else:
            return 1.0
    
    async def _generate_task_suggestion_explanation(
        self, 
        task: Task, 
        user_context: Dict, 
        db: Session
    ) -> str:
        """Generate AI explanation for why this task is suggested"""
        try:
            prompt = f"""Explain in 1-2 friendly sentences why this task is a good choice right now:

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}
Energy required: {task.energy_level_required}/10
User's current energy: {user_context.get('recent_energy', 5)}/10
User's current mood: {user_context.get('recent_mood', 5)}/10
Time of day: {datetime.now().strftime('%H:%M')}

Be encouraging and specific about why this timing makes sense."""

            response = await self.openai_service.get_emotional_response(
                user_message=prompt,
                user_mood=user_context.get("recent_mood", 5),
                user_energy=user_context.get("recent_energy", 5),
                user_context={}
            )
            
            # Clean response to just the explanation
            return response.strip()
            
        except Exception as e:
            return f"This {task.priority.value}-priority task is well-suited for your current energy level and will move you closer to your goal."