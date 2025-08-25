from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    CHAT = "chat"
    MOOD_CHECKIN = "mood_checkin"
    GOAL_UPDATE = "goal_update"
    COACHING = "coaching"
    QUICK_COMMAND = "quick_command"
    PROACTIVE = "proactive"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.CHAT)
    content = Column(Text, nullable=False)
    
    # Context and memory management
    context_data = Column(JSON, nullable=True)  # Related context (goals, mood, calendar events)
    response_time_ms = Column(Integer, nullable=True)  # Response time for analytics
    user_mood_at_time = Column(Integer, nullable=True)  # User's mood when message sent
    user_energy_at_time = Column(Integer, nullable=True)  # User's energy when message sent
    
    # AI coaching metadata
    coaching_intent = Column(String, nullable=True)  # goal_breakdown, motivation, problem_solving, etc.
    action_items_generated = Column(JSON, nullable=True)  # Any action items created from this conversation
    follow_up_needed = Column(Boolean, default=False)
    
    # Proactive messaging fields
    is_proactive = Column(Boolean, default=False)  # True if AI initiated this message
    trigger_type = Column(String, nullable=True)  # mood_gap, goal_deadline, energy_pattern, etc.
    trigger_context = Column(JSON, nullable=True)  # Additional trigger context data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")