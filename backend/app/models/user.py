from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    
    # PRD-specific fields for personalization
    personality_data = Column(JSON, nullable=True)  # Personality insights and preferences
    preferences = Column(JSON, nullable=True)  # User preferences for coaching style, notifications, etc.
    coaching_style = Column(String, default="balanced")  # supportive, direct, motivational, balanced
    timezone = Column(String, default="UTC")
    work_hours_start = Column(String, default="09:00")
    work_hours_end = Column(String, default="18:00")
    
    # Onboarding and context
    onboarding_completed = Column(Boolean, default=False)
    industry = Column(String, nullable=True)  # Solopreneur industry/field
    experience_level = Column(String, default="intermediate")  # beginner, intermediate, advanced
    primary_challenges = Column(Text, nullable=True)  # Main challenges they face
    
    # Calendar integrations
    google_calendar_connected = Column(Boolean, default=False)
    outlook_calendar_connected = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")