#!/usr/bin/env python3
"""
Autonomous Scheduling API Routes
Provides intelligent scheduling suggestions and automatic task organization
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..services.autonomous_scheduling_service import AutonomousSchedulingService
from ..models.task import Task, TaskStatus

router = APIRouter()

class ScheduleSuggestionRequest(BaseModel):
    """Request model for schedule suggestions"""
    user_id: int = 1
    days_ahead: int = 7
    include_insights: bool = True

class RescheduleRequest(BaseModel):
    """Request model for rescheduling a task"""
    task_id: int
    user_id: int = 1
    reason: Optional[str] = None

class AutoScheduleTaskRequest(BaseModel):
    """Request model for auto-scheduling a new task"""
    task_id: int
    user_id: int = 1

class ApproveScheduleRequest(BaseModel):
    """Request model for approving suggested schedule"""
    task_id: int
    scheduled_time: datetime
    user_id: int = 1

@router.post("/schedule/suggest")
async def suggest_optimal_schedule(
    request: ScheduleSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered scheduling suggestions for pending tasks
    
    This endpoint analyzes:
    - User's energy patterns from mood data
    - Calendar availability
    - Task priorities and types
    - Optimal time slots based on historical performance
    """
    try:
        scheduling_service = AutonomousSchedulingService()
        
        suggestions = await scheduling_service.suggest_optimal_schedule(
            user_id=request.user_id,
            db=db,
            days_ahead=request.days_ahead
        )
        
        return {
            'success': True,
            'scheduled_count': len(suggestions['scheduled_tasks']),
            'unscheduled_count': len(suggestions.get('unscheduled_tasks', [])),
            'scheduled_tasks': suggestions['scheduled_tasks'],
            'unscheduled_tasks': suggestions.get('unscheduled_tasks', []),
            'insights': suggestions.get('insights', []) if request.include_insights else [],
            'energy_patterns': suggestions.get('energy_patterns', {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate schedule suggestions: {str(e)}"
        )

@router.post("/schedule/reschedule")
async def reschedule_task_intelligently(
    request: RescheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Intelligently reschedule a task based on current context
    
    Considers:
    - Current energy levels
    - Calendar conflicts
    - Task priority
    - Optimal time slots
    """
    try:
        scheduling_service = AutonomousSchedulingService()
        
        result = await scheduling_service.reschedule_intelligently(
            task_id=request.task_id,
            user_id=request.user_id,
            db=db,
            reason=request.reason
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reschedule task: {str(e)}"
        )

@router.post("/schedule/auto-schedule-task")
async def auto_schedule_new_task(
    request: AutoScheduleTaskRequest,
    db: Session = Depends(get_db)
):
    """
    Automatically find the best time for a newly created task
    """
    try:
        # Get the task
        task = db.query(Task).filter(
            Task.id == request.task_id,
            Task.user_id == request.user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        scheduling_service = AutonomousSchedulingService()
        
        result = await scheduling_service.auto_schedule_new_task(
            task=task,
            user_id=request.user_id,
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to auto-schedule task: {str(e)}"
        )

@router.post("/schedule/approve")
async def approve_schedule_suggestion(
    request: ApproveScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Approve and apply a scheduling suggestion
    """
    try:
        # Update the task with the approved schedule
        task = db.query(Task).filter(
            Task.id == request.task_id,
            Task.user_id == request.user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update scheduled time
        task.scheduled_for = request.scheduled_time
        task.updated_at = datetime.now()
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Task "{task.title}" scheduled for {request.scheduled_time.strftime("%B %d at %I:%M %p")}',
            'task': {
                'id': task.id,
                'title': task.title,
                'scheduled_for': task.scheduled_for.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve schedule: {str(e)}"
        )

@router.get("/schedule/preview/{user_id}")
async def preview_weekly_schedule(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a preview of the optimized weekly schedule
    """
    try:
        scheduling_service = AutonomousSchedulingService()
        
        # Get suggestions for next 7 days
        suggestions = await scheduling_service.suggest_optimal_schedule(
            user_id=user_id,
            db=db,
            days_ahead=7
        )
        
        # Group by day for easier visualization
        schedule_by_day = {}
        
        for task in suggestions['scheduled_tasks']:
            date_key = task['scheduled_time'].date().isoformat()
            if date_key not in schedule_by_day:
                schedule_by_day[date_key] = {
                    'date': date_key,
                    'day_name': task['scheduled_time'].strftime('%A'),
                    'tasks': []
                }
            
            schedule_by_day[date_key]['tasks'].append({
                'time': task['scheduled_time'].strftime('%I:%M %p'),
                'title': task['task_title'],
                'duration': task['duration_minutes'],
                'priority': task['task_priority'],
                'confidence': task['confidence']
            })
        
        # Sort tasks within each day by time
        for day_data in schedule_by_day.values():
            day_data['tasks'].sort(key=lambda x: x['time'])
        
        return {
            'success': True,
            'weekly_schedule': list(schedule_by_day.values()),
            'total_tasks': len(suggestions['scheduled_tasks']),
            'energy_optimization': suggestions.get('energy_patterns', {}).get('patterns_available', False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate schedule preview: {str(e)}"
        )

@router.post("/schedule/batch-approve")
async def batch_approve_suggestions(
    task_schedules: List[Dict[str, Any]],
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Approve multiple scheduling suggestions at once
    
    Expected format:
    [
        {
            "task_id": 123,
            "scheduled_time": "2024-01-15T10:00:00"
        },
        ...
    ]
    """
    try:
        approved_count = 0
        errors = []
        
        for schedule in task_schedules:
            try:
                task = db.query(Task).filter(
                    Task.id == schedule['task_id'],
                    Task.user_id == user_id
                ).first()
                
                if task:
                    task.scheduled_for = datetime.fromisoformat(schedule['scheduled_time'])
                    task.updated_at = datetime.now()
                    approved_count += 1
                else:
                    errors.append(f"Task {schedule['task_id']} not found")
                    
            except Exception as e:
                errors.append(f"Failed to schedule task {schedule.get('task_id')}: {str(e)}")
        
        db.commit()
        
        return {
            'success': True,
            'approved_count': approved_count,
            'total_submitted': len(task_schedules),
            'errors': errors if errors else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to batch approve schedules: {str(e)}"
        )