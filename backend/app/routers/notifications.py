from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from app.core.database import get_db
from app.models import CalendarEvent, User, ChatMessage, MessageRole, MessageType
from app.services.openai_service import OpenAIService

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderRequest(BaseModel):
    user_id: int
    minutes_ahead: int = 30  # Default to 30 minutes

class NotificationResponse(BaseModel):
    message: str
    event_title: str
    start_time: datetime
    minutes_until: int
    notification_type: str  # "reminder" or "alarm"

# In-memory storage for active reminders (in production, use Redis or similar)
active_reminders = {}

@router.post("/schedule-reminders/{user_id}")
async def schedule_event_reminders(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Schedule reminders for all upcoming events for a user"""
    try:
        # Get upcoming events (next 24 hours)
        now = datetime.now()
        tomorrow = now + timedelta(hours=24)
        
        upcoming_events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= tomorrow,
            CalendarEvent.is_synced == True
        ).all()
        
        reminders_scheduled = 0
        
        for event in upcoming_events:
            # Schedule reminders at 30, 10, and 5 minutes before
            reminder_times = [30, 10, 5]
            
            for minutes in reminder_times:
                reminder_time = event.start_time - timedelta(minutes=minutes)
                
                # Only schedule if reminder time is in the future
                if reminder_time > now:
                    background_tasks.add_task(
                        schedule_reminder,
                        user_id,
                        event.id,
                        event.title,
                        event.start_time,
                        minutes,
                        reminder_time
                    )
                    reminders_scheduled += 1
        
        return {
            "message": f"Scheduled {reminders_scheduled} reminders for {len(upcoming_events)} events",
            "events_count": len(upcoming_events),
            "reminders_count": reminders_scheduled
        }
        
    except Exception as e:
        logger.error(f"Error scheduling reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule reminders: {str(e)}")

async def schedule_reminder(
    user_id: int,
    event_id: int,
    event_title: str,
    start_time: datetime,
    minutes_before: int,
    reminder_time: datetime
):
    """Schedule a single reminder"""
    try:
        # Calculate delay until reminder time
        now = datetime.now()
        delay_seconds = (reminder_time - now).total_seconds()
        
        if delay_seconds > 0:
            # Wait until reminder time
            await asyncio.sleep(delay_seconds)
            
            # Send reminder notification
            await send_reminder_notification(
                user_id, event_id, event_title, start_time, minutes_before
            )
            
    except Exception as e:
        logger.error(f"Error in reminder task: {str(e)}")

async def send_reminder_notification(
    user_id: int,
    event_id: int,
    event_title: str,
    start_time: datetime,
    minutes_before: int
):
    """Send a reminder notification to the chat"""
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Get event details for enhanced reminder
        event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        
        # Create reminder message
        if minutes_before >= 30:
            emoji = "⏰"
            urgency = "upcoming"
        elif minutes_before >= 10:
            emoji = "🔔"
            urgency = "soon"
        else:
            emoji = "🚨"
            urgency = "very soon"
        
        time_str = start_time.strftime("%I:%M %p")
        
        # Add meeting link info if available
        meeting_info = ""
        if event and event.meeting_url:
            meeting_icons = {
                'zoom': '🎥',
                'google-meet': '📹', 
                'teams': '👥',
                'webex': '💼',
                'gotomeeting': '📞'
            }
            icon = meeting_icons.get(event.meeting_type, '🔗')
            meeting_type = event.meeting_type.replace('-', ' ').title() if event.meeting_type else 'Meeting'
            meeting_info = f" • {icon} {meeting_type} ready to join"
        
        reminder_message = f"{emoji} Reminder: '{event_title}' starts {urgency} at {time_str} ({minutes_before} minutes){meeting_info}"
        
        # Save as system message in chat
        system_message = ChatMessage(
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.CHAT,
            content=reminder_message,
            context_data={
                "notification_type": "event_reminder",
                "event_id": event_id,
                "minutes_before": minutes_before,
                "event_title": event_title,
                "start_time": start_time.isoformat(),
                "meeting_url": event.meeting_url if event else None,
                "meeting_type": event.meeting_type if event else None,
                "meeting_id": event.meeting_id if event else None
            }
        )
        
        db.add(system_message)
        db.commit()
        
        logger.info(f"Sent reminder for event '{event_title}' to user {user_id}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error sending reminder notification: {str(e)}")

@router.get("/upcoming-reminders/{user_id}")
async def get_upcoming_reminders(
    user_id: int,
    hours_ahead: int = 24,
    db: Session = Depends(get_db)
):
    """Get upcoming events that will have reminders"""
    try:
        now = datetime.now()
        future_time = now + timedelta(hours=hours_ahead)
        
        upcoming_events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= future_time,
            CalendarEvent.is_synced == True
        ).order_by(CalendarEvent.start_time).all()
        
        reminders = []
        for event in upcoming_events:
            # Calculate when reminders will be sent
            reminder_times = []
            for minutes in [30, 10, 5]:
                reminder_time = event.start_time - timedelta(minutes=minutes)
                if reminder_time > now:
                    reminder_times.append({
                        "minutes_before": minutes,
                        "reminder_time": reminder_time,
                        "status": "scheduled"
                    })
            
            if reminder_times:  # Only include events with future reminders
                reminders.append({
                    "event_id": event.id,
                    "title": event.title,
                    "start_time": event.start_time,
                    "minutes_until_start": int((event.start_time - now).total_seconds() / 60),
                    "reminders": reminder_times
                })
        
        return {
            "upcoming_reminders": reminders,
            "total_events": len(reminders)
        }
        
    except Exception as e:
        logger.error(f"Error getting upcoming reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-reminder")
async def test_reminder_system(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Test the reminder system with a fake event in 2 minutes"""
    try:
        # Create a test event 2 minutes from now
        test_start_time = datetime.now() + timedelta(minutes=2)
        
        test_event = CalendarEvent(
            user_id=user_id,
            title="Test Reminder Event",
            description="This is a test event for reminder system",
            event_type="meeting",
            start_time=test_start_time,
            end_time=test_start_time + timedelta(minutes=30),
            is_synced=True,
            sync_status="synced"
        )
        
        db.add(test_event)
        db.commit()
        db.refresh(test_event)
        
        # Schedule a test reminder 1 minute from now (1 minute before the test event)
        reminder_time = datetime.now() + timedelta(minutes=1)
        
        # Use asyncio to schedule the reminder
        asyncio.create_task(
            schedule_reminder(
                user_id=user_id,
                event_id=test_event.id,
                event_title=test_event.title,
                start_time=test_start_time,
                minutes_before=1,
                reminder_time=reminder_time
            )
        )
        
        return {
            "message": "Test reminder scheduled",
            "test_event_id": test_event.id,
            "reminder_in_seconds": 60,
            "event_starts_in_seconds": 120
        }
        
    except Exception as e:
        logger.error(f"Error creating test reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cancel-reminders/{user_id}")
async def cancel_all_reminders(user_id: int):
    """Cancel all active reminders for a user"""
    try:
        # In production, this would cancel scheduled tasks
        # For now, just clear from our tracking
        if user_id in active_reminders:
            del active_reminders[user_id]
        
        return {"message": f"Cancelled all reminders for user {user_id}"}
        
    except Exception as e:
        logger.error(f"Error cancelling reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))