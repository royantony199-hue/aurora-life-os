from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.models import Goal, GoalStatus, GoalCategory, User
from app.services.openai_service import OpenAIService
from app.routers.auth import get_current_user

router = APIRouter()


class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: GoalCategory
    target_date: Optional[datetime] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[GoalCategory] = None
    status: Optional[GoalStatus] = None
    progress: Optional[float] = None
    target_date: Optional[datetime] = None


class GoalResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: GoalCategory
    status: GoalStatus
    progress: float
    target_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    days_until_target: Optional[int] = None
    ai_insights: Optional[dict] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[GoalResponse])
async def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all goals for the current user"""
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    
    # Add calculated fields
    for goal in goals:
        if goal.target_date:
            days_until = (goal.target_date.date() - date.today()).days
            goal.days_until_target = days_until
    
    return goals


@router.get("/user/{user_id}", response_model=List[GoalResponse])
async def get_goals_by_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all goals for a specific user - preserves existing functionality"""
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    
    # Add calculated fields (same as existing endpoint)
    for goal in goals:
        if goal.target_date:
            days_until = (goal.target_date.date() - date.today()).days
            goal.days_until_target = days_until
    
    return goals


@router.post("/", response_model=GoalResponse)
async def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new goal"""
    goal = Goal(
        user_id=current_user.id,
        title=goal_data.title,
        description=goal_data.description,
        category=goal_data.category,
        target_date=goal_data.target_date
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    # Add calculated fields
    if goal.target_date:
        goal.days_until_target = (goal.target_date.date() - date.today()).days
    
    return goal


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific goal"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Add calculated fields
    if goal.target_date:
        goal.days_until_target = (goal.target_date.date() - date.today()).days
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a goal"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Update fields
    for field, value in goal_update.dict(exclude_unset=True).items():
        setattr(goal, field, value)
    
    db.commit()
    db.refresh(goal)
    
    # Add calculated fields
    if goal.target_date:
        goal.days_until_target = (goal.target_date.date() - date.today()).days
    
    return goal


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a goal"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(goal)
    db.commit()
    
    return {"message": "Goal deleted successfully"}


@router.post("/{goal_id}/progress")
async def update_progress(
    goal_id: int,
    progress: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update goal progress (0-100)"""
    if not 0 <= progress <= 100:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
    
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal.progress = progress
    
    # Auto-complete goal if progress reaches 100%
    if progress >= 100 and goal.status == GoalStatus.ACTIVE:
        goal.status = GoalStatus.COMPLETED
    
    db.commit()
    db.refresh(goal)
    
    return {"message": "Progress updated", "progress": progress, "status": goal.status}


@router.get("/{goal_id}/insights")
async def get_goal_insights(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered insights and recommendations for a specific goal"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    try:
        openai_service = OpenAIService()
        insights = await openai_service.break_down_goal(goal)
        return {
            "goal": goal.title,
            "insights": insights,
            "generated_at": datetime.now()
        }
    except Exception as e:
        return {
            "goal": goal.title,
            "insights": [
                {"task": "Define specific milestones", "estimated_time": "30 min", "priority": "high"},
                {"task": "Create action plan", "estimated_time": "1 hour", "priority": "high"},
                {"task": "Set weekly checkpoints", "estimated_time": "20 min", "priority": "medium"}
            ],
            "error": "AI insights temporarily unavailable"
        }


@router.get("/analytics/overview")
async def get_goals_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall goals analytics and progress overview"""
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    
    if not goals:
        return {
            "total_goals": 0,
            "active_goals": 0,
            "completed_goals": 0,
            "average_progress": 0,
            "categories": {},
            "upcoming_deadlines": []
        }
    
    # Calculate analytics
    active_goals = [g for g in goals if g.status == GoalStatus.ACTIVE]
    completed_goals = [g for g in goals if g.status == GoalStatus.COMPLETED]
    
    # Category breakdown
    categories = {}
    for goal in goals:
        cat = goal.category.value
        if cat not in categories:
            categories[cat] = {"total": 0, "completed": 0, "avg_progress": 0}
        categories[cat]["total"] += 1
        if goal.status == GoalStatus.COMPLETED:
            categories[cat]["completed"] += 1
    
    # Calculate average progress for active goals
    avg_progress = sum(g.progress for g in active_goals) / len(active_goals) if active_goals else 0
    
    # Upcoming deadlines (next 30 days)
    upcoming = []
    for goal in active_goals:
        if goal.target_date:
            days_until = (goal.target_date.date() - date.today()).days
            if 0 <= days_until <= 30:
                upcoming.append({
                    "id": goal.id,
                    "title": goal.title,
                    "target_date": goal.target_date,
                    "days_remaining": days_until,
                    "progress": goal.progress
                })
    
    # Sort by days remaining
    upcoming.sort(key=lambda x: x["days_remaining"])
    
    return {
        "total_goals": len(goals),
        "active_goals": len(active_goals),
        "completed_goals": len(completed_goals),
        "average_progress": round(avg_progress, 1),
        "categories": categories,
        "upcoming_deadlines": upcoming[:5]  # Top 5 most urgent
    }