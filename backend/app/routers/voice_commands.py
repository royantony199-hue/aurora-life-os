#!/usr/bin/env python3
"""
Voice Command API Routes
Handles natural language command parsing and execution
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from ..core.database import get_db
from ..services.voice_command_service import VoiceCommandService

router = APIRouter()

class VoiceCommandRequest(BaseModel):
    command: str
    user_id: int = 1  # Default to user 1 for MVP

class VoiceCommandResponse(BaseModel):
    success: bool
    message: str
    action: str
    data: Dict[str, Any] = {}
    confidence: float = 0.0
    ai_parsed: bool = False

@router.post("/parse", response_model=VoiceCommandResponse)
async def parse_voice_command(
    request: VoiceCommandRequest,
    db: Session = Depends(get_db)
):
    """Parse a voice command into structured actions"""
    try:
        service = VoiceCommandService()
        
        # Parse the command
        parsed = await service.parse_command(request.command, request.user_id, db)
        
        return VoiceCommandResponse(
            success=True,
            message=f"Command parsed: {parsed.get('action', 'unknown')}",
            action=parsed.get('action', 'unknown'),
            data=parsed.get('parameters', {}),
            confidence=parsed.get('confidence', 0.0),
            ai_parsed=parsed.get('ai_parsed', False)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing command: {str(e)}")

@router.post("/execute", response_model=VoiceCommandResponse)
async def execute_voice_command(
    request: VoiceCommandRequest,
    db: Session = Depends(get_db)
):
    """Parse and execute a voice command"""
    try:
        service = VoiceCommandService()
        
        # Parse the command
        parsed = await service.parse_command(request.command, request.user_id, db)
        
        # Execute the parsed command
        result = await service.execute_command(parsed, request.user_id, db)
        
        return VoiceCommandResponse(
            success=result.get('success', False),
            message=result.get('message', 'Command executed'),
            action=result.get('action', 'unknown'),
            data=result.get('data', {}),
            confidence=parsed.get('confidence', 0.0),
            ai_parsed=parsed.get('ai_parsed', False)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")

@router.get("/supported-actions")
async def get_supported_actions():
    """Get list of supported voice command actions"""
    return {
        "actions": [
            {
                "name": "log_mood",
                "description": "Log mood level from 1-10",
                "examples": ["feeling 7/10", "mood 8", "I'm feeling 5 today"]
            },
            {
                "name": "create_goal", 
                "description": "Create a new goal",
                "examples": ["create goal exercise daily", "add goal save money", "new goal learn Spanish"]
            },
            {
                "name": "create_task",
                "description": "Create a new task",
                "examples": ["add task call dentist", "create task buy groceries", "todo finish report"]
            },
            {
                "name": "show_schedule",
                "description": "Show upcoming calendar events",
                "examples": ["what's next", "schedule today", "what meetings do I have"]
            },
            {
                "name": "show_goals",
                "description": "Show goal progress",
                "examples": ["my goals", "goal progress", "how am I doing"]
            },
            {
                "name": "suggest_task",
                "description": "Suggest next task to work on",
                "examples": ["what should I do", "next task", "my tasks"]
            },
            {
                "name": "reschedule_help",
                "description": "Get help with rescheduling",
                "examples": ["reschedule meeting", "move appointment", "postpone call"]
            }
        ]
    }