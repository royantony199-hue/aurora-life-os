#!/usr/bin/env python3
"""
Goal Coaching API Routes
Intelligent conversational goal planning and achievement guidance
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ..core.database import get_db
from ..services.goal_coaching_service import GoalCoachingService
from ..services.intelligent_coaching_service import IntelligentCoachingService
from ..models.chat import ChatMessage, MessageRole, MessageType

router = APIRouter()

class CoachingRequest(BaseModel):
    message: str
    user_id: int = 1
    conversation_id: Optional[str] = None
    include_history: bool = True

class CoachingResponse(BaseModel):
    response: str
    coaching_type: str
    suggestions: List[str]
    suggested_tasks: Optional[List[Dict[str, Any]]] = None
    suggested_goal: Optional[Dict[str, Any]] = None
    conversation_id: str
    next_steps: Optional[List[str]] = None

class TaskCreationRequest(BaseModel):
    tasks: List[Dict[str, Any]]
    user_id: int = 1
    goal_id: Optional[int] = None

@router.post("/coach", response_model=CoachingResponse)
async def coach_conversation(
    request: CoachingRequest,
    db: Session = Depends(get_db)
):
    """
    Main goal coaching conversation endpoint
    Provides intelligent guidance from goal definition to actionable steps
    """
    try:
        # Use the new intelligent coaching service
        intelligent_coaching_service = IntelligentCoachingService()
        
        # Get conversation history if requested
        conversation_history = []
        if request.include_history:
            recent_messages = db.query(ChatMessage).filter(
                ChatMessage.user_id == request.user_id
            ).order_by(ChatMessage.created_at.desc()).limit(15).all()  # Get more history for better context
            
            conversation_history = [
                {
                    'role': msg.role.value,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat()
                }
                for msg in reversed(recent_messages)
            ]
        
        # Get intelligent coaching response
        coaching_result = await intelligent_coaching_service.coach_conversation(
            message=request.message,
            user_id=request.user_id,
            db=db,
            conversation_history=conversation_history
        )
        
        # Save the conversation to chat history
        user_message = ChatMessage(
            user_id=request.user_id,
            role=MessageRole.USER,
            content=request.message,
            message_type=MessageType.COACHING
        )
        db.add(user_message)
        
        ai_message = ChatMessage(
            user_id=request.user_id,
            role=MessageRole.ASSISTANT,
            content=coaching_result['response'],
            message_type=MessageType.COACHING
        )
        db.add(ai_message)
        db.commit()
        
        # Generate next steps based on coaching type
        next_steps = _generate_next_steps(coaching_result)
        
        return CoachingResponse(
            response=coaching_result['response'],
            coaching_type=coaching_result.get('coaching_type', 'general'),
            suggestions=coaching_result.get('suggestions', []),
            suggested_tasks=coaching_result.get('suggested_tasks'),
            suggested_goal=coaching_result.get('suggested_goal'),
            conversation_id=f"coaching_{request.user_id}_{int(user_message.created_at.timestamp())}",
            next_steps=next_steps
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Coaching conversation failed: {str(e)}"
        )

@router.post("/coach/create-tasks")
async def create_tasks_from_coaching(
    request: TaskCreationRequest,
    db: Session = Depends(get_db)
):
    """
    Create tasks from coaching conversation suggestions
    """
    try:
        from ..models.task import Task, TaskStatus, TaskPriority, TaskType
        from ..models.goal import Goal
        
        created_tasks = []
        
        for task_data in request.tasks:
            # Map priority string to enum
            priority_map = {
                'high': TaskPriority.HIGH,
                'medium': TaskPriority.MEDIUM,
                'low': TaskPriority.LOW,
                'urgent': TaskPriority.URGENT
            }
            
            # Map category to task type
            type_map = {
                'research': TaskType.RESEARCH,
                'planning': TaskType.DECISION,
                'outreach': TaskType.ACTION,
                'analysis': TaskType.RESEARCH,
                'networking': TaskType.ACTION
            }
            
            priority = priority_map.get(task_data.get('priority', 'medium'), TaskPriority.MEDIUM)
            task_type = type_map.get(task_data.get('category', 'action'), TaskType.ACTION)
            
            task = Task(
                user_id=request.user_id,
                title=task_data['title'],
                description=task_data.get('description', ''),
                priority=priority,
                task_type=task_type,
                estimated_duration=task_data.get('estimated_minutes', 30),
                goal_id=request.goal_id,
                ai_generated=True
            )
            
            db.add(task)
            created_tasks.append(task)
        
        db.commit()
        
        return {
            'message': f'Successfully created {len(created_tasks)} tasks',
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'priority': task.priority.value,
                    'estimated_duration': task.estimated_duration
                }
                for task in created_tasks
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tasks: {str(e)}"
        )

@router.get("/coach/conversation-types")
async def get_conversation_types():
    """Get available coaching conversation types and their descriptions"""
    return {
        'types': [
            {
                'type': 'goal_definition',
                'title': 'Goal Definition',
                'description': 'Help clarify and define specific, measurable goals',
                'examples': ['I want to make $10k/month', 'My goal is to get fit']
            },
            {
                'type': 'strategy_discussion',
                'title': 'Strategy Discussion',
                'description': 'Explore different approaches to achieve your goals',
                'examples': ['I want to sell AI services', 'How should I build my audience?']
            },
            {
                'type': 'action_planning',
                'title': 'Action Planning',
                'description': 'Convert strategies into specific, actionable tasks',
                'examples': ['What should I do first?', 'Give me my next steps']
            },
            {
                'type': 'research_request',
                'title': 'Research & Analysis',
                'description': 'Get market insights and competitive analysis',
                'examples': ['Research the AI consulting market', 'Who are my competitors?']
            },
            {
                'type': 'motivation_support',
                'title': 'Motivation Support',
                'description': 'Get encouragement and overcome obstacles',
                'examples': ['I\'m feeling stuck', 'This seems too hard']
            }
        ]
    }

@router.post("/coach/suggest-goal")
async def suggest_goal_creation(
    message: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Analyze a message and suggest goal creation if appropriate
    """
    try:
        coaching_service = GoalCoachingService()
        should_create = await coaching_service._should_create_goal_from_message(message, {})
        
        if should_create:
            goal_info = await coaching_service._extract_goal_from_message(message)
            return {
                'should_create_goal': True,
                'suggested_goal': goal_info,
                'message': 'I can help you create this as a trackable goal. Would you like me to set this up for you?'
            }
        else:
            return {
                'should_create_goal': False,
                'message': 'Let\'s continue our conversation about your goals.'
            }
            
    except Exception as e:
        return {
            'should_create_goal': False,
            'message': 'I\'m here to help with your goals. Tell me more about what you\'d like to achieve.'
        }

def _generate_next_steps(coaching_result: Dict[str, Any]) -> List[str]:
    """Generate contextual next steps based on coaching type"""
    
    coaching_type = coaching_result.get('coaching_type', 'general')
    
    steps_map = {
        'goal_definition': [
            'Set a specific target date',
            'Define success metrics',
            'Identify required resources'
        ],
        'strategy_discussion': [
            'Research competitors and market',
            'Validate your approach',
            'Create an action plan'
        ],
        'action_planning': [
            'Start with the highest priority task',
            'Set daily/weekly milestones',
            'Track progress regularly'
        ],
        'research': [
            'Gather market data',
            'Analyze competition',
            'Identify opportunities'
        ],
        'motivation': [
            'Focus on one small step',
            'Celebrate recent progress',
            'Connect with your why'
        ]
    }
    
    return steps_map.get(coaching_type, [
        'Define your next action',
        'Set a deadline',
        'Track your progress'
    ])