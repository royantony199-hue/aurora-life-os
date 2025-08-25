#!/usr/bin/env python3
"""
Task Management API Router
Handles CRUD operations for tasks and AI-powered goal breakdown
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..models.goal import Goal, GoalStatus
from ..models.user import User
from ..services.task_management_service import TaskManagementService
from .auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter()
task_service = TaskManagementService()


# Pydantic models for request/response
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal_id: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.ACTION
    estimated_duration: Optional[int] = None
    energy_level_required: Optional[int] = Field(None, ge=1, le=10)
    preferred_time_of_day: Optional[str] = None
    parent_task_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    completion_notes: Optional[str] = None
    actual_duration: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    task_type: str
    due_date: Optional[datetime]
    progress_percentage: float
    estimated_duration: Optional[int]
    energy_level_required: Optional[int]
    preferred_time_of_day: Optional[str]
    goal_id: Optional[int]
    goal_title: Optional[str]
    is_overdue: bool
    days_until_due: int
    time_estimate_display: str
    ai_generated: bool
    created_at: datetime
    updated_at: Optional[datetime]


class GoalBreakdownRequest(BaseModel):
    goal_id: int
    max_tasks: int = Field(default=8, ge=1, le=15)
    auto_schedule: bool = True
    consider_user_context: bool = True


class NextTaskSuggestion(BaseModel):
    task_id: int
    title: str
    description: str
    estimated_duration: str
    priority: str
    reason: str
    ai_tips: List[str]
    goal_title: Optional[str]


@router.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    status: Optional[TaskStatus] = None,
    goal_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's tasks with filtering options"""
    query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if status:
        query = query.filter(Task.status == status)
    if goal_id:
        query = query.filter(Task.goal_id == goal_id)
    
    tasks = query.order_by(Task.order_index, Task.created_at.desc()).limit(limit).all()
    
    # Convert to response format
    task_responses = []
    for task in tasks:
        goal_title = task.goal.title if task.goal else None
        task_response = TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            task_type=task.task_type.value,
            due_date=task.due_date,
            progress_percentage=task.progress_percentage,
            estimated_duration=task.estimated_duration,
            energy_level_required=task.energy_level_required,
            preferred_time_of_day=task.preferred_time_of_day,
            goal_id=task.goal_id,
            goal_title=goal_title,
            is_overdue=task.is_overdue,
            days_until_due=task.days_until_due,
            time_estimate_display=task.get_time_estimate_display(),
            ai_generated=task.ai_generated,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        task_responses.append(task_response)
    
    return task_responses


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new task"""
    # Validate goal exists if provided
    if task_data.goal_id:
        goal = db.query(Goal).filter(
            Goal.id == task_data.goal_id,
            Goal.user_id == current_user.id
        ).first()
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
    
    # Validate parent task if provided
    if task_data.parent_task_id:
        parent_task = db.query(Task).filter(
            Task.id == task_data.parent_task_id,
            Task.user_id == current_user.id
        ).first()
        if not parent_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent task not found"
            )
    
    # Create task
    task = Task(
        user_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        goal_id=task_data.goal_id,
        due_date=task_data.due_date,
        priority=task_data.priority,
        task_type=task_data.task_type,
        estimated_duration=task_data.estimated_duration,
        energy_level_required=task_data.energy_level_required,
        preferred_time_of_day=task_data.preferred_time_of_day,
        parent_task_id=task_data.parent_task_id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Return response
    goal_title = task.goal.title if task.goal else None
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        task_type=task.task_type.value,
        due_date=task.due_date,
        progress_percentage=task.progress_percentage,
        estimated_duration=task.estimated_duration,
        energy_level_required=task.energy_level_required,
        preferred_time_of_day=task.preferred_time_of_day,
        goal_id=task.goal_id,
        goal_title=goal_title,
        is_overdue=task.is_overdue,
        days_until_due=task.days_until_due,
        time_estimate_display=task.get_time_estimate_display(),
        ai_generated=task.ai_generated,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific task by ID"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    goal_title = task.goal.title if task.goal else None
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        task_type=task.task_type.value,
        due_date=task.due_date,
        progress_percentage=task.progress_percentage,
        estimated_duration=task.estimated_duration,
        energy_level_required=task.energy_level_required,
        preferred_time_of_day=task.preferred_time_of_day,
        goal_id=task.goal_id,
        goal_title=goal_title,
        is_overdue=task.is_overdue,
        days_until_due=task.days_until_due,
        time_estimate_display=task.get_time_estimate_display(),
        ai_generated=task.ai_generated,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Handle status changes
    if task_data.status:
        if task_data.status == TaskStatus.IN_PROGRESS and task.status == TaskStatus.PENDING:
            task.start_task()
        elif task_data.status == TaskStatus.COMPLETED:
            task.complete_task(
                completion_notes=task_data.completion_notes,
                actual_duration=task_data.actual_duration
            )
    
    db.commit()
    db.refresh(task)
    
    # Update goal progress in background if task is completed
    if task.status == TaskStatus.COMPLETED and task.goal_id:
        background_tasks.add_task(
            task_service.update_goal_progress_from_tasks,
            task.goal_id,
            db
        )
    
    goal_title = task.goal.title if task.goal else None
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        task_type=task.task_type.value,
        due_date=task.due_date,
        progress_percentage=task.progress_percentage,
        estimated_duration=task.estimated_duration,
        energy_level_required=task.energy_level_required,
        preferred_time_of_day=task.preferred_time_of_day,
        goal_id=task.goal_id,
        goal_title=goal_title,
        is_overdue=task.is_overdue,
        days_until_due=task.days_until_due,
        time_estimate_display=task.get_time_estimate_display(),
        ai_generated=task.ai_generated,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.post("/goals/{goal_id}/breakdown")
async def break_down_goal(
    goal_id: int,
    breakdown_request: GoalBreakdownRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Break down a goal into actionable tasks using AI"""
    # Validate goal
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    try:
        # Use AI to break down goal
        created_tasks = await task_service.create_tasks_from_breakdown(
            goal=goal,
            user_id=current_user.id,
            db=db,
            auto_schedule=breakdown_request.auto_schedule
        )
        
        # Convert to response format
        task_responses = []
        for task in created_tasks:
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status.value,
                priority=task.priority.value,
                task_type=task.task_type.value,
                due_date=task.due_date,
                progress_percentage=task.progress_percentage,
                estimated_duration=task.estimated_duration,
                energy_level_required=task.energy_level_required,
                preferred_time_of_day=task.preferred_time_of_day,
                goal_id=task.goal_id,
                goal_title=goal.title,
                is_overdue=task.is_overdue,
                days_until_due=task.days_until_due,
                time_estimate_display=task.get_time_estimate_display(),
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            task_responses.append(task_response)
        
        return {
            "message": f"Successfully created {len(created_tasks)} tasks from goal breakdown",
            "goal_title": goal.title,
            "tasks": task_responses
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to break down goal: {str(e)}"
        )


