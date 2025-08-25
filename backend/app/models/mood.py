from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood_level = Column(Integer, nullable=False)  # 1-10 scale
    energy_level = Column(Integer, nullable=False)  # 1-10 scale
    mood_emoji = Column(String, nullable=True)  # Emoji representation
    stress_level = Column(Integer, nullable=True)  # 1-10 scale for stress
    notes = Column(Text, nullable=True)
    location = Column(String, nullable=True)  # Where they are
    triggers = Column(Text, nullable=True)  # What influenced their mood
    is_burnout_risk = Column(Boolean, default=False)
    intervention_suggested = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")