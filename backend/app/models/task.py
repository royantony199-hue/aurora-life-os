from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Boolean, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from ..core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, enum.Enum):
    ACTION = "action"           # Simple actionable task
    MILESTONE = "milestone"     # Important checkpoint
    HABIT = "habit"            # Recurring activity
    RESEARCH = "research"      # Information gathering
    DECISION = "decision"      # Decision point
    REVIEW = "review"          # Check progress/quality


class Task(Base):
    """
    Enhanced Task model matching PRD requirements
    Supports goal breakdown, smart scheduling, and AI coaching
    """
    __tablename__ = "tasks"

    # Core fields from PRD
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)  # Tasks can exist without goals
    
    # Task details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    
    # Enhanced fields for better task management
    task_type = Column(Enum(TaskType), default=TaskType.ACTION, nullable=False)
    estimated_duration = Column(Integer, nullable=True)  # Minutes
    actual_duration = Column(Integer, nullable=True)     # Minutes spent
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)  # 0-100
    completion_notes = Column(Text, nullable=True)
    
    # Hierarchy and dependencies
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # For sub-tasks
    order_index = Column(Integer, default=0)  # Order within goal or parent task
    
    # Smart scheduling (PRD requirement)
    energy_level_required = Column(Integer, nullable=True)  # 1-10 scale
    preferred_time_of_day = Column(String(20), nullable=True)  # morning, afternoon, evening
    is_flexible_timing = Column(Boolean, default=True)
    scheduled_for = Column(DateTime, nullable=True)  # When task is scheduled to be done
    
    # AI coaching integration
    ai_generated = Column(Boolean, default=False)  # True if task was created by AI coaching
    ai_suggestions = Column(Text, nullable=True)  # JSON of AI-generated suggestions
    context_notes = Column(Text, nullable=True)  # Additional context for AI
    mood_when_created = Column(Integer, nullable=True)  # User's mood when task was created
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_goal_order', 'goal_id', 'order_index'),
        Index('idx_due_date', 'due_date'),
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', goal_id={self.goal_id})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return datetime.now() > self.due_date
        return False
    
    @property
    def days_until_due(self) -> int:
        """Days until due date (negative if overdue)"""
        if self.due_date:
            delta = self.due_date.date() - datetime.now().date()
            return delta.days
        return 999  # No due date
    
    def start_task(self):
        """Mark task as started"""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.IN_PROGRESS
            self.started_at = datetime.now()
    
    def complete_task(self, completion_notes: str = None, actual_duration: int = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress_percentage = 100.0
        if completion_notes:
            self.completion_notes = completion_notes
        if actual_duration:
            self.actual_duration = actual_duration
    
    def get_time_estimate_display(self) -> str:
        """Get human-readable time estimate"""
        if not self.estimated_duration:
            return "No estimate"
        
        hours = self.estimated_duration // 60
        minutes = self.estimated_duration % 60
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return f"{minutes}m"


class TaskDependency(Base):
    """
    Task dependencies - one task must be completed before another can start
    Supports complex project management workflows
    """
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)  # Task that depends
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)  # Task it depends on
    
    # Dependency type
    dependency_type = Column(String(20), default="blocks")  # blocks, enhances, related
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id])
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id])
    
    __table_args__ = (
        Index('idx_task_dependency', 'task_id', 'depends_on_task_id'),
    )