@router.get("/tasks/suggestions/next")
async def get_next_task_suggestion(
    consider_mood: bool = True,
    consider_energy: bool = True,
    consider_time: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered next task suggestion"""
    try:
        suggestion = await task_service.suggest_next_task(
            user_id=current_user.id,
            db=db,
            consider_mood=consider_mood,
            consider_energy=consider_energy,
            consider_time=consider_time
        )
        
        if not suggestion:
            return {
                "message": "No tasks available for suggestion",
                "suggestion": None
            }
        
        return {
            "message": "Here's your next recommended task",
            "suggestion": NextTaskSuggestion(**suggestion)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task suggestion: {str(e)}"
        )


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start working on a task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is already {task.status.value}"
        )
    
    task.start_task()
    db.commit()
    
    return {
        "message": "Task started successfully",
        "task_id": task.id,
        "status": task.status.value,
        "started_at": task.started_at
    }


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    completion_notes: Optional[str] = None,
    actual_duration: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a task as completed"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already completed"
        )
    
    task.complete_task(completion_notes, actual_duration)
    db.commit()
    
    # Update goal progress in background
    if task.goal_id:
        background_tasks.add_task(
            task_service.update_goal_progress_from_tasks,
            task.goal_id,
            db
        )
    
    return {
        "message": "Task completed successfully!",
        "task_id": task.id,
        "status": task.status.value,
        "completed_at": task.completed_at,
        "milestone_reached": task.goal_id is not None
    }