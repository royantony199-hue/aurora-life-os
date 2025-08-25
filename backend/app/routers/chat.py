from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import time
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models import ChatMessage, MessageRole, MessageType, User, MoodEntry, Goal, GoalStatus
from app.services.openai_service import OpenAIService
from app.routers.auth import get_current_user

router = APIRouter()
openai_service = None  # Initialize lazily

def get_openai_service():
    """Get or create OpenAI service instance"""
    global openai_service
    if openai_service is None:
        openai_service = OpenAIService()
    else:
        # Reload the client to get updated API key
        openai_service.reload_client()
    return openai_service


class MessageRequest(BaseModel):
    message: str
    message_type: MessageType = MessageType.CHAT
    context_data: Optional[dict] = None


class MessageResponse(BaseModel):
    message: str
    response: str
    message_type: MessageType
    response_time_ms: int
    suggestions: Optional[List[str]] = None
    action_items: Optional[List[dict]] = None


@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send message to Aurora AI and get emotionally intelligent response"""
    start_time = time.time()
    
    # Get user's recent mood for context
    recent_mood = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id
    ).order_by(MoodEntry.created_at.desc()).first()
    
    user_mood = recent_mood.mood_level if recent_mood else 7
    user_energy = recent_mood.energy_level if recent_mood else 7
    
    # Get conversation history
    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(20).all()
    
    conversation_history = []
    for msg in reversed(recent_messages):  # Reverse to get chronological order
        conversation_history.append({
            "role": msg.role.value,
            "content": msg.content
        })
    
    # Get user's active goals for context
    active_goals = db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.status == GoalStatus.ACTIVE
    ).all()
    
    goals_context = {
        "active_goals": [
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "category": goal.category.value,
                "progress": goal.progress,
                "target_date": goal.target_date.isoformat() if goal.target_date else None
            }
            for goal in active_goals
        ],
        "goals_count": len(active_goals)
    }
    
    # Merge goals context with any existing context
    combined_context = {**(request.context_data or {}), "goals": goals_context}
    
    # Get AI response
    try:
        ai_response = await get_openai_service().get_emotional_response(
            user_message=request.message,
            user_mood=user_mood,
            user_energy=user_energy,
            conversation_history=conversation_history,
            user_context=combined_context
        )
    except Exception as e:
        ai_response = "I'm having trouble connecting right now. How can I help you in the meantime?"
    
    response_time = int((time.time() - start_time) * 1000)
    
    # Save user message
    user_message = ChatMessage(
        user_id=current_user.id,
        role=MessageRole.USER,
        message_type=request.message_type,
        content=request.message,
        context_data=request.context_data,
        user_mood_at_time=user_mood,
        user_energy_at_time=user_energy
    )
    db.add(user_message)
    
    # Save AI response
    ai_message = ChatMessage(
        user_id=current_user.id,
        role=MessageRole.ASSISTANT,
        message_type=request.message_type,
        content=ai_response,
        context_data=request.context_data,
        response_time_ms=response_time,
        user_mood_at_time=user_mood,
        user_energy_at_time=user_energy
    )
    db.add(ai_message)
    db.commit()
    
    return MessageResponse(
        message=request.message,
        response=ai_response,
        message_type=request.message_type,
        response_time_ms=response_time,
        suggestions=get_quick_reply_suggestions(request.message_type, user_mood),
        action_items=None  # TODO: Extract action items from AI response
    )


@router.get("/history")
@router.get("/messages")  # Alias for frontend compatibility
async def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for the user"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    return {"messages": [
        {
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "message_type": msg.message_type.value,
            "created_at": msg.created_at,
            "user_mood": msg.user_mood_at_time,
            "user_energy": msg.user_energy_at_time
        }
        for msg in reversed(messages)
    ]}


@router.post("/quick-command")
async def process_quick_command(
    command: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process quick commands for dynamic planning"""
    # TODO: Implement command parsing and execution
    # Examples: "reschedule meeting", "add task", "check mood", etc.
    
    return {
        "command": command,
        "status": "processed",
        "actions_taken": [],
        "message": "Quick command processing coming soon!"
    }


def get_quick_reply_suggestions(message_type: MessageType, user_mood: int) -> List[str]:
    """Generate contextual quick reply suggestions"""
    
    base_suggestions = [
        "Tell me about my goals",
        "How am I doing today?",
        "What should I focus on?",
        "Help me plan my day"
    ]
    
    if message_type == MessageType.MOOD_CHECKIN:
        return [
            "I'm feeling better now",
            "Still struggling a bit",
            "What can I do to improve?",
            "Show me some recovery tips"
        ]
    
    if user_mood <= 4:
        return [
            "I need some motivation",
            "Help me feel better",
            "What's one small win I can have?",
            "Should I take a break?"
        ]
    elif user_mood >= 8:
        return [
            "I'm ready to tackle big tasks!",
            "What challenging goal can I work on?",
            "Let's plan something ambitious",
            "How can I maintain this energy?"
        ]
    
    return base_suggestions


