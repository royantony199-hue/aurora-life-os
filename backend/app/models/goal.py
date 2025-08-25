from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalCategory(str, enum.Enum):
    LEARNING = "learning"
    HEALTH = "health"
    PERSONAL = "personal"
    CAREER = "career"
    FINANCIAL = "financial"
    RELATIONSHIP = "relationship"
    OTHER = "other"


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(Enum(GoalCategory), nullable=False)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    progress = Column(Float, default=0.0)
    target_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan", order_by="Task.order_index")