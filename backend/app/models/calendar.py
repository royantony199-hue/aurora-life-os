from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class EventType(str, enum.Enum):
    MEETING = "meeting"
    TASK = "task"
    GOAL_WORK = "goal_work"
    DEEP_WORK = "deep_work"
    ADMIN = "admin"
    BREAK = "break"
    PERSONAL = "personal"
    LEARNING = "learning"
    NETWORKING = "networking"
    PLANNING = "planning"


class EventPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    URGENT = "urgent"


class SchedulingType(str, enum.Enum):
    MANUAL = "manual"           # User created manually
    AI_SUGGESTED = "ai_suggested"  # AI suggested, not confirmed
    AI_SCHEDULED = "ai_scheduled"  # AI scheduled and confirmed
    AUTO_GENERATED = "auto_generated"  # Generated from goals


class EisenhowerQuadrant(str, enum.Enum):
    Q1_URGENT_IMPORTANT = "q1_urgent_important"      # Do First - Crisis, emergencies
    Q2_NOT_URGENT_IMPORTANT = "q2_not_urgent_important"  # Schedule - Important goals, planning
    Q3_URGENT_NOT_IMPORTANT = "q3_urgent_not_important"  # Delegate - Interruptions, some emails
    Q4_NOT_URGENT_NOT_IMPORTANT = "q4_not_urgent_not_important"  # Eliminate - Time wasters, distractions


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    event_type = Column(Enum(EventType), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    
    # Google Calendar integration
    google_event_id = Column(String, nullable=True, unique=True)  # Google Calendar event ID
    google_calendar_data = Column(JSON, nullable=True)  # Raw Google Calendar event data
    is_synced = Column(Boolean, default=False)  # Whether synced with Google Calendar
    sync_status = Column(String, default="pending")  # pending, synced, failed, deleted
    
    # Meeting links and join information
    meeting_url = Column(String, nullable=True)  # Primary meeting URL (Zoom, Meet, Teams, etc.)
    meeting_id = Column(String, nullable=True)  # Meeting ID (for Zoom, etc.)
    meeting_passcode = Column(String, nullable=True)  # Meeting passcode if required
    meeting_phone = Column(String, nullable=True)  # Phone dial-in number
    meeting_type = Column(String, nullable=True)  # zoom, google-meet, teams, webex, etc.
    
    # AI Scheduling Fields
    priority = Column(Enum(EventPriority), default=EventPriority.MEDIUM)
    scheduling_type = Column(Enum(SchedulingType), default=SchedulingType.MANUAL)
    
    # Eisenhower Matrix Integration
    eisenhower_quadrant = Column(Enum(EisenhowerQuadrant), nullable=True)  # AI-determined quadrant
    is_urgent = Column(Boolean, default=False)  # Must be done soon (deadline pressure)
    is_important = Column(Boolean, default=True)  # Contributes to goals/values
    urgency_reason = Column(String, nullable=True)  # Why this is urgent (deadline, dependency, etc.)
    importance_reason = Column(String, nullable=True)  # Why this is important (goal contribution, impact, etc.)
    energy_required = Column(Integer, nullable=True)  # 1-10 scale
    optimal_time_of_day = Column(String, nullable=True)  # morning, afternoon, evening
    ai_reasoning = Column(Text, nullable=True)  # Why AI scheduled this here
    flexibility = Column(Integer, default=0)  # Minutes this can be moved (0-120)
    
    # Goal Integration
    contributes_to_goal = Column(Boolean, default=False)  # Does this event help goals?
    goal_weight = Column(Integer, nullable=True)  # Importance for goal achievement (1-10)
    
    # Scheduling Metadata
    auto_scheduled = Column(Boolean, default=False)  # Was this auto-scheduled by AI?
    user_confirmed = Column(Boolean, default=True)   # Has user confirmed this time?
    reschedule_count = Column(Integer, default=0)    # How many times rescheduled
    last_rescheduled = Column(DateTime(timezone=True), nullable=True)
    
    # Time Optimization
    focus_level_required = Column(Integer, nullable=True)  # 1-10 how much focus needed
    break_before = Column(Integer, default=0)  # Minutes of break needed before
    break_after = Column(Integer, default=0)   # Minutes of break needed after
    can_be_interrupted = Column(Boolean, default=True)  # Can this be interrupted?
    
    # AI insights
    ai_insights = Column(JSON, nullable=True)  # AI-generated insights about the event
    mood_impact_prediction = Column(Integer, nullable=True)  # Predicted mood impact (-5 to +5)
    
    # Smart Rescheduling & Dependencies
    depends_on_event_ids = Column(JSON, nullable=True)  # List of event IDs this depends on
    blocks_event_ids = Column(JSON, nullable=True)  # List of event IDs that depend on this
    auto_reschedule_enabled = Column(Boolean, default=True)  # Allow automatic rescheduling
    reschedule_buffer_minutes = Column(Integer, default=15)  # Buffer time when auto-rescheduling
    dependency_type = Column(String, nullable=True)  # "sequential", "same_day", "before_deadline"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User")
    goal = relationship("Goal")