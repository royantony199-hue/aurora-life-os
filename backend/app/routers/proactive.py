#!/usr/bin/env python3
"""
Proactive AI Messaging API Router
Handles proactive message analysis, triggering, and management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatMessage, MessageType
from ..services.proactive_ai_service import ProactiveAIService, ProactiveMessagingScheduler
from pydantic import BaseModel


router = APIRouter()
proactive_service = ProactiveAIService()
scheduler = ProactiveMessagingScheduler()


class ProactiveMessageResponse(BaseModel):
    id: int
    trigger_type: str
    priority: str
    message: str
    context: str
    timestamp: str
    is_read: bool = False


class ProactiveAnalysisResponse(BaseModel):
    messages: List[Dict[str, Any]]
    analysis_timestamp: str
    triggers_found: int


class ProactiveSettingsRequest(BaseModel):
    enabled: bool = True
    check_interval_minutes: int = 30
    quiet_hours_start: Optional[int] = 22  # 10 PM
    quiet_hours_end: Optional[int] = 7     # 7 AM
    mood_reminders: bool = True
    goal_reminders: bool = True
    energy_insights: bool = True
    calendar_insights: bool = True


@router.get("/analyze/{user_id}", response_model=ProactiveAnalysisResponse)
async def analyze_user_triggers(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyze current triggers for a user and return potential proactive messages
    This is for testing/admin purposes - real triggers happen in background
    """
    # Validate user_id
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user_id: must be positive integer")
    
    try:
        messages = await proactive_service.analyze_and_trigger_proactive_messages(user_id, db)
        
        return ProactiveAnalysisResponse(
            messages=messages,
            analysis_timestamp=datetime.now().isoformat(),
            triggers_found=len(messages)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/trigger/{user_id}")
async def trigger_proactive_check(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger a proactive message check for a user
    Creates actual chat messages if triggers are found
    """
    # Validate user_id
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user_id: must be positive integer")
    
    # Check if user exists
    from ..models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    try:
        # Run the check in background
        background_tasks.add_task(scheduler.check_user_triggers, user_id, db)
        
        return {"message": "Proactive check triggered", "user_id": user_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trigger failed: {str(e)}")


@router.get("/messages/{user_id}")
async def get_proactive_messages(
    user_id: int,
    limit: int = 10,
    include_read: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get proactive messages for a user with read status
    """
    # Validate user_id
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user_id: must be positive integer")
    
    try:
        from ..models.proactive_message_log import ProactiveMessageLog
        
        # Query messages with their read status
        query = db.query(ChatMessage, ProactiveMessageLog).outerjoin(
            ProactiveMessageLog,
            ProactiveMessageLog.message_id == ChatMessage.id
        ).filter(
            ChatMessage.user_id == user_id,
            ChatMessage.is_proactive == True
        )
        
        if not include_read:
            # Filter out read messages
            query = query.filter(
                (ProactiveMessageLog.is_read == False) | 
                (ProactiveMessageLog.is_read == None)
            )
        
        messages_data = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        result = []
        for msg, log in messages_data:
            # Determine priority from trigger context
            priority = "medium"
            if msg.trigger_context and "priority" in msg.trigger_context:
                priority = msg.trigger_context["priority"]
            elif msg.trigger_type in ["goal_deadline", "overdue_goal"]:
                priority = "high"
            
            result.append({
                "id": msg.id,
                "trigger_type": msg.trigger_type,
                "priority": priority,
                "message": msg.content,
                "context": msg.trigger_context.get("context", "") if msg.trigger_context else "",
                "timestamp": msg.created_at.isoformat(),
                "is_read": log.is_read if log else False,
                "read_at": log.read_at.isoformat() if log and log.read_at else None
            })
        
        return {"messages": result, "total": len(result)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/settings/{user_id}")
async def update_proactive_settings(
    user_id: int,
    settings: ProactiveSettingsRequest,
    db: Session = Depends(get_db)
):
    """
    Update proactive messaging settings for a user
    TODO: Store in user preferences table
    """
    try:
        # For now, just return the settings
        # In a real app, you'd store these in user preferences
        
        return {
            "message": "Settings updated successfully",
            "user_id": user_id,
            "settings": settings.dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/settings/{user_id}")
async def get_proactive_settings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get proactive messaging settings for a user
    TODO: Retrieve from user preferences table
    """
    try:
        # Return default settings for now
        default_settings = {
            "enabled": True,
            "check_interval_minutes": 30,
            "quiet_hours_start": 22,
            "quiet_hours_end": 7,
            "mood_reminders": True,
            "goal_reminders": True,
            "energy_insights": True,
            "calendar_insights": True
        }
        
        return {
            "user_id": user_id,
            "settings": default_settings
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.post("/start-monitoring")
async def start_proactive_monitoring(
    background_tasks: BackgroundTasks,
    check_interval_minutes: int = 30
):
    """
    Start the background proactive messaging monitoring
    This would typically be started on app startup
    """
    try:
        if not scheduler.is_running:
            background_tasks.add_task(scheduler.start_monitoring, check_interval_minutes)
            return {"message": "Proactive monitoring started", "interval_minutes": check_interval_minutes}
        else:
            return {"message": "Proactive monitoring already running"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/stop-monitoring")
async def stop_proactive_monitoring():
    """
    Stop the background proactive messaging monitoring
    """
    try:
        scheduler.stop_monitoring()
        return {"message": "Proactive monitoring stopped"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.get("/status")
async def get_monitoring_status():
    """
    Get current status of proactive monitoring
    """
    return {
        "is_running": scheduler.is_running,
        "service_name": "ProactiveMessagingScheduler",
        "description": "Background service that analyzes user patterns and triggers proactive AI messages"
    }


@router.post("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    user_id: int = 1,  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Mark a proactive message as read
    """
    try:
        success = proactive_service.mark_message_as_read(user_id, message_id, db)
        
        if success:
            return {"message": "Message marked as read", "message_id": message_id}
        else:
            raise HTTPException(status_code=404, detail="Message not found or already read")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark message as read: {str(e)}")


@router.get("/test-triggers/{user_id}")
async def test_trigger_scenarios(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Test different trigger scenarios for development/debugging
    """
    test_scenarios = {
        "mood_gap": "User hasn't logged mood in 24+ hours",
        "goal_deadline": "Goal deadline approaching with low progress",
        "energy_pattern": "Consistently low energy levels detected",
        "calendar_busy": "Very busy day ahead (5+ events)",
        "goal_completion": "User recently completed a goal",
        "morning_checkin": "Morning time, no mood logged today",
        "evening_reflection": "Evening time, no goal activity today"
    }
    
    # Run actual analysis
    try:
        messages = await proactive_service.analyze_and_trigger_proactive_messages(user_id, db)
        
        return {
            "user_id": user_id,
            "available_scenarios": test_scenarios,
            "current_triggers": [msg["trigger_type"] for msg in messages],
            "triggered_messages": len(messages),
            "analysis": messages
        }
    
    except Exception as e:
        return {
            "user_id": user_id,
            "available_scenarios": test_scenarios,
            "error": str(e),
            "current_triggers": [],
            "triggered_messages": 0
        }