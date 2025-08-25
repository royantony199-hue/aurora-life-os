#!/usr/bin/env python3
"""
Proactive Message Log Model
Tracks sent proactive messages to prevent duplicates and enforce rate limiting
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base


class ProactiveMessageLog(Base):
    """Track proactive messages sent to users for duplicate prevention and rate limiting"""
    __tablename__ = "proactive_message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trigger_type = Column(String, nullable=False)  # mood_gap, goal_deadline, etc.
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)  # Link to actual message
    
    # Rate limiting fields
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cooldown_expires_at = Column(DateTime(timezone=True), nullable=False)  # When this trigger type can fire again
    
    # Read tracking
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    message = relationship("ChatMessage")
    
    # Unique constraint to prevent duplicate logs
    __table_args__ = (
        UniqueConstraint('user_id', 'trigger_type', 'sent_at', name='_user_trigger_time_uc'),
        Index('idx_user_trigger_cooldown', 'user_id', 'trigger_type', 'cooldown_expires_at'),
        Index('idx_user_sent_at', 'user_id', 'sent_at'),
    )


class UserProactivePreferences(Base):
    """Store user preferences for proactive messaging"""
    __tablename__ = "user_proactive_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Feature toggles
    enabled = Column(Boolean, default=True)
    mood_reminders = Column(Boolean, default=True)
    goal_reminders = Column(Boolean, default=True)
    energy_insights = Column(Boolean, default=True)
    calendar_insights = Column(Boolean, default=True)
    
    # Rate limiting
    max_messages_per_day = Column(Integer, default=2)
    check_interval_minutes = Column(Integer, default=30)
    
    # Quiet hours (stored as hour integers 0-23)
    quiet_hours_start = Column(Integer, default=22)  # 10 PM
    quiet_hours_end = Column(Integer, default=7)     # 7 AM
    timezone = Column(String, default="UTC")
    
    # Preferences
    preferred_trigger_times = Column(String, nullable=True)  # JSON array of preferred hours
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")